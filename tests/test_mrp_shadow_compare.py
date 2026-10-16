"""Validação do comparador sem consultar nem alterar o Supabase."""
import base64
import gzip
import json
import unittest

import pandas as pd

from mrp_shadow_compare import (
    CAMPOS,
    abrir_snapshot,
    comparar_tabela,
    confrontar_mrp,
)


class ComparadorMRPTests(unittest.TestCase):
    def test_ordem_nao_altera_resultado_e_numeros_sao_tolerantes(self):
        original = pd.DataFrame({
            "Código": [10000001, 10000002],
            "DIV": [2, 1.5],
        })
        autonomo = pd.DataFrame({
            "DIV": [1.500000001, 2.0],
            "Código": [10000002, 10000001],
        })
        result = comparar_tabela(original, autonomo)
        self.assertTrue(result["identico"])
        self.assertEqual(result["linhas_ausentes"], 0)

    def test_divergencia_em_quantidade_ou_coluna_bloqueia_validacao(self):
        original = pd.DataFrame({"Código": [10000001], "DIV": [2]})
        autonomo = pd.DataFrame({"Código": [10000001], "DIV": [3]})
        result = comparar_tabela(original, autonomo)
        self.assertFalse(result["identico"])
        self.assertEqual(result["linhas_ausentes"], 1)
        self.assertEqual(result["linhas_adicionais"], 1)
        self.assertFalse(comparar_tabela(
            original, pd.DataFrame({"Código": [10000001], "SALDO": [2]})
        )["identico"])

    def test_registros_duplicados_sao_detectados(self):
        original = pd.DataFrame({"Código": [10000001, 10000001], "DIV": [2, 2]})
        autonomo = original.iloc[[0]].copy()
        result = comparar_tabela(original, autonomo)
        self.assertFalse(result["identico"])
        self.assertEqual(result["linhas_ausentes"], 1)

    def test_snapshot_compactado_usa_seis_secoes_e_nao_muta_registro(self):
        sections = {name: [] for name in CAMPOS.values()}
        sections["demanda_projeto"] = [{"Projeto": "123", "Necessidade": 2}]
        packed = base64.b64encode(
            gzip.compress(json.dumps(sections).encode("utf-8"))
        ).decode("ascii")
        oficial = {"id": 53, "semana_mrp": 202641, "compressed_payload": packed}
        normalizado = abrir_snapshot(oficial)
        self.assertEqual(normalizado["demanda_projeto"][0]["Necessidade"], 2)
        self.assertNotIn("demanda_projeto", oficial)
        frame = {
            campo: pd.DataFrame(normalizado[salvo])
            for campo, salvo in CAMPOS.items()
        }
        report = confrontar_mrp(frame, oficial)
        self.assertTrue(report["todos_iguais"])
        frame["demanda_projeto"]["Necessidade"] = 3
        self.assertFalse(confrontar_mrp(frame, oficial)["todos_iguais"])

    def test_historico_incompleto_nao_e_validado(self):
        with self.assertRaises(ValueError):
            abrir_snapshot({"demanda_projeto": []})


if __name__ == "__main__":
    unittest.main()
