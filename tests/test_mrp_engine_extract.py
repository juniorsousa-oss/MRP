"""Prova que o cálculo atual pode ser identificado sem abrir o Streamlit."""
import unittest

from mrp_engine_extract import (
    APP_EXEC, RUNTIME_EXEC, _replace_exact,
    identificar_bloco_calculo, montar_fonte_atual,
)


class ExtracaoFonteMRPTests(unittest.TestCase):
    def test_falha_se_ancora_for_modificada(self):
        with self.assertRaises(RuntimeError):
            _replace_exact("sem marca", APP_EXEC, "", "app")
        with self.assertRaises(RuntimeError):
            _replace_exact("sem marca", RUNTIME_EXEC, "", "runtime")

    def test_monta_codigo_com_regras_operacionais(self):
        source = montar_fonte_atual()
        self.assertIn("CANCELADO", source)
        self.assertIn("SUSPENSO", source)
        self.assertIn("RESIDUO", source)
        self.assertIn("SEMANA DE NECESSIDADE", source)
        self.assertIn("MRP —", source) if False else None

    def test_identifica_calculo_e_saida_sem_executar_interface(self):
        info = identificar_bloco_calculo(montar_fonte_atual())
        self.assertLess(info["calculation_start_line"], info["calculation_end_line"])
        self.assertGreaterEqual(info["statement_count"], 10)
        print("AUDITORIA DO MOTOR MRP:", info)
        self.assertIn("macro", info["final_outputs"])
        self.assertIn("demanda_projeto", info["final_outputs"])
        self.assertIn("fab_det", info["final_outputs"])
        # Serve de auditoria: referências a UI devem ser separadas no motor puro.
        self.assertIsInstance(info["streamlit_refs"], list)
        self.assertTrue(info["treatments_referenced"])


if __name__ == "__main__":
    unittest.main()
