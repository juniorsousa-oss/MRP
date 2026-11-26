"""Apresentação dos relatórios completos, sem editar dados ou cabeçalhos."""
from datetime import datetime, timezone
from functools import lru_cache
from textwrap import wrap
from zoneinfo import ZoneInfo

from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from mrp_identidade_setta import AMARELO, CINZA_CLARO, CINZA_ESCURO, CINZA_FUNDO, GRAFITE

# Título de impressão, larguras, colunas fixas, texto longo, quantidades, ênfase, aba.
_LAYOUTS = {
    "MRP_Geral": ("MRP Geral", (15,55,11,19,14,11,11,14,12,18,23,24),
                  2, (2,10,12), (4,5,6,7,8,9), (9,10), GRAFITE),
    "Projecao_Semanal": ("Projeção Semanal", (15,54,11,14,24,17,14,11,11,14,18),
                         2, (2,5,11), (6,7,8,9,10,11), (11,), CINZA_ESCURO),
    "Tratativas_Projetos": ("Tratativas de Projetos", (19,80,27,31),
                            1, (2,), (), (), CINZA_ESCURO),
    "Tratativas_Produtos": ("Tratativas de Produtos", (19,15,80,27,31),
                            2, (3,), (), (), CINZA_ESCURO),
    "Compras": ("Compras", (15,21,16,21,16,38,38,22),
                1, (6,7), (2,4,8), (8,), CINZA_ESCURO),
    "Fabricacao": ("Fabricação", (25,21,22,18),
                   2, (), (4,), (4,), CINZA_ESCURO),
    "Cadastro_Base": ("Cadastro Base", (68,13,13,23,24,16),
                       0, (1,), (4,5), (), "919191"),
}


# Colunas por nome para o projeto (15 no cálculo e 16 no espelho de
# consulta), comparativos históricos, e relatórios de outros módulos.
_LAYOUTS_POR_NOME = {
    "Demanda_Projeto": ("Demanda por Projeto", 2, CINZA_ESCURO),
    "MRP_Geral_Comparativo": ("Comparativo | MRP Geral", 2, GRAFITE),
    "Projecao_Comparativo": ("Comparativo | Projeção Semanal", 1, CINZA_ESCURO),
    "Demanda_Projeto_Comparativo": ("Comparativo | Demanda por Projeto", 2, CINZA_ESCURO),
    "Compras_Comparativo": ("Comparativo | Compras", 1, CINZA_ESCURO),
    "MRP_Anterior": ("MRP Anterior", 2, "919191"),
    "MRP_Atual": ("MRP Atual", 2, CINZA_ESCURO),
    "Compra_Anterior": ("Compra Anterior", 1, "919191"),
    "Compra_Atual": ("Compra Atual", 1, CINZA_ESCURO),
    "Solicitações SC": ("Excedentes | Solicitações de Compra", 0, CINZA_ESCURO),
    "Pedidos PC": ("Excedentes | Pedidos de Compra", 0, CINZA_ESCURO),
    "Materiais_por_SA": ("Solicitações Avulsas | Materiais", 1, CINZA_ESCURO),
}

_LONGOS = {"descrição": 53, "ação": 42, "resumo": 36, "obs": 46, "justificativa": 46}
_LARGURAS = {
    "código": 15, "produto": 15, "projeto": 19, "tipo": 11, "op": 20,
    "última solicitação": 22, "data cm": 16, "semana": 14,
    "semana de necessidade": 23, "semana de atendimento": 23,
    "semana prevista": 19, "período de atendimento": 24,
    "status de atendimento": 23, "status": 18, "classificação": 20,
    "cancelamento": 18, "solicitado em": 21, "solicitante": 28,
    "finalidade": 27, "situação": 26, "validação final": 18,
}
_QUANTIDADES = {
    "demanda", "saldo em estoque", "necessidade", "estoque", "pré nota",
    "p.c.", "s.c.", "fabricação", "produzindo", "div", "sf", "saldo inicial",
    "resumo final", "quantidade", "qtd. cancelar", "qnt", "vunit",
}
_DESTAQUES = {
    "ação", "resumo", "status de atendimento", "classificação", "sf", "div",
    "resumo final", "qtd. cancelar", "cancelamento", "situação",
}


def _layout_por_nome(sheet):
    titulo, fixas, cor = _LAYOUTS_POR_NOME.get(sheet.title, (sheet.title, 0, CINZA_ESCURO))
    widths, wrap_cols, numeric_cols, accents = [], [], [], []
    for i, cell in enumerate(sheet[1], 1):
        name = str(cell.value or "").strip().casefold()
        # Nos comparativos, "anterior", "atual" e delta mantêm a unidade
        # do mesmo campo, sem tratar código/semana/prioridade como quantidade.
        base = name.removeprefix("δ ").removesuffix(" anterior").removesuffix(" atual")
        width = _LONGOS.get(name) or _LARGURAS.get(name) or max(13, min(38, len(name) + 5))
        if name != base:
            width = max(width, min(34, len(name) + 6))
        widths.append(width)
        if name in _LONGOS:
            wrap_cols.append(i)
        if base in _QUANTIDADES:
            numeric_cols.append(i)
        if name in _DESTAQUES or name.startswith("δ "):
            accents.append(i)
    return titulo, widths, min(fixas, max(0, sheet.max_column - 1)), wrap_cols, numeric_cols, accents, cor


def formatar_referencia_espelho(identificador, criado_em):
    """Identifica a execução exata, inclusive duas fotografias do mesmo dia."""
    try:
        dt = datetime.fromisoformat(str(criado_em).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return f"MRP {int(identificador)} (data indisponível)"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(ZoneInfo("America/Sao_Paulo"))
    return f"MRP {int(identificador)} | {local:%d/%m/%Y %H:%M:%S} (Brasília)"


def _fill(color):
    return PatternFill("solid", fgColor=color)


@lru_cache(maxsize=32)
def _corpo(par, numeric, long_text, accent):
    return (
        Font(name="Calibri", size=11, color=GRAFITE, bold=accent),
        _fill("FFFFFF" if par else CINZA_FUNDO),
        Alignment(horizontal="right" if numeric else "left", vertical="center",
                  wrap_text=long_text, indent=1),
    )


def estilizar_relatorios_mrp(workbook, *, espelhos=()):
    """Mantém endereços das células usados nos fluxos de Excel e Power Query."""
    workbook.properties.title = "SETTA | Relatórios do MRP"
    if espelhos:
        anterior, atual = espelhos
        workbook.properties.subject = f"Anterior: {anterior}; Atual: {atual}"
    heading = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = _fill(GRAFITE)
    result_fill = _fill(CINZA_ESCURO)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    header_line = Side(style="thin", color="626262")
    header_border = Border(left=header_line, right=header_line, top=header_line,
                           bottom=Side(style="medium", color=AMARELO))
    cell_line = Side(style="thin", color=CINZA_CLARO)
    cell_border = Border(left=cell_line, right=cell_line, top=cell_line, bottom=cell_line)
    for sheet in workbook.worksheets:
        layout = _LAYOUTS.get(sheet.title)
        if sheet.title not in _LAYOUTS_POR_NOME and layout is None:
            continue
        if layout is None or sheet.max_column != len(layout[1]):
            # Nunca pule o visual de uma aba reconhecida por mudança de esquema.
            layout = _layout_por_nome(sheet)
        title, widths, frozen, wrap_cols, numeric_cols, accents, tab_color = layout
        last = get_column_letter(sheet.max_column)
        row_count = sheet.max_row
        sheet.sheet_view.showGridLines = False
        sheet.sheet_view.zoomScale = 90
        sheet.sheet_properties.tabColor = tab_color
        if any(cell.value is not None for cell in sheet[1]):
            sheet.freeze_panes = get_column_letter(frozen+1) + "2"
            sheet.auto_filter.ref = f"A1:{last}{row_count}"
            sheet.print_title_rows = "1:1"
            sheet.print_area = f"A1:{last}{row_count}"
        sheet.row_dimensions[1].height = 36
        sheet.sheet_format.defaultRowHeight = 24
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A3 if len(widths)>10 else sheet.PAPERSIZE_A4
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.oddHeader.left.text = f"SETTA | {title}"
        sheet.oddHeader.left.size = 11
        sheet.oddFooter.right.text = "Página &P de &N"
        if espelhos:
            # Cabeçalho/rodapé de impressão e propriedade do arquivo, sem
            # inserir linhas/colunas ou misturar metadados com a tabela.
            sheet.oddFooter.left.text = f"Anterior: {anterior}"
            sheet.oddFooter.center.text = f"Atual: {atual}"
        headers = sheet[1]
        currency_columns = {i for i, cell in enumerate(headers, 1)
                            if str(cell.value).strip().casefold() == "vunit"}
        if sheet.title == "Cadastro_Base" and layout is _LAYOUTS["Cadastro_Base"]:
            currency_columns.add(5)
        for i, cell in enumerate(headers,1):
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
                    if i in currency_columns:
                        c.number_format = '"R$" #,##0.00'
                    else:
                        c.number_format = "#,##0" if c.value == int(c.value) else "#,##0.00#"
            if lines > 1:
                sheet.row_dimensions[row_num].height = min(409, 14*lines+10)
        if row_count <= 1:
            continue
        columns = {str(cell.value).strip().casefold(): cell.column_letter for cell in headers}
        balance = (columns.get("div") or columns.get("sf")) if sheet.title in {
            "MRP_Geral", "MRP_Anterior", "MRP_Atual"
        } else columns.get("resumo final") if sheet.title == "Projecao_Semanal" else None
        if balance:
            sheet.conditional_formatting.add(f"{balance}2:{balance}{row_count}",
                CellIsRule(operator="lessThan", formula=["0"], fill=_fill("FDE8E7"),
                           font=Font(color="9E3027", bold=True)))

        palettes = {
            "status": (("CRIAR S.C.", "FFF1D0", "784A08"), ("OK", "E3F4E8", "23653A")),
            "classificação": (("ALTERADO", "FFF1D0", "784A08"), ("NOVO", "E1EFFA", CINZA_ESCURO),
                              ("REMOVIDO", "FDE8E7", "9E3027"), ("NOVO S.C.", "FDE8E7", "9E3027"),
                              ("NORMALIZADO", "E3F4E8", "23653A")),
            "cancelamento": (("TOTAL", "FDE8E7", "9E3027"), ("PARCIAL", "FFF1D0", "784A08")),
            "situação": (("ENTREGUE", "E3F4E8", "23653A"), ("RECUSADA", "FDE8E7", "9E3027"),
                         ("AGUARDANDO SEPARAÇÃO", "FFF1D0", "784A08"),
                         ("SEPARADA", "E1EFFA", CINZA_ESCURO)),
        }
        for field, palette in palettes.items():
            col = columns.get(field)
            if col:
                for status, background, color in palette:
                    sheet.conditional_formatting.add(f"{col}2:{col}{row_count}",
                        FormulaRule(formula=[f'${col}2="{status}"'],
                                   fill=_fill(background), font=Font(color=color, bold=True)))
