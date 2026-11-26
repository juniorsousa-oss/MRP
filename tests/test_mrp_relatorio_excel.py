import ast
import unittest
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook

from mrp_engine_extract import montar_fonte_atual
from mrp_relatorio_excel import formatar_referencia_espelho


class RelatorioExcelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = montar_fonte_atual()
        fn = next(n for n in ast.parse(cls.source).body if isinstance(n, ast.FunctionDef) and n.name == "excel_bytes")
        fn.decorator_list = []
        context = {"pd": pd, "BytesIO": BytesIO}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<export>", "exec"), context)
        cls._export = staticmethod(context["excel_bytes"])

    def test_rotas_usam_cache_versionado_e_comparativo_pronto_antes_do_download(self):
        self.assertIn('excel_bytes(s, layout_relatorio=True, versao_layout="2026-11-26-v8")', self.source)
        self.assertIn('excel_bytes(report, layout_relatorio=True, espelhos=_espelhos, versao_layout="2026-11-26-v8")', self.source)
        self.assertNotIn("lambda r=report, e=_espelhos", self.source)

    def test_preparo_excel_so_gera_ao_ser_solicitado(self):
        from streamlit.testing.v1 import AppTest

        node = next(n for n in ast.parse(self.source).body
                    if isinstance(n, ast.FunctionDef) and n.name == "_mrp_preparar_excel_relatorios")
        source = (
            "import streamlit as st\n"
            "def excel_bytes(s, **kwargs):\n"
            "    st.session_state.calls = st.session_state.get('calls', 0) + 1\n"
            "    return b'planilha-de-teste'\n"
            + ast.unparse(node)
            + "\nwith st.popover('Exportar'):\n"
            "    _mrp_preparar_excel_relatorios({}, 'MRP_Consulta.xlsx')\n"
        )
        app = AppTest.from_string(source).run()
        self.assertFalse(app.exception)
        self.assertNotIn("calls", app.session_state)
        self.assertFalse(app.get("download_button"))
        app.button(key="preparar_excel_MRP_Consulta.xlsx").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state.calls, 1)
        self.assertEqual(len(app.get("download_button")), 1)

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

    def test_demanda_with_and_without_status_keeps_layout_and_values(self):
        columns = ["Projeto","Produto","Descrição","Última Solicitação","Data CM",
                   "Semana de Necessidade","Semana de Atendimento","Necessidade","Estoque",
                   "Pré Nota","P.C.","Fabricação","S.C.","Ação","Resumo"]
        frame = pd.DataFrame([["P1","00000042","Material para teste","01/10/2026","05/10/2026",
                               202645,"NN",2.25,1,0,0,0,0,"CRIAR S.C.","Obs. de teste"]], columns=columns)
        for with_status in (False, True):
            with self.subTest(with_status=with_status):
                data = frame.copy()
                if with_status:
                    data.insert(7, "Status de Atendimento", "🔴")
                raw = load_workbook(BytesIO(self._export({"Demanda_Projeto": data}))).active
                sheet = load_workbook(BytesIO(self._export({"Demanda_Projeto": data}, layout_relatorio=True))).active
                self.assertEqual(list(raw.values), list(sheet.values))
                self.assertEqual(sheet["B2"].data_type, "s")
                self.assertEqual(sheet.freeze_panes, "C2")
                self.assertEqual(sheet.auto_filter.ref, "A1:P2" if with_status else "A1:O2")
                quantity = "I2" if with_status else "H2"
                self.assertEqual(sheet[quantity].number_format, "#,##0.00#")
                self.assertEqual(sheet[quantity].alignment.horizontal, "right")
                self.assertEqual(sheet["C2"].alignment.indent, 1)
                self.assertEqual(sheet["C2"].border.bottom.style, "thin")
                self.assertTrue(sheet["C2"].alignment.wrap_text)
                if with_status:
                    self.assertEqual(sheet["H2"].number_format, "General")

    def test_comparativo_styles_every_sheet_preserves_data_and_identifies_snapshots(self):
        old = formatar_referencia_espelho(17, "2026-11-25T11:03:12Z")
        new = formatar_referencia_espelho(22, "2026-11-26T11:07:45+00:00")
        self.assertEqual(old, "MRP 17 | 25/11/2026 08:03:12 (Brasília)")
        self.assertEqual(new, "MRP 22 | 26/11/2026 08:07:45 (Brasília)")
        self.assertIn("indisponível", formatar_referencia_espelho(1, None))
        report = {
            "MRP_Geral_Comparativo": pd.DataFrame({"Código":[700],"Classificação":["ALTERADO"],
                                                  "Δ Demanda":[-1.125],"Descrição":["Peça"]}),
            "Projecao_Comparativo": pd.DataFrame({"Código":[700],"Semana":[202647],"Classificação":["NOVO"]}),
            "Demanda_Projeto_Comparativo": pd.DataFrame({"Projeto":["P1"],"Produto":["00000042"],
                                              "Semana de Necessidade":[202647],"Classificação":["ALTERADO"]}),
            "Compras_Comparativo": pd.DataFrame({"produto":["00000042"],"op":["OP7"],"Classificação":["REMOVIDO"]}),
            "MRP_Anterior": pd.DataFrame({"Código":[700],"Descrição":["Peça"],"DIV":[0]}),
            "MRP_Atual": pd.DataFrame({"Código":[700],"Descrição":["Peça"],"DIV":[-1.125],"Fórmula":["=SUM(C2)"]}),
            "Compra_Anterior": pd.DataFrame({"produto":["00000042"],"qnt":[1]}),
            "Compra_Atual": pd.DataFrame({"produto":["00000042"],"qnt":[2],"vunit":[10.25]}),
        }
        plain = load_workbook(BytesIO(self._export(report)))
        styled = load_workbook(BytesIO(self._export(report, layout_relatorio=True, espelhos=(old, new))))
        self.assertEqual(styled.sheetnames, list(report))
        self.assertIn(old, styled.properties.subject)
        self.assertIn(new, styled.properties.subject)
        for s in styled.worksheets:
            self.assertEqual(list(plain[s.title].values), list(s.values))
            self.assertEqual(s["A1"].fill.fgColor.rgb[-6:], "142B43")
            self.assertEqual(s["A2"].border.bottom.style, "thin")
            self.assertIsNotNone(s.auto_filter.ref)
            self.assertIsNotNone(s.freeze_panes)
            self.assertIn(old, s.oddFooter.left.text)
            self.assertIn(new, s.oddFooter.center.text)
        self.assertEqual(styled["MRP_Atual"]["D2"].data_type, "f")
        self.assertEqual(styled["MRP_Atual"]["D2"].value, "=SUM(C2)")
        self.assertEqual(styled["Projecao_Comparativo"]["B2"].number_format, "General")
        self.assertEqual(styled["Compra_Atual"]["C2"].number_format, '"R$" #,##0.00')
        self.assertTrue(len(styled["MRP_Geral_Comparativo"].conditional_formatting))

    def test_avulsas_formats_quantity_not_codes_and_comparison_can_be_empty(self):
        columns = ["S.A.","SOLICITADO EM","SOLICITANTE","CÓDIGO","DESCRIÇÃO","QUANTIDADE","SITUAÇÃO"]
        data = pd.DataFrame([["SA7","26/11/2026","Jr","00000042","Produto",1.375,"ENTREGUE"]], columns=columns)
        styled = load_workbook(BytesIO(self._export({"Materiais_por_SA": data,
            "Compras_Comparativo": pd.DataFrame()}, layout_relatorio=True)))
        sheet = styled["Materiais_por_SA"]
        self.assertEqual(list(sheet[1][i].value for i in range(7)), columns)
        self.assertEqual(sheet["D2"].value, "00000042")
        self.assertEqual(sheet["F2"].value, 1.375)
        self.assertEqual(sheet["F2"].alignment.horizontal, "right")
        self.assertEqual(sheet["F2"].border.left.style, "thin")
        self.assertTrue(sheet["E2"].alignment.wrap_text)
        blank = styled["Compras_Comparativo"]
        self.assertIsNone(blank["A1"].value)
        self.assertIsNone(blank.auto_filter.ref)
        self.assertFalse(blank.sheet_view.showGridLines)

    def test_only_report_downloads_use_new_layout(self):
        hits = [line for line in self.source.splitlines() if "layout_relatorio=True" in line]
        self.assertEqual(len(hits), 3)
        self.assertIn('_mrp_preparar_excel_relatorios(sheets, "MRP_Relatorios_Completos.xlsx")', self.source)
        self.assertIn('_mrp_preparar_excel_relatorios(sheets, "MRP_Consulta.xlsx")', self.source)
        self.assertTrue(any("Comparativo_MRP.xlsx" in l and "espelhos=_espelhos" in l for l in hits))
        self.assertTrue(any("Materiais_por_SA" in l for l in hits))
        for title in ("Compra_MRP", "Tratativas", "Tratativas_Produtos"):
            with self.subTest(title=title):
                purchase = load_workbook(BytesIO(self._export({title: pd.DataFrame({"produto": ["00000012"]})}))).active
                self.assertIsNone(purchase.freeze_panes)
                self.assertEqual(purchase["A2"].value, "00000012")
