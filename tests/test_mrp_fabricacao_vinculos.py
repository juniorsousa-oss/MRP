"""Regressões: PMP PROGRAMADO sem BOM H001 não pode gerar S.C. indevida."""
import unittest

import pandas as pd

from mrp_fabricacao_vinculos import filtrar_tctp_para_mrp


def linha(op, produto, material, quantidade, semana=202647):
    return {
        "ORDEM DE PRODUÇÃO": op,
        "Código Produto": produto,
        "Material": material,
        "Quantidade": quantidade,
        "Semana Entrega": semana,
        "Semana Necessidade": semana,
    }


class FabricacaoSemBomTests(unittest.TestCase):
    def test_op_26_1120_01_70150003_programada_mas_sem_bom(self):
        # Arquivo PMP de 18/11: C=70150003, STATUS=PROGRAMADO,
        # PROGRAMADO=1, PRODUZIDO=0, UNIFICADO vazio, OP=26-1120-01.
        # O Conversor gera MATERIAL=0 / Quantidade=0 quando H001 sem BOM.
        mt = pd.DataFrame([
            linha("26-1120-01", 70150003, 0, 0),
        ])
        filtrado = filtrar_tctp_para_mrp(mt, {70150003})
        self.assertEqual(len(filtrado), 1)
        self.assertEqual(int(filtrado.iloc[0]["Código Produto"]), 70150003)
        # A demanda TC/TP vem APENAS de linhas com material real.
        tc_rows = filtrado[
            (filtrado["Material"] > 0)
            & filtrado["Semana Necessidade"].between(1, 999953)
        ]
        self.assertTrue(tc_rows.empty)
        # A oferta de produto acabado conta uma OP uma vez.
        op = filtrado[
            (filtrado["Código Produto"] > 0)
            & filtrado["Semana Entrega"].between(1, 999953)
        ]
        oferta = op.groupby(["Código Produto", "Semana Entrega"])[
            "ORDEM DE PRODUÇÃO"
        ].nunique()
        self.assertEqual(oferta.loc[(70150003, 202647)], 1)
        estoque, demanda, pc, sc = 0, 1, 0, 0
        produzindo = int(oferta.loc[(70150003, 202647)])
        self.assertEqual(estoque + pc + sc + produzindo - demanda, 0)

    def test_material_real_continua_gerando_demanda_mas_op_conta_uma_vez(self):
        mt = pd.DataFrame([
            linha("26-1120-01", 70150003, 70020016, 2),
            linha("26-1120-01", 70150003, 70150002, 1),
        ])
        filtrado = filtrar_tctp_para_mrp(
            mt, {70150003, 70020016, 70150002}
        )
        self.assertEqual(len(filtrado), 2)
        self.assertEqual(filtrado["Quantidade"].sum(), 3)
        self.assertEqual(filtrado["ORDEM DE PRODUÇÃO"].nunique(), 1)

    def test_linha_sem_bom_nunca_gera_demanda_ficticia(self):
        mt = pd.DataFrame([
            linha("26-1120-01", 70150003, 0, 0),
            linha("26-1121-01", 70150003, 99999999, 2),
            linha("26-1122-01", 99999999, 0, 0),
        ])
        filtrado = filtrar_tctp_para_mrp(mt, {70150003})
        self.assertEqual(filtrado["ORDEM DE PRODUÇÃO"].tolist(), ["26-1120-01"])
        self.assertEqual(filtrado["Quantidade"].sum(), 0)

    def test_sem_op_nao_pode_entrar_na_producao(self):
        mt = pd.DataFrame([linha("", 70150003, 0, 0)])
        filtrado = filtrar_tctp_para_mrp(mt, {70150003})
        self.assertTrue(filtrado.empty)

    def test_codigos_textuais_do_tctp_sao_aceitos(self):
        mt = pd.DataFrame([
            linha("26-1120-01", "70150003", "0", "0"),
        ])
        filtrado = filtrar_tctp_para_mrp(mt, {70150003})
        self.assertEqual(len(filtrado), 1)

    def test_exige_colunas_para_evitar_contabilizacao_indefinida(self):
        with self.assertRaisesRegex(ValueError, "TCTP sem colunas"):
            filtrar_tctp_para_mrp(pd.DataFrame({"Material": [0]}), {70150003})


if __name__ == "__main__":
    unittest.main()
