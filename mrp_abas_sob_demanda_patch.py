"""Renderiza somente a aba ativa, sem modificar dados, cálculos ou compras."""

ABAS_SOB_DEMANDA_PATCH = r"""
def _abas_substituir(antigo, novo):
    global _source
    if _source.count(antigo) != 1:
        raise RuntimeError("MRP: ponto de abas sob demanda não encontrado: " + antigo)
    _source = _source.replace(antigo, novo, 1)


_abas_manter_estado = '''def _mrp_manter_filtros_de_abas(*chaves):
    # Reatribuir antes de montar os widgets interrompe a limpeza automática
    # do Streamlit nos reruns em que a aba não desenha esses controles.
    for chave in chaves:
        if chave in st.session_state:
            st.session_state[chave] = st.session_state[chave]


'''
_abas_substituir("def render_consulta_view():", _abas_manter_estado + "def render_consulta_view():")

_abas_consulta = '''    _mrp_manter_filtros_de_abas(
        "consulta_codigo_busca", "consulta_descricao_busca", "consulta_tipo", "consulta_status",
        "consulta_projeto_busca", "consulta_produto_busca", "consulta_projeto_descricao",
        "consulta_semana", "consulta_mostrar_residuos",
        "trat_filtro_projeto", "trat_filtro_obs", "trat_filtro_atualizado",
        "mrp_history_current_form", "mrp_history_previous_form",
    )
'''
_abas_consulta_anchor = '    if st.session_state.get("auth_role") == "ADMIN":\n        tab_geral, tab_projeto, tab_tratativa, tab_comparativo = st.tabs('
_abas_substituir(_abas_consulta_anchor, _abas_consulta + _abas_consulta_anchor)
for _aba in ("tab_geral", "tab_projeto", "tab_tratativa"):
    _abas_substituir(f"    with {_aba}:\n", f"    if {_aba}.open:\n" + "__MRP_INDENTAR_ABA__\n" + f"    with {_aba}:\n")
_abas_substituir("    if tab_comparativo is not None:\n        with tab_comparativo:", "    if tab_comparativo is not None and tab_comparativo.open:\n        with tab_comparativo:")

_abas_admin = '''_mrp_manter_filtros_de_abas(
    "admin_codigo_geral", "admin_descricao_geral", "admin_tipo_geral", "admin_status_geral",
    "admin_projeto_busca", "admin_produto_busca", "admin_proj_descricao",
    "admin_semana_projeto", "admin_status_atendimento", "admin_mostrar_residuos",
    "trat_filtro_projeto", "trat_filtro_obs", "trat_filtro_atualizado",
    "mrp_history_current_form", "mrp_history_previous_form",
)
'''
_abas_substituir("tab1,tab2,tab3,tab4=st.tabs(", _abas_admin + "tab1,tab2,tab3,tab4=st.tabs(")
for _aba in ("tab1", "tab2", "tab3", "tab4"):
    _abas_substituir(f"\nwith {_aba}:\n", f"\nif {_aba}.open:\n__MRP_INDENTAR_ABA__\nwith {_aba}:\n")

# Delimitar pelo nível de indentação original. Os exports e o painel de
# compras permanecem fora das abas e continuam sempre acessíveis.
_abas_linhas = _source.splitlines(keepends=True)
_abas_runtime = []
_abas_nivel = None
for _aba_linha in _abas_linhas:
    if _aba_linha == "__MRP_INDENTAR_ABA__\n":
        _abas_nivel = -1
        continue
    if _abas_nivel == -1:
        _abas_nivel = len(_aba_linha) - len(_aba_linha.lstrip(" "))
        _abas_runtime.append("    " + _aba_linha)
        continue
    if _abas_nivel is not None and _aba_linha.strip():
        _linha_nivel = len(_aba_linha) - len(_aba_linha.lstrip(" "))
        if _linha_nivel <= _abas_nivel:
            _abas_nivel = None
        else:
            _aba_linha = "    " + _aba_linha
    _abas_runtime.append(_aba_linha)
_source = "".join(_abas_runtime)
"""
