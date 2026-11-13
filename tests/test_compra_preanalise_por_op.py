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


if __name__ == "__main__":
    unittest.main()
