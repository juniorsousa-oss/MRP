"""Apresentação dos relatórios completos, sem editar dados ou cabeçalhos."""
from functools import lru_cache
from textwrap import wrap

from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# Título de impressão, larguras, colunas fixas, texto longo, quantidades, ênfase, aba.
_LAYOUTS = {
    "MRP_Geral": ("MRP Geral", (15,55,11,19,14,11,11,14,12,18,23,24),
                  2, (2,10,12), (4,5,6,7,8,9), (9,10), "142B43"),
    "Projecao_Semanal": ("Projeção Semanal", (15,54,11,14,24,17,14,11,11,14,18),
                         2, (2,5,11), (6,7,8,9,10,11), (11,), "234C69"),
    "Demanda_Projeto": ("Demanda por Projeto", (19,15,53,22,16,23,23,17,13,13,11,14,11,42,36),
                        2, (3,14,15), (8,9,10,11,12,13), (14,15), "234C69"),
    "Tratativas_Projetos": ("Tratativas de Projetos", (19,80,27,31),
                            1, (2,), (), (), "407473"),
    "Tratativas_Produtos": ("Tratativas de Produtos", (19,15,80,27,31),
                            2, (3,), (), (), "407473"),
    "Compras": ("Compras", (15,21,16,21,16,38,38,22),
                1, (6,7), (2,4,8), (8,), "407473"),
    "Fabricacao": ("Fabricação", (25,21,22,18),
                   2, (), (4,), (4,), "407473"),
    "Cadastro_Base": ("Cadastro Base", (68,13,13,23,24,16),
                       0, (1,), (4,5), (), "768799"),
}


def _fill(color):
    return PatternFill("solid", fgColor=color)


@lru_cache(maxsize=32)
def _corpo(par, numeric, long_text, accent):
    return (
        Font(name="Calibri", size=11, color="24384C", bold=accent),
        _fill("FFFFFF" if par else "F1F5F9"),
        Alignment(horizontal="right" if numeric else "left", vertical="center",
                  wrap_text=long_text, indent=1),
    )


def estilizar_relatorios_mrp(workbook):
    """Mantém endereços das células usados nos fluxos de Excel e Power Query."""
    workbook.properties.title = "SETTA | Relatórios do MRP"
    heading = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = _fill("142B43")
    result_fill = _fill("234C69")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    header_line = Side(style="thin", color="4E6680")
    header_border = Border(left=header_line, right=header_line, top=header_line,
                           bottom=Side(style="medium", color="91ABBE"))
    cell_line = Side(style="thin", color="CFDAE6")
    cell_border = Border(left=cell_line, right=cell_line, top=cell_line, bottom=cell_line)
    for sheet in workbook.worksheets:
        if sheet.title not in _LAYOUTS:
            continue
        title, widths, frozen, wrap_cols, numeric_cols, accents, tab_color = _LAYOUTS[sheet.title]
        if sheet.max_column != len(widths):
            # Evita associar formato numérico indevido se a estrutura mudar.
            continue
        last = get_column_letter(sheet.max_column)
        row_count = sheet.max_row
        sheet.sheet_view.showGridLines = False
        sheet.sheet_view.zoomScale = 90
        sheet.sheet_properties.tabColor = tab_color
        sheet.freeze_panes = get_column_letter(frozen+1) + "2"
        sheet.auto_filter.ref = f"A1:{last}{row_count}"
        sheet.row_dimensions[1].height = 36
        sheet.sheet_format.defaultRowHeight = 24
        sheet.print_title_rows = "1:1"
        sheet.print_area = f"A1:{last}{row_count}"
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A3 if len(widths)>10 else sheet.PAPERSIZE_A4
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.oddHeader.left.text = f"SETTA | {title}"
        sheet.oddHeader.left.size = 11
        sheet.oddFooter.right.text = "Página &P de &N"
        for i, cell in enumerate(sheet[1],1):
            cell.font = heading
            cell.fill = result_fill if i in accents else header_fill
            cell.alignment = header_alignment
            cell.border = header_border
            sheet.column_dimensions[cell.column_letter].width = widths[i-1]
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, max_row=row_count),2):
            lines = 1
            for i, c in enumerate(row,1):
                number = c.data_type == "n" and c.value is not None and i in numeric_cols
                long_text = i in wrap_cols
                c.font, c.fill, c.alignment = _corpo(row_num % 2 == 0, number, long_text, i in accents)
                c.border = cell_border
                if long_text and isinstance(c.value, str):
                    lines = max(lines, sum(
                        max(1,len(wrap(line, width=max(8,widths[i-1]-7))))
                        for line in c.value.splitlines()))
                if number:
                    if sheet.title == "Cadastro_Base" and i == 5:
                        c.number_format = '"R$" #,##0.00'
                    else:
                        c.number_format = "#,##0" if c.value == int(c.value) else "#,##0.00#"
            if lines > 1:
                sheet.row_dimensions[row_num].height = min(409, 14*lines+10)
        if row_count > 1 and sheet.title in {"MRP_Geral", "Projecao_Semanal"}:
            balance = "I" if sheet.title == "MRP_Geral" else "K"
            sheet.conditional_formatting.add(f"{balance}2:{balance}{row_count}",
                CellIsRule(operator="lessThan", formula=["0"], fill=_fill("FDE8E7"),
                           font=Font(color="9E3027", bold=True)))
        if row_count > 1 and sheet.title == "MRP_Geral":
            for status, background, color in (
                ("CRIAR S.C.", "FFF1D0", "784A08"), ("OK", "E3F4E8", "23653A")
            ):
                sheet.conditional_formatting.add(f"J2:J{row_count}",
                    FormulaRule(formula=[f'$J2="{status}"'],
                               fill=_fill(background), font=Font(color=color, bold=True)))
