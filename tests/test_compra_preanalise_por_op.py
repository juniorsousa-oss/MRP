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
            r["DETALHE OP"]["Parecer do analista"].isin(["OK", "VERIFICAR"]).all()
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
            self.assertIn("SOLICITAÇÃO: 25/11/2026", linha["Observações da análise"])
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
                self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "VERIFICAR")

    def test_fotografia_inconsistente_nao_justifica(self):
        r = self.analisar([self.compra()], [
            self.linha(self.NOVO, "25/11/2026", "27/11/2026", 202647, 5, "Estoque 2"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "VERIFICAR")
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Observações da análise"], "")

    def test_exportacao_bloqueia_parecer_ausente_com_data_valida(self):
        from mrp_compra_preanalise import validar_pareceres_exportacao
        r = self.analisar([self.compra()], [
            self.linha(self.ANTIGO, "24/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        validar_pareceres_exportacao(r, referencia="2026-11-25")
        r["MATERIAIS OP"].loc[:, "Parecer do analista"] = ""
        with self.assertRaisesRegex(ValueError, "parecer automático ausente"):
            validar_pareceres_exportacao(r, referencia="2026-11-25")

    def test_exportacao_permite_revisao_manual_sem_data(self):
        from mrp_compra_preanalise import validar_pareceres_exportacao
        r = self.analisar([self.compra()], [
            self.linha(self.ANTIGO, "NI", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        validar_pareceres_exportacao(r, referencia="2026-11-25")


    def test_prioridade_1_recebe_ok_sem_observacao(self):
        from mrp_compra_preanalise import validar_pareceres_exportacao
        compra = self.compra()
        compra["prioridade"] = "1"
        r = self.analisar([compra], [
            self.linha(self.ANTIGO, "25/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650")
        ])
        for aba in ["MATERIAIS OP", "DETALHE OP"]:
            self.assertEqual(r[aba].iloc[0]["Parecer do analista"], "OK")
            self.assertEqual(r[aba].iloc[0]["Observações da análise"], "")
        validar_pareceres_exportacao(r, referencia="2026-11-25")

    def test_prioridade_mista_preserva_emergencial_no_consolidado(self):
        normal = self.compra(quantidade=2)
        normal["prioridade"] = "1"
        r = self.analisar([normal, self.compra(quantidade=3)], [
            self.linha(self.ANTIGO, "25/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650")
        ])
        d = r["DETALHE OP"].set_index("Prioridade")
        self.assertEqual(d.loc["1", "Parecer do analista"], "OK")
        self.assertEqual(d.loc["2", "Parecer do analista"], "NOVA DEMANDA")
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "NOVA DEMANDA")

    def test_caso_703747_cm_ni_na_mesma_semana(self):
        codigo = "00703747"
        recente = "26007206007"
        vitima = "26032202002"
        normal = "26029101001"
        aloc = [
            self.linha(recente, "24/11/2026", "17/11/2026", 202647, 9, "P.C. 9 (sem. 202649)"),
            self.linha("26031201001", "10/11/2026", "19/11/2026", 202647, 13, "P.C. 13 (sem. 202649)"),
            self.linha(vitima, "10/11/2026", "NI", 202647, 8, "CRIAR S.C. 8 para semana 202647"),
            self.linha(normal, "07/10/2026", "NI", 202650, 1, "CRIAR S.C. 1 para semana 202650"),
        ]
        for linha in aloc:
            linha["Produto"] = 703747
        a,b = self.compra(vitima,8), self.compra(normal,1)
        a["produto"] = b["produto"] = codigo
        b["prioridade"] = "1"
        r = self.analisar([a,b], aloc)["MATERIAIS OP"].set_index("OP")
        self.assertIn(recente, r.loc[vitima,"Observações da análise"])
        self.assertIn("8 UN.", r.loc[vitima,"Observações da análise"])
        self.assertIn("SOLICITAÇÃO: 24/11/2026", r.loc[vitima,"Observações da análise"])
        self.assertEqual(r.loc[normal,"Parecer do analista"], "OK")
        self.assertEqual(r.loc[normal,"Observações da análise"], "")

    def test_saldo_zerado_apos_excedente_justifica_as_duas_compras_auditadas(self):
        import pandas as pd
        from mrp_compra_preanalise import exportar_preanalise_formatada
        from openpyxl import load_workbook
        from io import BytesIO

        casos = [
            ("06080025", "26007206007", "03/11/2026", 27, 5),
            ("00010497", "26009201001", "16/10/2026", 30, 15),
        ]
        antigo, novo, macro_ant, macro_novo, compras = [], [], [], [], []
        for codigo, op, data, saldo, necessidade in casos:
            velho = self.linha(op, data, "26/11/2026", 202648, necessidade, f"Estoque {necessidade}")
            velho["Produto"] = int(codigo)
            antigo.append(velho)
            novo.append({**velho, "Ação": f"CRIAR S.C. {necessidade} para semana 202648"})
            macro_linha = {"Código": int(codigo), "Demanda": necessidade, "P.C.": 0, "S.C.": 0, "Produzindo": 0}
            macro_ant.append({**macro_linha, "Saldo em Estoque": saldo})
            macro_novo.append({**macro_linha, "Saldo em Estoque": 0})
            compras.append({**self.compra(op, necessidade), "produto": codigo})
        macro_atual = pd.DataFrame(macro_novo)
        hist = {"macro_anterior": pd.DataFrame(macro_ant), "alocacoes_anterior": pd.DataFrame(antigo),
                "macro_referencia": macro_atual, "alocacoes_referencia": pd.DataFrame(novo),
                "espelho_anterior": {"id": 127, "created_at": "2026-11-25T10:22:00Z"},
                "espelho_referencia": {"id": 132, "created_at": "2026-11-26T10:52:00Z"}}
        sem_perda = {**hist, "macro_anterior": macro_atual, "alocacoes_anterior": pd.DataFrame(novo),
                     "espelho_anterior": {"id": 131, "created_at": "2026-11-25T18:11:00Z"}}
        kwargs = {"referencia": "2026-11-26", "macro_atual": macro_atual}
        sem_primeiro = self.analisar(compras, novo, historico=sem_perda, **kwargs)
        self.assertEqual(sem_primeiro["MATERIAIS OP"]["Parecer do analista"].tolist(),
                         ["VERIFICAR", "VERIFICAR"])
        self.assertTrue(sem_primeiro["MATERIAIS OP"]["Observações da análise"].eq("").all())
        analise = self.analisar(compras, novo, historico={"comparativos": [hist, sem_perda]}, **kwargs)
        for aba in ("MATERIAIS OP", "DETALHE OP"):
            linhas = analise[aba].set_index("Código")
            for codigo, _, _, saldo, necessidade in casos:
                self.assertEqual(linhas.loc[codigo, "Parecer do analista"], "DEMANDA")
                obs = linhas.loc[codigo, "Observações da análise"]
                self.assertIn(f"REDUÇÃO DE ESTOQUE DE {saldo} UN.", obs)
                self.assertIn(f"NECESSIDADE ADICIONAL DE {necessidade} UN.", obs)
                self.assertIn("#127 DE 25/11/2026 07:22 → #132 DE 26/11/2026 07:52", obs)
                self.assertIn("CONFERIR AJUSTE NO ERP", obs)
        ws = load_workbook(BytesIO(exportar_preanalise_formatada(analise)))["MATERIAIS OP"]
        self.assertEqual(sum(isinstance(c.value, str) and "#127 DE 25/11/2026" in c.value
                             for row in ws for c in row), 2)

    def test_saldo_ainda_cobre_demanda_sem_gerar_nova_falta(self):
        from mrp_compra_preanalise import _observacoes_variacao_historica
        antigo = pd.DataFrame([self.linha(self.ANTIGO, "10/11/2026", "25/11/2026", 202648, 5, "Estoque 5")])
        def macro(saldo):
            return pd.DataFrame([{"Código": 158, "Saldo em Estoque": saldo, "Demanda": 5,
                                  "P.C.": 0, "S.C.": 0, "Produzindo": 0}])
        hist = {"macro_anterior": macro(27), "alocacoes_anterior": antigo,
                "macro_referencia": macro(10), "alocacoes_referencia": antigo}
        self.assertEqual(_observacoes_variacao_historica(antigo, macro(10), hist), {})

    def test_caso_6050235_perda_liquida_estoque_com_historico(self):
        codigo = "06050235"
        alvo = "26022703006"
        op1 = "26032201001"
        op2 = "26030701001"
        demais = "26025101001"
        old = [
            self.linha(op1, "17/11/2026", "26/11/2026", 202647, 5, "Estoque 2; P.C. 3 (sem. 202649)"),
            self.linha(op2, "13/11/2026", "01/12/2026", 202647, 2, "P.C. 2 (sem. 202649)"),
            self.linha(demais, "14/10/2026", "10/12/2026", 202647, 10, "P.C. 10 (sem. 202649)"),
            self.linha(alvo, "13/11/2026", "04/12/2026", 202648, 2, "P.C. 2 (sem. 202649)"),
        ]
        new = [
            self.linha(op1, "17/11/2026", "26/11/2026", 202647, 5, "P.C. 5 (sem. 202649)"),
            self.linha(op2, "13/11/2026", "01/12/2026", 202647, 1, "P.C. 1 (sem. 202649)"),
            self.linha(demais, "14/10/2026", "10/12/2026", 202647, 10, "P.C. 10 (sem. 202649)"),
            self.linha(alvo, "13/11/2026", "04/12/2026", 202648, 2, "P.C. 1 (sem. 202649); CRIAR S.C. 1 para semana 202648"),
        ]
        for linha in old + new:
            linha["Produto"] = 6050235
        def macro(estoque, demanda):
            return pd.DataFrame([{"Código": 6050235, "Saldo em Estoque": estoque,
                                  "Demanda": demanda, "P.C.": 17, "S.C.": 0, "Produzindo": 0}])
        hist = {"macro_anterior": macro(2,19), "alocacoes_anterior": pd.DataFrame(old),
                "macro_referencia": macro(0,18), "alocacoes_referencia": pd.DataFrame(new)}
        compra = self.compra(alvo,1)
        compra["produto"] = codigo
        r = self.analisar([compra], new, macro_atual=macro(0,18), historico=hist)
        for aba in ["MATERIAIS OP", "DETALHE OP"]:
            obs = r[aba].iloc[0]["Observações da análise"]
            self.assertIn("POSSÍVEL ERRO DE ESTOQUE", obs)
            self.assertIn("ESTOQUE DE 2 UN.", obs)
            self.assertIn("DEMANDA DE 1 UN.", obs)
            self.assertIn("NECESSIDADE ADICIONAL DE 1 UN.", obs)
        # Uma nova fotografia idêntica no mesmo dia não deve apagar a causa diária.
        repetido = {**hist, "macro_anterior": macro(0,18), "alocacoes_anterior": pd.DataFrame(new)}
        r = self.analisar([compra], new, macro_atual=macro(0,18),
                          historico={"comparativos": [hist, repetido]})
        self.assertIn("POSSÍVEL ERRO DE ESTOQUE", r["MATERIAIS OP"].iloc[0]["Observações da análise"])
        # Uma baixa normal (estoque e demanda reduzidos igualmente) não é erro.
        normal = {**hist, "macro_anterior": macro(1,19)}
        r = self.analisar([compra], new, macro_atual=macro(0,18), historico=normal)
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Parecer do analista"], "VERIFICAR")
        # Não usar uma fotografia de referência diferente da atual.
        r = self.analisar([compra], new, macro_atual=macro(0,19), historico=hist)
        self.assertEqual(r["MATERIAIS OP"].iloc[0]["Observações da análise"], "")


    def _variacao(self, antigo, atual, acao_antiga, acao_atual, qtd, codigo="00000158", op=None, ausente=False):
        op = op or self.ANTIGO
        base = ("Saldo em Estoque", "Demanda", "P.C.", "S.C.", "Produzindo")
        def macro(v, c):
            return {"Código": c, **dict(zip(base, v))}
        def alocacao(demanda, acao):
            return {**self.linha(op,"24/11/2026","11/12/2026",202647,demanda,acao), "Produto": int(codigo)}
        nova = [alocacao(atual[1], acao_atual)]
        ant = [alocacao(antigo[1], acao_antiga)]
        mac = pd.DataFrame([macro(atual,int(codigo))])
        mac_ant = pd.DataFrame([macro(antigo,int(codigo))])
        if ausente:
            ant[0]["Necessidade"] = 0
            ant[0]["Ação"] = "RESÍDUO 4"
            ant[0]["Projeto"] = self.OUTRO
            mac_ant["Código"] = 9999
        hist = {"macro_anterior": mac_ant, "alocacoes_anterior": pd.DataFrame(ant),
                "macro_referencia": mac, "alocacoes_referencia": pd.DataFrame(nova),
                "espelho_anterior": {"id": 127, "created_at": "2026-11-25T10:22:00Z"},
                "espelho_referencia": {"id": 132, "created_at": "2026-11-26T10:52:00Z"}}
        compra = {**self.compra(op,qtd),"produto":codigo}
        return self.analisar([compra],nova,referencia="2026-11-26",macro_atual=mac,historico=hist)["MATERIAIS OP"].iloc[0]

    def test_00705912_demanda_nova_ou_aumentada_justifica_as_duas_unidades(self):
        for ausente in (True,False):
            with self.subTest(ausente=ausente):
                row = self._variacao((0,3,0,3,0),(0,5,0,3,0),
                                     "S.C. 3 (sem. 202647)","S.C. 3 (sem. 202647); CRIAR S.C. 2 para semana 202647",
                                     2,"00705912","26033001001",ausente)
                self.assertEqual(row["Parecer do analista"],"DEMANDA")
                inicio = 0 if ausente else 3
                self.assertIn(f"AUMENTO DE DEMANDA DE {inicio} PARA 5",row["Observações da análise"])
                self.assertIn("NECESSIDADE ADICIONAL DE 2 UN.",row["Observações da análise"])
                self.assertIn(f"OP 26033001001 (+{5-inicio} UN.)",row["Observações da análise"])
                self.assertNotIn("S.C.", row["Observações da análise"])

    def test_identifica_as_ops_que_aumentaram_e_nao_a_op_afetada(self):
        def linha(op, qtd, acao):
            return self.linha(op, "24/11/2026", "11/12/2026", 202647, qtd, acao)

        antes = [linha(self.ANTIGO, 2, "Estoque 2")]
        agora = [linha(self.ANTIGO, 2, "CRIAR S.C. 2 para semana 202647"),
                 linha(self.NOVO, 1, "Estoque 1"),
                 linha(self.OUTRO, 1, "Estoque 1")]

        def macro(demanda):
            return pd.DataFrame([{"Código": 158, "Saldo em Estoque": 2, "Demanda": demanda,
                                  "P.C.": 0, "S.C.": 0, "Produzindo": 0}])

        referencia = macro(4)
        hist = {"macro_anterior": macro(2), "alocacoes_anterior": pd.DataFrame(antes),
                "macro_referencia": referencia, "alocacoes_referencia": pd.DataFrame(agora)}
        r = self.analisar([self.compra(self.ANTIGO, 2)], agora, referencia="2026-11-26",
                          macro_atual=referencia, historico=hist)["MATERIAIS OP"].iloc[0]
        self.assertEqual(r["OP"], self.ANTIGO)
        obs = r["Observações da análise"]
        self.assertIn(f"OP {self.NOVO} (+1 UN.)", obs)
        self.assertIn(f"OP {self.OUTRO} (+1 UN.)", obs)
        self.assertNotIn(self.ANTIGO, obs)
        self.assertIn("NECESSIDADE ADICIONAL DE 2 UN.", obs)

    def test_falta_maior_em_uma_op_nao_desaparece_ao_diminuir_em_outra(self):
        # O material passa de 4 para 6 faltantes, mas a OP nova ganha 5
        # de falta e a antiga perde 3. A comparação líquida deve bater.
        def linha(op, qtd, acao):
            return self.linha(op, "24/11/2026", "11/12/2026", 202647, qtd, acao)

        antes = [linha(self.ANTIGO, 4, "CRIAR S.C. 4 para semana 202647"),
                 linha(self.NOVO, 6, "Estoque 6")]
        agora = [linha(self.ANTIGO, 1, "CRIAR S.C. 1 para semana 202647"),
                 linha(self.NOVO, 11, "Estoque 6; CRIAR S.C. 5 para semana 202647")]

        def macro(demanda):
            return pd.DataFrame([{"Código": 158, "Saldo em Estoque": 6, "Demanda": demanda,
                                  "P.C.": 0, "S.C.": 0, "Produzindo": 0}])

        referencia = macro(12)
        hist = {"macro_anterior": macro(10), "alocacoes_anterior": pd.DataFrame(antes),
                "macro_referencia": referencia, "alocacoes_referencia": pd.DataFrame(agora)}
        resultado = self.analisar([self.compra(self.ANTIGO, 1), self.compra(self.NOVO, 5)],
                                   agora, referencia="2026-11-26", macro_atual=referencia,
                                   historico=hist)["MATERIAIS OP"].set_index("OP")
        self.assertEqual(resultado.loc[self.NOVO, "Parecer do analista"], "DEMANDA")
        obs = resultado.loc[self.NOVO, "Observações da análise"]
        self.assertIn(f"OP {self.NOVO} (+5 UN.)", obs)
        self.assertIn("NECESSIDADE ADICIONAL DE 5 UN. NESTA OP", obs)
        self.assertNotIn("Estoque 6", obs)
        self.assertEqual(resultado.loc[self.ANTIGO, "Observações da análise"], "")

    def test_reducao_parcial_de_sc_exibe_so_as_unidades_sem_reposicao(self):
        row = self._variacao((0,8,0,8,0),(0,8,3,0,0),
                             "S.C. 8","P.C. 3; CRIAR S.C. 5 para semana 202647",5)
        self.assertIn("REDUÇÃO DE S.C. SEM REPOSIÇÃO: 5 UN.",row["Observações da análise"])
        self.assertNotIn("P.C.",row["Observações da análise"])

    def test_reducao_de_sc_sem_compensacao_gera_falta(self):
        row = self._variacao((0,8,0,8,0),(0,8,0,3,0),
                             "S.C. 8","S.C. 3; CRIAR S.C. 5 para semana 202647",5)
        self.assertEqual(row["Parecer do analista"],"DEMANDA")
        self.assertIn("REDUÇÃO DE S.C. SEM REPOSIÇÃO: 5 UN.",row["Observações da análise"])

    def test_sc_convertida_em_pc_nao_explica_compra_extra(self):
        row = self._variacao((0,8,0,8,0),(0,10,8,0,0),
                             "S.C. 8","P.C. 8; CRIAR S.C. 2 para semana 202647",2)
        self.assertIn("AUMENTO DE DEMANDA",row["Observações da análise"])
        self.assertNotIn("S.C.",row["Observações da análise"])

    def test_queda_pc_sem_aumento_ou_parcial_fica_para_conferencia(self):
        for saldo, acao, qtd, motivo in [
            (0, "CRIAR S.C. 8 para semana 202647", 8, "SEM AUMENTO DE ESTOQUE"),
            (3, "Estoque 3; CRIAR S.C. 5 para semana 202647", 5, "SALDO A CONFERIR: 5 UN."),
        ]:
            with self.subTest(saldo=saldo):
                row = self._variacao((0,8,8,0,0),(saldo,8,0,0,0),"P.C. 8",acao,qtd)
                self.assertEqual(row["Parecer do analista"],"VERIFICAR")
                self.assertIn(motivo,row["Observações da análise"])

    def test_queda_pc_sem_duplicar_baixa_normal_de_estoque(self):
        row = self._variacao((2,10,8,0,0),(0,8,3,0,0),
                             "Estoque 2; P.C. 8","P.C. 3; CRIAR S.C. 5 para semana 202647",5)
        self.assertEqual(row["Parecer do analista"],"VERIFICAR")
        self.assertIn("REDUÇÃO DE P.C. DE 5 UN.",row["Observações da análise"])
        self.assertNotIn("POSSÍVEL ERRO DE ESTOQUE",row["Observações da análise"])

    def test_queda_pc_com_aumento_equivalente_nao_explica_a_falta(self):
        row = self._variacao((0,8,8,0,0),(8,10,0,0,0),
                             "P.C. 8","Estoque 8; CRIAR S.C. 2 para semana 202647",2)
        self.assertEqual(row["Parecer do analista"],"DEMANDA")
        self.assertIn("AUMENTO DE DEMANDA",row["Observações da análise"])
        self.assertNotIn("P.C.",row["Observações da análise"])

    def test_demanda_antiga_sem_motivo_retorna_verificar(self):
        from mrp_compra_preanalise import validar_pareceres_exportacao
        r = self.analisar([self.compra()], [
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        for aba in ["MATERIAIS OP", "DETALHE OP"]:
            self.assertEqual(r[aba].iloc[0]["Parecer do analista"], "VERIFICAR")
            self.assertEqual(r[aba].iloc[0]["Observações da análise"], "")
        validar_pareceres_exportacao(r, referencia="2026-11-25")
        r["MATERIAIS OP"].loc[:, "Parecer do analista"] = "DEMANDA"
        with self.assertRaisesRegex(ValueError, "parecer automático ausente"):
            validar_pareceres_exportacao(r, referencia="2026-11-25")

    def test_observacao_multiplos_projetos_com_datas_individuais(self):
        r = self.analisar([self.compra()], [
            self.linha(self.NOVO, "24/11/2026", "27/11/2026", 202647, 2, "Estoque 2"),
            self.linha(self.OUTRO, "25/11/2026", "04/12/2026", 202648, 3, "P.C. 3 (sem. 202648)"),
            self.linha(self.ANTIGO, "10/11/2026", "18/12/2026", 202650, 5,
                       "CRIAR S.C. 5 para semana 202650"),
        ])
        for aba in ["MATERIAIS OP", "DETALHE OP"]:
            linha = r[aba].iloc[0]
            self.assertEqual(linha["Parecer do analista"], "DEMANDA")
            self.assertIn(f"PROJETO {self.NOVO} (SOLICITAÇÃO: 24/11/2026)", linha["Observações da análise"])
            self.assertIn(f"PROJETO {self.OUTRO} (SOLICITAÇÃO: 25/11/2026)", linha["Observações da análise"])


class LayoutPreAnaliseTests(unittest.TestCase):
    def setUp(self):
        CompraPreAnalisePorOpTests.setUp(self)

    def test_excel_formatado_duas_abas_e_integridade(self):
        from io import BytesIO
        from datetime import datetime
        from openpyxl import load_workbook
        from mrp_compra_preanalise import exportar_preanalise_formatada, PREANALISE_VERSAO
        entrada = self.entrada.copy()
        entrada["vunit"] = [0, 19.5, 32.8, 0, 0]
        planilhas = construir_relatorio_compra_por_op(entrada, self.desc)
        bytes_xlsx = exportar_preanalise_formatada(planilhas)
        wb = load_workbook(BytesIO(bytes_xlsx))
        self.assertEqual(wb.sheetnames, ["RESUMO OP", "MATERIAIS OP"])
        self.assertEqual(wb.active.title, "MATERIAIS OP")
        ws = wb["MATERIAIS OP"]
        self.assertEqual(ws.freeze_panes, "C6")
        self.assertEqual(ws.auto_filter.ref, "A5:M9")
        self.assertFalse(ws.sheet_view.showGridLines)
        self.assertIn(PREANALISE_VERSAO, ws["A2"].value)
        self.assertIsNone(ws["A3"].value)
        self.assertTrue(ws.row_dimensions[4].hidden)
        self.assertEqual(ws["C6"].alignment.indent, 2)
        self.assertEqual(ws["D6"].alignment.indent, 1)
        self.assertEqual(ws["D6"].number_format, "#,##0")
        self.assertGreaterEqual(ws.row_dimensions[6].height, 28)
        self.assertEqual(ws["C6"].border.left.style, "thin")
        self.assertEqual(ws["A5"].value, "OP")
        self.assertEqual(ws["L5"].value, "Parecer do analista")
        self.assertEqual(ws["M5"].value, "Observações da análise")
        self.assertGreaterEqual(ws.column_dimensions["M"].width, 60)
        self.assertTrue(ws["M6"].alignment.wrap_text)
        self.assertEqual(len(ws.data_validations.dataValidation), 1)
        self.assertEqual(len(ws.conditional_formatting), 2)
        esperado = planilhas["MATERIAIS OP"]
        for i, linha in enumerate(esperado.to_dict("records"), 6):
            for j, nome in ((1,"OP"),(2,"Código"),(4,"Quantidade"),(5,"Valor mínimo encontrado"),(9,"Prioridade"),(12,"Parecer do analista"),(13,"Observações da análise")):
                valor = ws.cell(i,j).value
                self.assertEqual(valor if valor is not None else "", linha[nome])
            self.assertIsInstance(ws.cell(i,8).value, datetime)
        linha_multi = next(i for i in range(6,10) if ws.cell(i,7).value == 2)
        self.assertIn("9 un.", ws.cell(linha_multi,4).comment.text)
        self.assertIn("3 un.", ws.cell(linha_multi,4).comment.text)
        self.assertIn("prioridade 1", ws.cell(linha_multi,4).comment.text)
        resumo = wb["RESUMO OP"]
        self.assertIsNone(resumo["A3"].value)
        self.assertTrue(resumo.row_dimensions[4].hidden)
        self.assertEqual(resumo.freeze_panes, "B11")
        self.assertEqual(resumo.auto_filter.ref, "A10:I13")
        self.assertEqual(resumo["I7"].value, '=COUNTIF(\'MATERIAIS OP\'!$L$6:$L$9,"VERIFICAR")')
        self.assertEqual(resumo["F11"].value, "=COUNTIFS('MATERIAIS OP'!$A$6:$A$9,$A11,'MATERIAIS OP'!$L$6:$L$9,F$10)")
        self.assertTrue(wb.calculation.fullCalcOnLoad)
        self.assertEqual(wb.calculation.calcMode, "auto")
        self.assertEqual(ws["B6"].data_type, "s")

    def test_excel_preserva_texto_sem_transformar_em_formula(self):
        from io import BytesIO
        from openpyxl import load_workbook
        from mrp_compra_preanalise import exportar_preanalise_formatada
        p = construir_relatorio_compra_por_op(self.entrada, self.desc)
        p["MATERIAIS OP"].loc[0,"Observações da análise"] = '=HYPERLINK("https://example.com")'
        p["MATERIAIS OP"].loc[0,"Descrição"] = "Descrição longa " * 30
        w = load_workbook(BytesIO(exportar_preanalise_formatada(p)))["MATERIAIS OP"]
        self.assertEqual(w["M6"].data_type, "s")
        self.assertGreater(w.row_dimensions[6].height, 23)


class HistoricoDiarioTests(unittest.TestCase):
    def test_prioriza_primeiro_dia_anterior_e_usa_ultimo_e_imediato_como_alternativas(self):
        from mrp_compra_preanalise import ids_comparacao_diaria
        atual = {"id": 130, "created_at": "2026-11-25T14:00:00Z"}
        meta = [
            {"id": 131, "created_at": "2026-11-25T15:00:00Z"},
            atual,
            {"id": 129, "created_at": "2026-11-25T13:00:00Z"},
            {"id": 128, "created_at": "2026-11-25T10:58:00Z"},
            {"id": 126, "created_at": "2026-11-24T11:30:00Z"},
            {"id": 125, "created_at": "2026-11-24T11:00:00Z"},
        ]
        self.assertEqual(ids_comparacao_diaria(meta, atual), [125,126,129])

    def test_consulta_direta_encontra_primeira_fotografia_sem_depender_dos_50_ultimos(self):
        from unittest.mock import Mock
        from mrp_compra_preanalise import consultar_metadados_preanalise, ids_comparacao_diaria
        atual = {"id": 132, "created_at": "2026-11-26T12:00:00Z"}
        ultimo = {"id": 129, "created_at": "2026-11-26T01:30:00Z"}  # 25/11 22:30 em Patos
        primeiro = {"id": 127, "created_at": "2026-11-25T10:30:00Z"}
        imediato = {"id": 130, "created_at": "2026-11-26T11:58:00Z"}
        consultar = Mock(side_effect=[[ultimo], [primeiro], [imediato]])
        metadados = consultar_metadados_preanalise(consultar, atual)
        self.assertEqual(ids_comparacao_diaria(metadados, atual), [127, 129, 130])
        esperado = {"select": "id,created_at", "limit": "1"}
        self.assertEqual([c.args[0] for c in consultar.call_args_list], [
            {**esperado, "order": "created_at.desc,id.desc", "created_at": "lt.2026-11-26T03:00:00+00:00"},
            {**esperado, "order": "created_at.asc,id.asc",
             "and": "(created_at.gte.2026-11-25T03:00:00+00:00,created_at.lt.2026-11-26T03:00:00+00:00)"},
            {**esperado, "order": "created_at.desc,id.desc", "created_at": "lt.2026-11-26T12:00:00+00:00"},
        ])

    def test_fuso_local_e_ultimo_dia_disponivel(self):
        from mrp_compra_preanalise import ids_comparacao_diaria
        atual = {"id": 4, "created_at": "2026-11-23T10:00:00Z"}
        meta = [{"id":3,"created_at":"2026-11-23T01:00:00Z"},
                {"id":2,"created_at":"2026-11-19T15:00:00Z"}]
        self.assertEqual(ids_comparacao_diaria(meta, atual), [3])
        self.assertEqual(ids_comparacao_diaria(meta[1:], atual), [2])
        self.assertEqual(ids_comparacao_diaria([], atual), [])


if __name__ == "__main__":
    unittest.main()
