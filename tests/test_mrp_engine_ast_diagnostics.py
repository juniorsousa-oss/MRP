"""Audita a localização do cálculo do MRP sem publicar dados nem exibir o código em logs."""
import ast
import unittest

from mrp_engine_extract import montar_fonte_atual, identificar_bloco_calculo


class MotorASTTests(unittest.TestCase):
    def test_localiza_calculo_sem_linhas_fixas(self):
        fonte = montar_fonte_atual()
        dados = identificar_bloco_calculo(fonte)
        self.assertIn("macro", dados["final_outputs"])
        self.assertIn("demanda_projeto", dados["final_outputs"])
        self.assertIn("compras_mrp", dados["final_outputs"])
        self.assertIn("fab_det", dados["final_outputs"])
        self.assertTrue(dados["treatments_referenced"])
        self.assertGreater(dados["calculation_end_line"], dados["calculation_start_line"])

    def test_localiza_cache_sem_executar_streamlit(self):
        arvore = ast.parse(montar_fonte_atual())
        caches = [
            node for node in arvore.body
            if isinstance(node, ast.If)
            and "_mrp_cached" in ast.unparse(node.test)
            and node.orelse
        ]
        self.assertEqual(len(caches), 1)


if __name__ == "__main__":
    unittest.main()
