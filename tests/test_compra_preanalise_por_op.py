"""Regressões do relatório consultivo de Compra MRP por OP."""
import unittest

import pandas as pd

from mrp_compra_preanalise import (
    OP_NAO_INFORMADA,
    construir_relatorio_compra_por_op,
)


class CompraPreAnalisePorOpTests(unittest.TestCase):
    def setUp(self):
        self.entrada = pd.DataFrame([
            {"produto": "00000158", "qnt": 9, "data": "13/11/2026",
             "psy": "", "cc": "600307", "op": "26007206007",
             "obs": "MRP", "prioridade": "2", "prj": ""},
            {"produto": "00000158", "qnt": 3, "data": "20/11/2026",
             "psy": "", "cc": "600307", "op": "26007206007",
             "obs": "MRP", "prioridade": "1", "prj": ""},
            {"produto": "00000158", "qnt": 5, "data": "13/11/2026",
             "psy": "", "cc": "600307", "op": "26031401001",
             "obs": "MRP", "prioridade": "2", "prj": ""},
            {"produto": "00000295", "qnt": 20, "data": "13/11/2026",
             "psy": "", "cc": "600307", "op": "26031401001",
             "obs": "MRP", "prioridade": "1", "prj": ""},
            {"produto": "00000520", "qnt": 2, "data": "20/11/2026",
             "psy": "", "cc": "600307", "op": "",
             "obs": "MRP TC/TP", "prioridade": "2", "prj": ""},
        ])
        self.desc = {"00000158": "CABO A", "00000295": "CONECTOR",
                     "00000520": "PARAFUSO"}

    def test_detalhe_preserva_linhas_op_codigo_e_datas(self):
        resultado = construir_relatorio_compra_por_op(self.entrada, self.desc)
        detalhamento = resultado["DETALHE OP"]
        self.assertEqual(len(detalhamento), 5)
        linhas = detalhamento[
            (detalhamento["OP"] == "26007206007")
            & (detalhamento["Código"] == "00000158")
        ]
        self.assertEqual(linhas["Quantidade"].tolist(), [9, 3])
        self.assertEqual(
            linhas["Data de necessidade"].tolist(),
            ["13/11/2026", "20/11/2026"],
        )
        self.assertEqual(linhas["Descrição"].tolist(), ["CABO A", "CABO A"])

    def test_consolidacao_nao_mistura_mesmo_material_de_ops_diferentes(self):
        resultado = construir_relatorio_compra_por_op(self.entrada, self.desc)
        material = resultado["MATERIAIS OP"]
        item_a = material[
            (material["OP"] == "26007206007")
            & (material["Código"] == "00000158")
        ].iloc[0]
        item_b = material[
            (material["OP"] == "26031401001")
            & (material["Código"] == "00000158")
        ].iloc[0]
        self.assertEqual(item_a["Quantidade"], 12)
        self.assertEqual(item_b["Quantidade"], 5)
        self.assertEqual(item_a["Prioridade"], "2")
        self.assertEqual(item_a["Primeira necessidade"], "13/11/2026")

    def test_op_ausente_fica_em_grupo_separado(self):
        r = construir_relatorio_compra_por_op(self.entrada, self.desc)
        self.assertIn(OP_NAO_INFORMADA, r["RESUMO OP"]["OP"].tolist())
        self.assertTrue(
            r["DETALHE OP"]["OP"].eq(OP_NAO_INFORMADA).any()
        )

    def test_filtrar_op_e_revisar_sem_alterar_origem(self):
        anterior = self.entrada.copy(deep=True)
        resultado = construir_relatorio_compra_por_op(
            self.entrada, self.desc, ["26007206007"]
        )
        self.assertEqual(len(resultado["RESUMO OP"]), 1)
        self.assertEqual(len(resultado["DETALHE OP"]), 2)
        self.assertEqual(resultado["MATERIAIS OP"]["Quantidade"].sum(), 12)
        pd.testing.assert_frame_equal(self.entrada, anterior)

    def test_data_ultima_solicitacao_vem_do_tratado_por_op_e_produto(self):
        # A necessidade da compra é novembro; última solicitação é outubro.
        # Uma solicitação de OUTRA OP para o mesmo material não contamina.
        tratado = pd.DataFrame([
            {"Projeto": "26007206007", "Código": 158,
             "Data Solicitação": pd.Timestamp("2026-10-10")},
            {"Projeto": "26007206007", "Código": 158.0,
             "Data Solicitação": pd.Timestamp("2026-10-27")},
            {"Projeto": "26031401001", "Código": 158,
             "Data Solicitação": pd.Timestamp("2026-11-12")},
            {"Projeto": "26031401001", "Código": 295,
             "Data Solicitação": pd.Timestamp("2026-11-01")},
        ])
        resultado = construir_relatorio_compra_por_op(
            self.entrada, self.desc, solicitacoes=tratado
        )
        d = resultado["DETALHE OP"]
        a = d[(d["OP"] == "26007206007") & (d["Código"] == "00000158")]
        b = d[(d["OP"] == "26031401001") & (d["Código"] == "00000158")]
        self.assertEqual(a["Última solicitação"].tolist(),
                         ["27/10/2026", "27/10/2026"])
        self.assertEqual(b["Última solicitação"].tolist(), ["12/11/2026"])
        self.assertEqual(a["Data de necessidade"].tolist(),
                         ["13/11/2026", "20/11/2026"])
        resumo = resultado["MATERIAIS OP"]
        self.assertEqual(
            resumo.loc[
                (resumo["OP"] == "26007206007")
                & (resumo["Código"] == "00000158"),
                "Última solicitação",
            ].iloc[0], "27/10/2026"
        )
        self.assertEqual(
            resumo.loc[
                (resumo["OP"] == "26031401001")
                & (resumo["Código"] == "00000158"),
                "Última solicitação",
            ].iloc[0], "12/11/2026"
        )
        self.assertTrue(
            d.loc[d["OP"] == OP_NAO_INFORMADA, "Última solicitação"]
            .eq("NI").all()
        )
        self.assertEqual(
            resultado["MATERIAIS OP"]["Quantidade"].sum(), 39
        )

    def test_data_ultima_solicitacao_vem_snapshot_consulta(self):
        historico = pd.DataFrame([
            {"Projeto": "26007206007", "Produto": 158,
             "Última Solicitação": "30/10/2026"},
            {"Projeto": "26031401001", "Produto": "00000158",
             "Última Solicitação": "02/11/2026"},
        ])
        antes = historico.copy(deep=True)
        resultado = construir_relatorio_compra_por_op(
            self.entrada, self.desc, ["26007206007"], historico
        )
        self.assertEqual(
            resultado["MATERIAIS OP"]["Última solicitação"].tolist(),
            ["30/10/2026"]
        )
        pd.testing.assert_frame_equal(historico, antes)

    def test_data_ausente_nao_substitui_pela_data_necessidade(self):
        resultado = construir_relatorio_compra_por_op(
            self.entrada, self.desc,
            solicitacoes=pd.DataFrame([
                {"Projeto": "26007206007", "Código": 158,
                 "Data Solicitação": "NI"},
            ])
        )
        self.assertTrue(resultado["DETALHE OP"]["Última solicitação"].eq("NI").all())
        self.assertIn("Última solicitação", resultado["MATERIAIS OP"].columns)

    def test_data_iso_normalizada_pela_chave_op_material(self):
        tratado = pd.DataFrame([
            {"Projeto": "26007206007", "Código": "00000158",
             "Última solicitação": "2026-11-15T00:00:00Z"},
            {"Projeto": "26007206007", "Código": "00000295",
             "Última solicitação": "2026-11-16"},
        ])
        resultado = construir_relatorio_compra_por_op(
            self.entrada, self.desc, solicitacoes=tratado
        )
        self.assertEqual(
            resultado["MATERIAIS OP"].loc[
                (resultado["MATERIAIS OP"]["OP"] == "26007206007")
                & (resultado["MATERIAIS OP"]["Código"] == "00000158"),
                "Última solicitação",
            ].iloc[0], "15/11/2026"
        )

    def test_pre_analise_mostra_valor_zero_e_consolida_preco_por_op(self):
        entrada=self.entrada.copy()
        entrada["vunit"]=[0,19.5,32.8,0,0]
        r=construir_relatorio_compra_por_op(entrada,self.desc)
        detalhe=r["DETALHE OP"]
        self.assertIn("Valor mínimo encontrado",detalhe.columns)
        self.assertEqual(detalhe.loc[
            (detalhe["OP"]=="26007206007")
            & (detalhe["Código"]=="00000158"),
            "Valor mínimo encontrado",
        ].tolist(),[0.0,19.5])
        m=r["MATERIAIS OP"]
        self.assertEqual(m.loc[
            (m["OP"]=="26007206007")
            & (m["Código"]=="00000158"),
            "Valor mínimo encontrado",
        ].iloc[0],19.5)
        self.assertEqual(m.loc[
            m["Código"]=="00000295",
            "Valor mínimo encontrado",
        ].iloc[0],0)
        self.assertEqual(m["Quantidade"].sum(),39)

    def test_pre_analise_arquivo_legado_sem_vunit_exibe_zero(self):
        r=construir_relatorio_compra_por_op(self.entrada,self.desc)
        self.assertTrue(r["DETALHE OP"]["Valor mínimo encontrado"].eq(0).all())
        self.assertTrue(r["MATERIAIS OP"]["Valor mínimo encontrado"].eq(0).all())

    def test_campos_analise_nao_sao_carga_protheus(self):
        r = construir_relatorio_compra_por_op(self.entrada, self.desc)
        self.assertIn("INSTRUÇÕES", r)
        self.assertIn("Parecer do analista", r["DETALHE OP"].columns)
        self.assertTrue(
            r["DETALHE OP"]["Parecer do analista"].eq("").all()
        )
        self.assertIn(
            "NÃO É CARGA DO PROTHEUS",
            r["INSTRUÇÕES"].iloc[0]["Orientação"],
        )

    def test_quantidade_invalida_bloqueada_sem_gerar_carga(self):
        inconsistente = self.entrada.copy()
        inconsistente.loc[0, "qnt"] = -1
        with self.assertRaisesRegex(ValueError, "quantidade"):
            construir_relatorio_compra_por_op(inconsistente, self.desc)

    def test_texto_hostil_na_observacao_nao_vira_formula(self):
        dados = self.entrada.head(1).copy()
        dados.loc[0, "obs"] = '=HYPERLINK("https://example.com")'
        r = construir_relatorio_compra_por_op(dados, self.desc)
        self.assertTrue(
            r["DETALHE OP"].iloc[0]["Observação MRP"].startswith("'=")
        )


class ParecerAutomaticoTests(unittest.TestCase):
    ANTIGO = "26007206007"
    NOVO = "26036201001"
    OUTRO = "26031401001"
    COD = "00000158"

    def compra(self, op=None, quantidade=5):
        return {"produto": self.COD, "qnt": quantidade, "data": "18/12/2026",
                "psy": "", "cc": "600307", "op": op or self.ANTIGO,
                "obs": "MRP", "prioridade": "2"}

    def linha(self, op, data, cm, semana, necessidade, acao):
        return {"Projeto": op, "Produto": 158, "Última Solicitação": data,
                "Data CM": cm, "Semana de Necessidade": semana,
                "Necessidade": necessidade, "Ação": acao}

    def analisar(self, compras, alocacoes, referencia="2026-11-25", **kwargs):
        return construir_relatorio_compra_por_op(
            pd.DataFrame(compras), solicitacoes=pd.DataFrame(alocacoes),
            referencia=referencia, **kwargs
        )

    def test_hoje_e_dia_util_anterior(self):
        for data in ["25/11/2026", "24/11/2026"]:
            with self.subTest(data=data):
                r = self.analisar([self.compra()], [
                    self.linha(self.ANTIGO, data, "18/12/2026", 202650, 5,
                               "CRIAR S.C. 5 para semana 202650")
                ])
                for aba in ["MATERIAIS OP", "DETALHE OP"]:
                    self.assertEqual(r[aba].iloc[0]["Parecer do analista"], "NOVA DEMANDA")
                    self.assertEqual(r[aba].iloc[0]["Observações da análise"], "")

    def test_segunda_considera_sexta(self):
        r = self.analisar([self.compra()], [
            self.linha(self.ANTIGO, "27/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650")
        ], referencia="2026-11-30")
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "NOVA DEMANDA")

    def test_segunda_apos_feriado_considera_quinta(self):
        r = self.analisar([self.compra()], [
            self.linha(self.ANTIGO, "19/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650")
        ], referencia="2026-11-23")
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "NOVA DEMANDA")

    def test_feriado_adicional(self):
        r = self.analisar([self.compra()], [
            self.linha(self.ANTIGO, "24/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650")
        ], referencia="2026-11-26", feriados_adicionais=["2026-11-25"])
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "NOVA DEMANDA")

    def test_redistribuicao_projeto_recente_atendido_fora_da_compra(self):
        aloc = [
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
            self.linha(self.NOVO, "25/11/2026", "27/11/2026", 202647, 5,
                       "Estoque 3; P.C. 2 (sem. 202647)"),
        ]
        r = self.analisar([self.compra()], aloc, ops=[self.ANTIGO])
        for aba in ["MATERIAIS OP", "DETALHE OP"]:
            linha = r[aba].iloc[0]
            self.assertEqual(linha["Parecer do analista"], "DEMANDA")
            self.assertIn(self.NOVO, linha["Observações da análise"])
            self.assertIn("5 UN.", linha["Observações da análise"])
            self.assertIn("INDÍCIO", linha["Observações da análise"])
            self.assertEqual(linha["Quantidade"], 5)

    def test_recente_sem_recurso_nao_gera_justificativa(self):
        r = self.analisar([self.compra()], [
            self.linha(self.NOVO, "25/11/2026", "27/11/2026", 202647, 5,
                       "CRIAR S.C. 5 para semana 202647"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Observações da análise"], "")

    def test_mesma_semana_data_cm_mais_proxima(self):
        r = self.analisar([self.compra()], [
            self.linha(self.NOVO, "25/11/2026", "16/12/2026", 202650, 5, "Estoque 5"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        self.assertIn(self.NOVO, r["MATERIAIS OP"].iloc[0]["Observações da análise"])

    def test_empate_de_prioridade_nao_inventa_causalidade(self):
        r = self.analisar([self.compra()], [
            self.linha("26000000001", "25/11/2026", "18/12/2026", 202650, 5, "Estoque 5"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Observações da análise"], "")

    def test_credito_parcial_nao_duplica_e_respeita_filtro(self):
        aloc = [
            self.linha(self.NOVO, "25/11/2026", "27/11/2026", 202647, 3, "Estoque 3"),
            self.linha(self.OUTRO, "10/11/2026", "04/12/2026", 202648, 2,
                       "CRIAR S.C. 2 para semana 202648"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ]
        r = self.analisar([self.compra(), self.compra(self.OUTRO, 2)], aloc,
                          ops=[self.ANTIGO])
        obs = r["MATERIAIS OP"].iloc[0]["Observações da análise"]
        self.assertIn("1 UN.", obs)
        self.assertIn("PARCIAL", obs)

    def test_admin_usa_acao_sem_contaminar_ultima_solicitacao(self):
        aloc = pd.DataFrame([
            self.linha(self.NOVO, "NI", "27/11/2026", 202647, 5, "Estoque 5"),
            self.linha(self.ANTIGO, "NI", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        tratado = pd.DataFrame([
            {"Projeto": self.NOVO, "Código": 158, "Data Solicitação": "25/11/2026"},
            {"Projeto": self.ANTIGO, "Código": 158, "Data Solicitação": "10/11/2026"},
        ])
        r = construir_relatorio_compra_por_op(
            pd.DataFrame([self.compra()]), solicitacoes=tratado,
            alocacoes=aloc, referencia="2026-11-25",
        )
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Última solicitação"], "10/11/2026")
        self.assertIn(self.NOVO, r["MATERIAIS OP"].iloc[0]["Observações da análise"])

    def test_data_ausente_e_futura_ficam_manuais(self):
        for data in ["NI", "26/11/2026"]:
            with self.subTest(data=data):
                r = self.analisar([self.compra()], [
                    self.linha(self.ANTIGO, data, "18/12/2026", 202650, 5,
                               "CRIAR S.C. 5 para semana 202650"),
                ])
                self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "")

    def test_fotografia_inconsistente_nao_justifica(self):
        r = self.analisar([self.compra()], [
            self.linha(self.NOVO, "25/11/2026", "27/11/2026", 202647, 5, "Estoque 2"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "DEMANDA")
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Observações da análise"], "")


if __name__ == "__main__":
    unittest.main()
