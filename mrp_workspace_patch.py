"""Wire the approved presentation to the existing MRP workflows."""
WORKSPACE_PATCH = r"""
from textwrap import indent as _ws_indent

def _ws_replace(old, new):
    if _source.count(old) != 1:
        raise RuntimeError("Âncora do layout MRP mudou: " + old[:100])
    return _source.replace(old, new, 1)

_source = _ws_replace(
    '_mrp_pages=["MRP ATUAL", "SOLICITAÇÕES AVULSAS", "CONFIGURAÇÕES"] if _mrp_role=="ADMIN" else ["MRP ATUAL", "SOLICITAÇÕES AVULSAS"]',
    'from mrp_workspace import workspace_pages, workspace_sidebar, WorkspaceSection, workspace_header, WORKSPACE_V2_CSS\n_mrp_pages=workspace_pages(_mrp_role)')
_source = _ws_replace(
    'def _mrp_set_sidebar_page(page):\n    st.session_state["_mrp_sidebar_page"]=page',
    '''def _mrp_set_sidebar_page(page):
    if page in workspace_pages(st.session_state.get("auth_role")):
        if page != st.session_state.get("_mrp_sidebar_page"):
            for prefix in ("admin", "consulta"):
                _compra_fechar(prefix)
        st.session_state["_mrp_sidebar_page"]=page''')
for _callback in ("_mrp_dashboard_navigate", "_mrp_consulta_navigate"):
    _needle = f'def {_callback}(status_key, mostrar_nao_aptas):\n'
    _source = _ws_replace(_needle, _needle+'    _mrp_set_sidebar_page("DEMANDA POR PROJETO")\n')
_source = _ws_replace(
    '        _compra_fechar(prefixo)\n        st.rerun()',
    '        _mrp_set_sidebar_page("MRP ATUAL")\n        st.rerun()')
_a = _source.index('if _mrp_page=="MRP ATUAL":\n    st.html(OPERACAO_CSS)')
_b = _source.index('    # Conta acessível para todos os perfis.', _a)
_source = _source[:_a]+'''st.html(OPERACAO_CSS)
st.html(WORKSPACE_CSS)
st.html(WORKSPACE_V2_CSS)
from mrp_abas_visual import ABAS_VISUAL_CSS, limpar_filtros_projeto
st.html(ABAS_VISUAL_CSS)
st.html(workspace_header(
    _mrp_page,UI_CONFIG.get("logo_data"),_mrp_status,_mrp_when,
    semana=_mrp_sidebar_week,bases=(_mrp_base_ok,_mrp_base_total),
    registros=_mrp_rows_text,alertas=_mrp_alertas,
    nome=st.session_state.get("auth_nome"),perfil=_mrp_role,
))
with st.sidebar:
    with st.container(key="mrp_sidebar_nav"):
        workspace_sidebar(st,_mrp_pages,_mrp_page,_mrp_set_sidebar_page)
'''+_source[_b:]
_a = _source.index('    st.caption(f"Último MRP salvo')
_b = _source.index('    _mrp_manter_filtros_de_abas("consulta_operacao_colunas")',_a)
_source = _source[:_a]+'''    if _mrp_page in {"MRP ATUAL", "DEMANDA POR PROJETO"}:
'''+_ws_indent(_source[_source.index('    _status_dashboard_consulta=',_a):_b].rstrip(), '    ')+'\n\n'+_source[_b:]
_a = _source.index('    _consulta_operacao_compra=st.empty()')
_b = _source.index('    if tab_geral.open:',_a)
_source = _source[:_a]+'''    if _mrp_page == "ANÁLISE DE COMPRA":
        with st.container(key="mrp_visual_compra"):
            render_validacao_compra_mrp(comp,"consulta",mg,dem,dem,mg,snap)
        return
    if _mrp_page == "EXCEDENTES":
        with st.container(key="mrp_visual_excedentes"):
            exibir_analise_excedentes(mg,compras,proj,"consulta",snap.get("created_at"),pagina=True)
        return

    tab_geral,tab_projeto,tab_tratativa,tab_comparativo = (
        WorkspaceSection(_mrp_page == p) for p in
        ("MRP ATUAL","DEMANDA POR PROJETO","TRATATIVA DE PROJETOS","COMPARATIVO MRP")
    )
    if tab_geral.open:
        with st.container(key="mrp_operacao_bar_consulta"):
            _busca_area,_filtro_area,_colunas_area,_consulta_operacao_acoes=st.columns([5,1.28,1.28,1.5],vertical_alignment="bottom")
'''+_source[_b:]
_a = _source.index('    sheets = {\n        "MRP_Geral":')
_b = _source.index('    if st.session_state.get("consulta_compra_aberta",False):',_a)
_c = _source.index('\n\n\n@st.cache_data',_b)
_block = _source[_a:_b]
_block = _block.replace('        _exp,_ana=st.columns([1,1.2],vertical_alignment="bottom")\n','')
_start = _block.index('        _ana.button(')
_block = _block[:_start]+_block[_block.index('\n',_start)+1:]
_block = _block.replace('with _exp.popover(', 'with st.popover(')
_source = _source[:_a]+'    if tab_geral.open:\n'+_ws_indent(_block,'    ')+_source[_c:]
_a = _source.index("_status_dashboard=_mrp_status_atendimento_series(demanda_projeto)")
_b = _source.index("\n\n# Protege a última fotografia",_a)
_source = _source[:_a]+'if _mrp_page in {"MRP ATUAL","DEMANDA POR PROJETO"}:\n'+_ws_indent(_source[_a:_b],'    ')+_source[_b:]
_a = _source.index('_admin_operacao_compra=st.empty()')
_b = _source.index('if tab1.open:',_a)
_mcols = next(l for l in _source[_a:_b].splitlines() if l.startswith('macro_cols='))
_source = _source[:_a]+'''if _mrp_page == "ANÁLISE DE COMPRA":
    with st.container(key="mrp_visual_compra"):
        render_validacao_compra_mrp(normalizar_compra_mrp(compras_mrp),"admin",cad,rg,demanda_projeto,macro)
    st.stop()
if _mrp_page == "EXCEDENTES":
    with st.container(key="mrp_visual_excedentes"):
        exibir_analise_excedentes(macro,cp,proj,"admin",pagina=True)
    st.stop()

tab1,tab2,tab3,tab4 = (
    WorkspaceSection(_mrp_page == p) for p in
    ("MRP ATUAL","DEMANDA POR PROJETO","TRATATIVA DE PROJETOS","COMPARATIVO MRP")
)
'''+_mcols+'''
if tab1.open:
    with st.container(key="mrp_operacao_bar_admin"):
        _busca_area,_filtro_area,_colunas_area,_admin_operacao_acoes=st.columns([5,1.28,1.28,1.5],vertical_alignment="bottom")
'''+_source[_b:]
_a = _source.index("compras_mrp_export=normalizar_compra_mrp(compras_mrp)")
_b = _source.index('if st.session_state.get("admin_compra_aberta",False):',_a)
_c = _source.index('\n\n\n# trigger-final-2',_b)
_block = _source[_a:_b].split('\n',1)[1]
_block = "\n".join(l for l in _block.split("\n") if "_exp,_ana=" not in l and "_ana.button(" not in l).replace('with _exp.popover(', 'with st.popover(')
_summary = _source[_source.index("if len(compras_mrp): st.caption",_b):_c]
_source = _source[:_a]+'if tab1.open:\n'+_ws_indent(_block+_summary,'    ')+_source[_c:]
_source = _ws_replace(
    'st.caption(operacao_rotulo_grade(len(f)))',
    'st.caption(operacao_rotulo_grade(len(f)))\n            f = workspace_falta(f)')
_source = _ws_replace(
    'st.caption(operacao_rotulo_grade(len(v)))',
    'st.caption(operacao_rotulo_grade(len(v)))\n        v = workspace_falta(v)')
_source = _ws_replace(
    '_idx=operacao_grade(_df_exibicao_br(v[macro_cols]),',
    '_idx=operacao_grade(v[macro_cols+["Falta"]],')
_source = _ws_replace(
    '_idx=operacao_grade(_df_exibicao_br(f),',
    '_idx=operacao_grade(f,')
_source = _ws_replace(
    'from mrp_workspace import workspace_pages, workspace_sidebar, WorkspaceSection, workspace_header, WORKSPACE_V2_CSS',
    'from mrp_workspace import workspace_pages, workspace_sidebar, WorkspaceSection, workspace_header, workspace_falta, WORKSPACE_V2_CSS')
for _catalog in ("MRP_COLS","macro_cols"):
    _old = next(l for l in _source.splitlines() if l.lstrip().startswith(f"_opc=[c for c in {_catalog} if"))
    _space = _old[:len(_old)-len(_old.lstrip())]
    _source = _ws_replace(_old, _space+f'_opc=list(dict.fromkeys(("Demanda","Saldo em Estoque","P.C.","S.C.","Produzindo","Falta","Status",*{_catalog})))\n'+_space+'_opc=[c for c in _opc if c not in ("Código","Descrição")]')
_source = _source.replace('("Demanda","Saldo em Estoque","S.C.","P.C.","Status","Semana de Atendimento") if c in _opc]', '("Demanda","Saldo em Estoque","P.C.","S.C.","Produzindo","Falta","Status") if c in _opc]')
# Aplicar o estilo só ao Excel dos relatórios, não às cargas nem aos CSVs.
_source = _ws_replace(
    'def excel_bytes(sheets):',
    'def excel_bytes(sheets, *, layout_relatorio=False):')
_source = _ws_replace(
    '        for name,df in sheets.items(): df.to_excel(writer,sheet_name=name[:31],index=False)\n',
    '        for name,df in sheets.items(): df.to_excel(writer,sheet_name=name[:31],index=False)\n'
    '        if layout_relatorio:\n'
    '            from mrp_relatorio_excel import estilizar_relatorios_mrp\n'
    '            estilizar_relatorios_mrp(writer.book)\n')
for _line in _source.splitlines():
    if 'excel_bytes(s)' in _line and ('"MRP_Consulta.xlsx"' in _line or '"MRP_Relatorios_Completos.xlsx"' in _line):
        _source = _ws_replace(_line, _line.replace('excel_bytes(s)', 'excel_bytes(s, layout_relatorio=True)'))
"""
