import ast
import unittest
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook

from mrp_engine_extract import montar_fonte_atual


class RelatorioExcelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = montar_fonte_atual()
        fn = next(n for n in ast.parse(cls.source).body if isinstance(n, ast.FunctionDef) and n.name == "excel_bytes")
        fn.decorator_list = []
        context = {"pd": pd, "BytesIO": BytesIO}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<export>", "exec"), context)
        cls._export = staticmethod(context["excel_bytes"])

    def test_export_style_preserves_values_and_positions(self):
        cols = ["Código", "Descrição", "Tipo", "Saldo em Estoque", "Demanda",
                "P.C.", "S.C.", "Produzindo", "SF", "Status",
                "Semana de Atendimento", "Período de Atendimento"]
        data = pd.DataFrame([["00000012","Peça de teste","MP",0,3,0,0,0,-3,"CRIAR S.C.","NN","NN"],
                             ["00000013","Peça de teste","MP",7,3,0,0,0,4,"OK","",""]],
                            columns=cols)
        raw = load_workbook(BytesIO(self._export({"MRP_Geral": data}))).active
        formatted = load_workbook(BytesIO(self._export({"MRP_Geral": data}, layout_relatorio=True))).active
        self.assertEqual(list(formatted.values), list(raw.values))
        self.assertEqual(formatted["A2"].data_type, "s")
        self.assertEqual(formatted.freeze_panes, "C2")
        self.assertEqual(formatted.auto_filter.ref, "A1:L3")
        self.assertEqual(formatted.print_title_rows, "$1:$1")
        self.assertEqual(len(formatted.conditional_formatting), 2)
        for row in formatted.iter_rows():
            for c in row:
                for edge in ("left", "right", "top", "bottom"):
                    self.assertIn(getattr(c.border, edge).style, {"thin", "medium"}, (c.coordinate, edge))
        self.assertIsNone(raw.freeze_panes)

    def test_only_report_downloads_use_new_layout(self):
        hits = [line for line in self.source.splitlines() if "layout_relatorio=True" in line]
        self.assertEqual(len(hits), 2)
        self.assertTrue(any("MRP_Relatorios_Completos.xlsx" in l for l in hits))
        self.assertTrue(any("MRP_Consulta.xlsx" in l for l in hits))
        purchase = load_workbook(BytesIO(self._export({"Compra_MRP": pd.DataFrame({"produto": ["00000012"]})}))).active
        self.assertIsNone(purchase.freeze_panes)
        self.assertEqual(purchase["A2"].value, "00000012")
