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


if __name__ == "__main__":
    unittest.main()
