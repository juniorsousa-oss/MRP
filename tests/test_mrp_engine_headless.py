"""Testes do motor extraído, sem API, Streamlit ou publicação."""
import unittest
from datetime import datetime

import pandas as pd

from mrp_engine_headless import calcular_mrp, construir_motor


class MotorPuroTests(unittest.TestCase):
    def _entradas(self):
        cadastro = pd.DataFrame({
            "Código": [10000001], "Descrição": ["MATERIAL TESTE"],
            "Tipo": ["MP"], "Ativo": ["S"],
        })
        estoque = pd.DataFrame({
            "Código": [10000001], "Saldo em Estoque": [5.0],
        })
        geral = pd.DataFrame({
            "Projeto": ["20260123456"],
            "Código": [10000001],
            "Pendência": [2.0],
            "Quantidade Solicitada": [2.0],
            "Data Solicitação": [pd.Timestamp("2026-10-10")],
            "Data CM": [pd.Timestamp("2026-10-25")],
            "Condição": ["NORMAL"],
            "Vinculação da Data": ["DATA MRP"],
            "Semana": [202641],
        })
        compras = pd.DataFrame({
            "Código": [10000001],
            "Quantidade S.C.": [0.0],
            "Semana S.C.": [float("nan")],
            "Quantidade P.C.": [0.0],
            "Semana P.C.": [float("nan")],
            "Nº S.C.": [""],
            "Nº P.C.": [""],
            "Saldo em Pré Nota": [0.0],
        })
        tctp = pd.DataFrame({
            "ORDEM DE PRODUÇÃO": pd.Series(dtype=str),
            "Código Produto": pd.Series(dtype="int64"),
            "Material": pd.Series(dtype="int64"),
            "Semana Entrega": pd.Series(dtype="int64"),
            "Quantidade": pd.Series(dtype="float64"),
            "Semana Necessidade": pd.Series(dtype="int64"),
        })
        projeto = pd.DataFrame(columns=["Projeto", "OBS"])
        produto = pd.DataFrame(columns=["Projeto", "Produto", "OBS"])
        return cadastro, estoque, geral, geral.copy(), compras, tctp, projeto, produto

    def test_motor_monta_sem_streamlit(self):
        self.assertTrue(callable(construir_motor()))

    def test_nao_aceita_tratativas_ausentes(self):
        args = list(self._entradas())
        args[-1] = None
        with self.assertRaises(ValueError):
            calcular_mrp(*args)

    def test_calculo_basico_com_todas_as_fontes(self):
        saidas = calcular_mrp(*self._entradas())
        self.assertEqual(len(saidas["macro"]), 1)
        geral = saidas["macro"].iloc[0]
        self.assertEqual(float(geral["Demanda"]), 2.0)
        self.assertEqual(float(geral["DIV"]), 3.0)
        self.assertEqual(len(saidas["demanda_projeto"]), 1)


    def test_residuo_de_projeto_nao_vira_demanda(self):
        args = list(self._entradas())
        args[6] = pd.DataFrame([{"Projeto": "20260123456", "OBS": "RESIDUO"}])
        saidas = calcular_mrp(*args)
        self.assertEqual(float(saidas["macro"].iloc[0]["Demanda S.A."]), 0.0)
        detalhe = saidas["demanda_projeto"].iloc[0]
        self.assertEqual(float(detalhe["Necessidade"]), 0.0)
        self.assertIn("RESÍDUO", detalhe["Ação"])

    def test_residuo_de_produto_nao_vira_demanda(self):
        args = list(self._entradas())
        args[7] = pd.DataFrame([{
            "Projeto": "20260123456", "Produto": "10000001", "OBS": "RESIDUO"
        }])
        saidas = calcular_mrp(*args)
        self.assertEqual(float(saidas["macro"].iloc[0]["Demanda S.A."]), 0.0)
        self.assertEqual(float(saidas["demanda_projeto"].iloc[0]["Necessidade"]), 0.0)

    def test_projeto_cancelado_ou_suspenso_e_preservado_sem_demanda(self):
        for condicao in ("CANCELADO", "SUSPENSO"):
            with self.subTest(condicao=condicao):
                args = list(self._entradas())
                for k in (2, 3):
                    args[k].loc[:, "Condição"] = condicao
                saidas = calcular_mrp(*args)
                self.assertEqual(float(saidas["macro"].iloc[0]["Demanda S.A."]), 0.0)
                detalhe = saidas["demanda_projeto"].iloc[0]
                self.assertEqual(float(detalhe["Necessidade"]), 0.0)
                self.assertIn(condicao, detalhe["Ação"])

    def test_tipo_ii_nao_aparece_com_demanda_de_compras(self):
        args = list(self._entradas())
        args[0].loc[:, "Tipo"] = "II"
        saidas = calcular_mrp(*args)
        self.assertEqual(float(saidas["macro"].iloc[0]["Demanda"]), 0.0)

    def test_fabricacao_conta_uma_op_uma_vez(self):
        args = list(self._entradas())
        args[5] = pd.DataFrame({
            "ORDEM DE PRODUÇÃO": ["OP-TESTE", "OP-TESTE"],
            "Código Produto": [10000001, 10000001],
            "Material": [10000001, 10000001],
            "Semana Entrega": [202642, 202642],
            "Quantidade": [1.0, 1.0],
            "Semana Necessidade": [202641, 202641],
        })
        saidas = calcular_mrp(*args)
        self.assertEqual(float(saidas["macro"].iloc[0]["Produzindo"]), 1.0)
        self.assertEqual(len(saidas["fab_det"]), 1)

    def test_calculo_repetido_e_deterministico_sem_modificar_entrada(self):
        args = self._entradas()
        antes = [df.copy(deep=True) for df in args]
        a = calcular_mrp(*args)
        b = calcular_mrp(*args)
        for campo in ("macro", "proj", "demanda_projeto", "compras_mrp", "fab_det"):
            with self.subTest(campo=campo):
                pd.testing.assert_frame_equal(a[campo], b[campo])
        for original, copia in zip(args, antes):
            pd.testing.assert_frame_equal(original, copia)


if __name__ == "__main__":
    unittest.main()
