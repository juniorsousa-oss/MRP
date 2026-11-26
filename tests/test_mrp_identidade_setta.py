import io
import unittest
from xml.etree import ElementTree

from PIL import Image
from openpyxl import Workbook

from mrp_identidade_setta import (
    AMARELO, ASSETS, EXCEL_LAYOUT_VERSION, GRAFITE,
    favicon_png, identidade_css, logo_data_uri,
)
from mrp_relatorio_excel import estilizar_relatorios_mrp
from mrp_workspace import workspace_header


class SettaBrandTests(unittest.TestCase):
    def test_official_assets_are_local_and_with_contrast(self):
        source = ElementTree.parse(ASSETS / "setta-logo-oficial.svg")
        paths = list(source.getroot())
        self.assertEqual(len(paths), 5)
        self.assertEqual({path.get("fill") for path in paths}, {"#" + GRAFITE})
        self.assertTrue((ASSETS / "outfit-latin.woff2").read_bytes().startswith(b"wOF2"))
        css = identidade_css()
        self.assertIn("data:font/woff2;base64,", css)
        self.assertNotIn("https://", css)
        with Image.open(io.BytesIO(favicon_png())) as icon:
            self.assertEqual(icon.size, (256, 256))
            self.assertEqual(icon.getpixel((0, 0))[3], 0)
            self.assertEqual(icon.getpixel((128, 9)), (255, 255, 255, 255))
            self.assertEqual(icon.getpixel((128, 25)), (51, 51, 51, 255))
            for size in (16, 32):
                small = icon.resize((size, size), Image.Resampling.LANCZOS)
                colors = list(small.getdata())
                self.assertTrue(any(r > 220 and g > 145 and b < 50 for r,g,b,a in colors if a > 230))
                self.assertTrue(any(r < 75 and g < 75 and b < 75 for r,g,b,a in colors if a > 230))
        self.assertEqual(EXCEL_LAYOUT_VERSION, "setta-v4.0")

    def test_header_uses_bundled_mark_and_not_arbitrary_svg(self):
        def render(asset):
            return workspace_header("MRP ATUAL", asset, "", None, semana=None,
                                    bases=(0, 5), registros=None, alertas=[],
                                    nome="", perfil="CONSULTA")

        self.assertIn(logo_data_uri(), render(logo_data_uri()))
        self.assertNotIn("data:image/svg+xml;base64,PHN2Zz4=", render("data:image/svg+xml;base64,PHN2Zz4="))

    def test_report_preserves_data_formats_and_alerts(self):
        wb = Workbook()
        sheet = wb.active
        sheet.title = "MRP_Atual"
        sheet.append(["Código", "Descrição", "DIV"])
        sheet.append(["00042", "Material", -1.5])
        estilizar_relatorios_mrp(wb, espelhos=("Antigo", "Atual"))
        self.assertEqual([c.value for c in sheet[2]], ["00042", "Material", -1.5])
        self.assertEqual(sheet["A1"].fill.fgColor.rgb[-6:], GRAFITE)
        self.assertEqual(sheet["A1"].border.bottom.color.rgb[-6:], AMARELO)
        self.assertEqual(sheet["A1"].font.name, "Calibri")
        self.assertEqual(sheet["C2"].number_format, "#,##0.00#")
        self.assertEqual(sheet.auto_filter.ref, "A1:C2")
        self.assertEqual(sheet.freeze_panes, "C2")
        self.assertEqual(len(sheet.conditional_formatting), 1)
