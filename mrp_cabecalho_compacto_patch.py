"""Aplica o cabeçalho ao shell depois dos patches de layout existentes."""

CABECALHO_COMPACTO_PATCH = r"""
def _header_compact_replace(old,new):
    global _source
    if _source.count(old)!=1:
        raise RuntimeError("MRP: âncora do cabeçalho compacto não encontrada: "+old)
    _source=_source.replace(old,new,1)


_old_logo='''st.markdown(
    _header_css + f'<div class="setta-logo-card">{_mrp_logo_html}</div>',
    unsafe_allow_html=True,
)'''
_header_compact_replace(_old_logo,'st.html(_header_css)')
_old_title='''st.markdown(f'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>', unsafe_allow_html=True)
if UI_CONFIG.get("section_main_description"):
    st.markdown(f'<p class="app-subtitle">{UI_CONFIG["section_main_description"]}</p>', unsafe_allow_html=True)'''
_header_compact_replace(_old_title,'')
_status_anchor='with st.sidebar:'
_header_compact_replace(_status_anchor,'''from mrp_interface_visual import WORKSPACE_CSS,cabecalho_html
st.html(WORKSPACE_CSS)
st.html(cabecalho_html(
    _mrp_page,UI_CONFIG.get("logo_data"),_mrp_status,_mrp_when,
    semana=_mrp_sidebar_week,bases=(_mrp_base_ok,_mrp_base_total),
    registros=_mrp_rows_text,alertas=_mrp_alertas,
))
''' + _status_anchor)
_login_anchor='    with st.form("login_form", clear_on_submit=False):'
_header_compact_replace(_login_anchor,'''    from mrp_interface_visual import LOGIN_COMPACTO_CSS
    st.html(LOGIN_COMPACTO_CSS)
''' + _login_anchor)

# O acesso à compra é a ação principal; os formatos existentes ficam em
# um grupo à parte. Os callbacks e geradores mantêm a implementação original.
_visual_cons_ini=_source.index('    c1, c2, c3, c4 = st.columns(4)\n    c1.download_button("BAIXAR TODOS — EXCEL"')
_visual_cons_fim=_source.index('    if st.session_state.get("consulta_compra_aberta",False):',_visual_cons_ini)
_visual_cons_linhas=_source[_visual_cons_ini:_visual_cons_fim].splitlines()
assert len(_visual_cons_linhas)==6 and 'c4.button("ANÁLISE DE COMPRA"' in _visual_cons_linhas[4]
_visual_cons_btn=_visual_cons_linhas[4].replace("c4.button", "st.button", 1)
_source=_source[:_visual_cons_ini]+"\n".join([
    _visual_cons_btn,_visual_cons_linhas[5],
    '    with st.expander("Exportar resultados do MRP"):',
    '        c1, c2, c3 = st.columns(3)',
    *["    "+linha for linha in _visual_cons_linhas[1:4]],
])+"\n"+_source[_visual_cons_fim:]

_visual_admin_ini=_source.index('b1,b2,b3,b4=st.columns(4)\nwith b1: st.download_button("BAIXAR TODOS — EXCEL"')
_visual_admin_fim=_source.index('if st.session_state.get("admin_compra_aberta",False):',_visual_admin_ini)
_visual_admin_linhas=_source[_visual_admin_ini:_visual_admin_fim].splitlines()
assert len(_visual_admin_linhas)==7 and _visual_admin_linhas[4]=="with b4:"
_source=_source[:_visual_admin_ini]+"\n".join([
    *[linha[4:] for linha in _visual_admin_linhas[5:7]],
    'with st.expander("Exportar resultados do MRP"):',
    '    b1,b2,b3=st.columns(3)',
    *["    "+linha for linha in _visual_admin_linhas[1:4]],
])+"\n"+_source[_visual_admin_fim:]

"""
