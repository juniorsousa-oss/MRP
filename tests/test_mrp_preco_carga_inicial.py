"""Protege o vínculo de preço OP/material e o cache da carga inicial."""
import ast
import unittest
from datetime import date

import pandas as pd

from mrp_engine_extract import montar_fonte_atual


class PrecoCargaInicialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = {
            n.name: n for n in ast.parse(montar_fonte_atual()).body
            if isinstance(n, ast.FunctionDef)
        }

    def test_cache_pertence_ao_zip_nao_ao_formatador_de_codigo(self):
        self.assertFalse(self.nodes["_compra_codigo"].decorator_list)
        self.assertIn("st.cache_data", ast.unparse(self.nodes["zip_bytes"].decorator_list[0]))

    def test_menor_valor_positivo_por_op_sem_emprestar_de_outra_op(self):
        deps = ("normalizar_compra_mrp", "_compra_codigo", "_preparar_compra_prioridades")
        env = {"pd": pd, "date": date, "formatar_data_br": lambda x: x}
        exec(compile(ast.Module([self.nodes[n] for n in deps], []), "<rotina-preco-mrp>", "exec"), env)
        entrada = pd.DataFrame([
            {"produto":"00000158", "qnt":2, "data":"01/01/2035", "op":op}
            for op in ("A", "B", "C", "")
        ])
        cad = pd.DataFrame({"Código":[158], "Lead Time (dias)":[5]})
        tratado = pd.DataFrame({
            "Código":[158]*7,
            "Projeto":["A","A","A","B","B","D","D"],
            "Valor mínimo encontrado":[70,50,0,"não informado",-1,20,0],
        })
        calcula = env["_preparar_compra_prioridades"]
        resultado = calcula(entrada, cad, tratado)
        self.assertEqual(resultado["vunit"].tolist(), [50,0,0,20])
        self.assertEqual(resultado["qnt"].tolist(), [2]*4)
        self.assertEqual(resultado["prioridade"].tolist(), ["1"]*4)
        legado = calcula(entrada, cad, tratado.drop(columns="Projeto"))
        self.assertEqual(legado["vunit"].tolist(), [20]*4)
