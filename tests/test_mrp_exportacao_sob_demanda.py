"""Exercita a tela de compra montada pelo entrypoint real, sem banco."""
import ast
import io
import unittest

import openpyxl
from streamlit.testing.v1 import AppTest

from mrp_engine_extract import montar_fonte_atual


class ExportacaoSobDemandaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = montar_fonte_atual()

    def test_previa_so_carrega_historico_e_monta_xlsx_quando_pedida(self):
        funcoes = {
            "render_validacao_compra_mrp", "_compra_botao_finalizar",
            "_compra_fechar", "_compra_menor_preco", "_compra_codigo",
            "normalizar_compra_mrp",
        }
        arvore = ast.parse(self.source)
        extraidas = "\n\n".join(
            ast.get_source_segment(self.source, node)
            for node in arvore.body if isinstance(node, ast.FunctionDef) and node.name in funcoes
        )
        app = AppTest.from_string(
            """
import pandas as pd
import streamlit as st
def formatar_data_br(s):
    return s
def _setta_dataframe(*args, **kwargs):
    return st.dataframe(*args, **kwargs)
def _compra_exclusoes_ler():
    return {}
def _historico_preanalise(snapshot_atual):
    st.session_state.historico = st.session_state.get("historico", 0) + 1
    return None
def _compra_excel_protheus(aptos):
    raise AssertionError("Carga oficial não deve ser gerada sem aprovação")
"""
            + extraidas
            + """
df = pd.DataFrame([
    {"produto":"00000158", "qnt":3, "data":"20/11/2026", "op":"26007206007", "prioridade":"1", "vunit":10},
    {"produto":"00000295", "qnt":2, "data":"20/11/2026", "op":"26031401001", "prioridade":"2", "vunit":30},
])
cadastro = pd.DataFrame({"Código":[158, 295], "Descrição":["Cabo", "Conector"]})
render_validacao_compra_mrp(df, "consulta", cadastro, snapshot_atual={"id":100})
"""
        ).run()
        self.assertFalse(app.exception)
        self.assertNotIn("historico", app.session_state)
        self.assertFalse(app.get("download_button"))
        self.assertTrue(app.button(key="consulta_compra_excel_inativo").disabled)
        self.assertEqual(list(app.dataframe[-1].value.columns),
                         ["Material","Quantidade","Necessidade","OP","Prioridade","Valor mínimo"])
        app.toggle(key="consulta_compra_campos_tecnicos").set_value(True).run()
        self.assertEqual(list(app.dataframe[-1].value.columns)[-4:],
                         ["PSY","Centro de custo","Observação","PRJ"])
        self.assertNotIn("historico", app.session_state)
        self.assertTrue(app.button(key="consulta_compra_excel_inativo").disabled)


        app.button(key="consulta_compra_preparar").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state.historico, 1)
        _, planilhas, xlsx, _ = app.session_state.consulta_compra_preparada
        self.assertEqual(planilhas["DETALHE OP"]["Quantidade"].sum(), 5)
        self.assertEqual(planilhas["DETALHE OP"]["Parecer do analista"].tolist(), ["OK", "VERIFICAR"])
        workbook = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True)
        self.assertEqual(workbook.sheetnames, ["RESUMO OP", "MATERIAIS OP"])
        workbook.close()
        self.assertEqual(len(app.get("download_button")), 1)
        self.assertTrue(app.button(key="consulta_compra_excel_inativo").disabled)

        app.run()
        self.assertEqual(app.session_state.historico, 1)
        app.multiselect(key="consulta_compra_relatorio_ops").set_value(["26007206007"]).run()
        self.assertNotIn("consulta_compra_preparada", app.session_state)
        self.assertFalse(app.get("download_button"))
        self.assertEqual(app.session_state.historico, 1)

        app.button(key="consulta_compra_preparar").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state.historico, 2)
        self.assertEqual(
            app.session_state.consulta_compra_preparada[1]["DETALHE OP"]["Quantidade"].tolist(), [3]
        )

    def test_planilhas_sao_preparadas_explicitamente_e_csvs_seguem_sob_demanda(self):
        calls = [
            n for n in ast.walk(ast.parse(self.source))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "download_button" and n.args
            and isinstance(n.args[0], ast.Constant)
            and n.args[0].value in {"BAIXAR TODOS — EXCEL", "BAIXAR TODOS — ZIP/CSV", "BAIXAR MRP GERAL — CSV"}
        ]
        self.assertEqual(len(calls), 5)
        self.assertEqual(self.source.count('_mrp_preparar_excel_relatorios(sheets, '), 2)
        helpers = [n for n in ast.parse(self.source).body
                   if isinstance(n, ast.FunctionDef) and n.name == "_mrp_preparar_excel_relatorios"]
        self.assertEqual(len(helpers), 1)
        gate = helpers[0].body[0]
        self.assertIsInstance(gate, ast.If)
        self.assertIn("Preparar relatório Excel", ast.unparse(gate.test))
        self.assertIn("dados = excel_bytes", ast.unparse(gate))

        for call in calls:
            kwargs = {p.arg: p.value for p in call.keywords}
            generator = kwargs["data"] if "data" in kwargs else call.args[1]
            if call.args[0].value == "BAIXAR TODOS — EXCEL":
                self.assertEqual(ast.unparse(generator), "dados")
            else:
                self.assertIsInstance(generator, ast.Lambda)
            self.assertEqual(kwargs["on_click"].value, "ignore")
            if call.args[0].value == "BAIXAR MRP GERAL — CSV":
                self.assertIn("_mrp_geral_export_sf", ast.unparse(generator))
