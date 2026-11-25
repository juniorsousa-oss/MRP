"""Reorganiza a tela MRP atual ao redor da grade, após o shell visual."""
MRP_OPERACAO_PATCH = r'''
import textwrap as _operacao_text

def _op_replace(old, new, label):
    global _source
    if _source.count(old)!=1:
        raise RuntimeError("MRP operação: âncora não encontrada: "+label)
    _source=_source.replace(old,new,1)


_op_replace("from mrp_interface_visual import WORKSPACE_CSS,cabecalho_html", """from mrp_interface_visual import WORKSPACE_CSS,cabecalho_html
from mrp_operacao_ui import OPERACAO_CSS,operacao_indicadores,operacao_busca,operacao_grade,operacao_detalhe,operacao_tabela_detalhe,operacao_rotulo_grade
if _mrp_page=="MRP ATUAL":
    st.html(OPERACAO_CSS)
    st.html('<nav class="mrp-operacao mrp-operacao-brandbar" aria-label="Localização"><strong>SETTA · MRP</strong><span aria-hidden="true">/</span><span>Operações</span><span aria-hidden="true">›</span><strong>MRP atual</strong></nav>')""", "css")
_op_replace('    st.subheader(UI_CONFIG["section_consulta_title"])\n    if UI_CONFIG.get("section_consulta_description"):\n        st.caption(UI_CONFIG["section_consulta_description"])\n', "", "cabeçalho consulta")

_op_replace('            cods = sorted(mg["Código"].dropna().astype(str).unique().tolist())\n            descricoes = sorted(mg["Descrição"].fillna("").astype(str).unique().tolist())\n', "", "listas antigas")
for _prefix in ("consulta","admin"):
    _indent = "    " if _prefix=="consulta" else ""
    _statuses = "_status_dashboard_consulta" if _prefix=="consulta" else "_status_dashboard"
    _data = "dem" if _prefix=="consulta" else "demanda_projeto"
    _callback = "_mrp_consulta_navigate" if _prefix=="consulta" else "_mrp_dashboard_navigate"
    _status_key = "consulta_status_kpi" if _prefix=="consulta" else "admin_status_atendimento"
    _ini = _source.index(_indent+'st.markdown("<style>[class*=st-key-mrp_kpi_]')
    if _prefix=="admin":
        _ini = _source.rindex('st.markdown(\n    \'<div class="section-band"',0,_ini)
    _fim = _source.index("\n",_source.index('"RESÍDUOS, SUSPENSAS E CANCELADAS"',_ini))
    _kpi = f"""\
{_indent}{_statuses}=_mrp_status_atendimento_series({_data})
{_indent}operacao_indicadores({_prefix!r}, [
{_indent}    _mrp_numero_br(t) for t in (len({_data}), *(({_statuses}==c).sum() for c in ("🟢","🟡","🔴","⚪")))
{_indent}], {_callback}, st.session_state.get({_status_key!r}, "TODOS"))
"""
    _source = _source[:_ini]+_kpi.rstrip("\n")+_source[_fim:]

_op_replace("""st.markdown('<div class="topic-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-band"><div class="section-band-kicker">02 · DEMANDA</div><div class="section-band-title">DEMANDA</div></div>', unsafe_allow_html=True)
_mrp_manter_filtros_de_abas(""","""_mrp_manter_filtros_de_abas(""","faixa demanda")

def _op_detalhe_tabs(source, anchors, indent):
    # Recupera os quatro blocos de consulta já existentes, sem reescrever os dados.
    base=_operacao_text.dedent(source)
    pos=[base.index(a) for a in anchors]
    if pos!=sorted(pos):
        raise RuntimeError("MRP operação: ordem dos blocos do detalhe mudou.")
    result=base[:pos[0]]+'_proj_tab,_dem_tab,_cp_tab,_fab_tab=st.tabs(["Projeção","Necessidades","Compras","Produção"])\n'
    tabs = (
        ("_proj_tab", "Nenhuma projeção semanal disponível."),
        ("_dem_tab", "Nenhuma necessidade vinculada."),
        ("_cp_tab", "Nenhuma solicitação ou pedido de compra vinculado."),
        ("_fab_tab", "Nenhuma ordem de produção vinculada."),
    )
    for (tab, empty),a,b in zip(tabs,pos,pos[1:]+[len(base)]):
        block=base[a:b].rstrip()
        if block.count("_setta_dataframe(")!=1:
            raise RuntimeError("MRP operação: tabela do detalhe não localizada: "+tab)
        block=block.replace("_setta_dataframe(", "_mostrou_detalhe = operacao_tabela_detalhe(", 1)
        # A consulta pode vir de uma fotografia antiga com quantidade mas sem OPs
        # discriminadas; nesse caso preserve o aviso específico em vez de duplicá-lo.
        block=block.replace('st.info("Este MRP foi salvo antes', '_mostrou_detalhe = True; st.info("Este MRP foi salvo antes')
        result+="with "+tab+":\n    _mostrou_detalhe = False\n"+_operacao_text.indent(block+"\n","    ")
        result+=f"    if not _mostrou_detalhe: st.caption({empty!r})\n"
    return _operacao_text.indent(result,indent)


for _prefix in ("consulta","admin"):
    _i="    " if _prefix=="consulta" else ""
    _j=_i+"        "
    _tab="tab_geral" if _prefix=="consulta" else "tab1"
    _tabs="(tab_geral,tab_projeto,tab_tratativa,tab_comparativo)" if _prefix=="consulta" else "(tab1,tab2,tab3,tab4)"
    _barra=f"_{_prefix}_operacao_bar"
    _buy=f"_{_prefix}_operacao_compra"
    _actions=f"_{_prefix}_operacao_acoes"
    _page_before=_i+f"if {_tab}.open:"
    # O slot de compra aparece acima das abas apenas quando aberto.
    _tabs_pos = _source.rfind('\n    if st.session_state.get("auth_role") == "ADMIN":\n        tab_geral,',0,_source.index(_page_before)) if _prefix=="consulta" else _source.index('\ntab1,tab2,tab3,tab4=st.tabs(')
    if _tabs_pos<0:
        raise RuntimeError("MRP operação: abas não encontradas.")
    _source=_source[:_tabs_pos]+f'\n{_i}{_buy}=st.empty()'+_source[_tabs_pos:]
    _op_replace(_page_before, f"""{_i}_aba_operacao=next((t for t in {_tabs} if t is not None and t.open),None)
{_i}{_barra}=(_aba_operacao if _aba_operacao is not None else st).container(key="mrp_operacao_bar_{_prefix}")
{_i}with {_barra}:
{_i}    st.html('<span class="mrp-operacao-tools"></span>')
{_i}    _busca_area, _filtro_area, _colunas_area, {_actions} = st.columns([3.8,1.3,1.35,3.55],vertical_alignment='bottom')
{_i}if {_tab}.open:""", f"barra {_prefix}")
    _start=_source.index(_j+f'with st.form("{_prefix}_'+("geral_filtros" if _prefix=="consulta" else "demanda_geral_filtros")+'", border=False):')
    _end=_source.index(_j+("f = mg.copy()" if _prefix=="consulta" else "v=macro.copy()"),_start)
    _cols="MRP_COLS" if _prefix=="consulta" else "macro_cols"
    _term_pos=_source.index(_i+"_mrp_manter_filtros_de_abas(", _source.index("def render_consulta_view") if _prefix=="consulta" else _source.index("# Salva apenas uma vez"))
    # Guarda estado de busca/colunas também quando outra aba é renderizada.
    _search_key="consulta_descricao_busca" if _prefix=="consulta" else "admin_descricao_geral"
    _type_key="consulta_tipo" if _prefix=="consulta" else "admin_tipo_geral"
    _status_widget="consulta_status" if _prefix=="consulta" else "admin_status_geral"
    _code_key="consulta_codigo_busca" if _prefix=="consulta" else "admin_codigo_geral"
    _form = f"""with _busca_area:
    with st.form("{_prefix}_operacao_pesquisa", border=False):
        _b1,_b2=st.columns([3,1],vertical_alignment="bottom")
        termo=_b1.text_input("Buscar por código ou descrição", key={_search_key!r}, label_visibility="collapsed", placeholder="Buscar por código ou descrição")
        _b2.form_submit_button("Buscar", width="stretch")
with _filtro_area:
    with st.popover("Filtros", icon=":material/tune:", width="stretch"):
        with st.form("{_prefix}_operacao_filtros", border=False):
            tipo_operacao=st.selectbox("Tipo", ["TODOS"] + { 'tipos' if _prefix=="consulta" else 'sorted([x for x in cad["Tipo"].unique() if x])'}, key={_type_key!r})
            status=st.selectbox("Status", { '["TODOS"] + sorted(set(mg["Status"].fillna("").astype(str))-{{"TODOS"}})' if _prefix=="consulta" else '["TODOS","OK","CRIAR S.C."]'}, key={_status_widget!r})
            st.form_submit_button("Aplicar filtros", width="stretch")
            st.form_submit_button("Limpar", on_click=_limpar_filtros_mrp, args=({_search_key!r},{_status_widget!r},{_type_key!r},{_code_key!r}), width="stretch")
with _colunas_area:
    with st.popover("Colunas", icon=":material/view_column:", width="stretch"):
        _opc=[c for c in {_cols} if c not in ("Código","Descrição")]
        _extras=st.multiselect("Colunas visíveis", _opc, default=[c for c in ("Demanda","Saldo em Estoque","S.C.","P.C.","Status","Semana de Atendimento") if c in _opc], key="{_prefix}_operacao_colunas", placeholder="Selecione as colunas", format_func=lambda c:"SF" if c=="DIV" else c)
_colunas=["Código","Descrição"]+_extras
"""
    # O formato da expressão do conjunto é gerado literalmente, sem depender da sessão.
    _form=_form.replace('-{{"TODOS"}}','-{"TODOS"}')
    _source=_source[:_start]+_operacao_text.indent(_form,_j)+_source[_end:]
    _source=_source[:_term_pos]+f'{_i}_mrp_manter_filtros_de_abas("{_prefix}_operacao_colunas")\n'+_source[_term_pos:]

    if _prefix=="consulta":
        _a=_source.index(_j+"f = mg.copy()")
        _b=_source.index("                    d_proj = ",_a)
        _des=_source.index("                    desc = f.loc",_b)
        _keep_end=_source.index("\n",_des)
        _labels_start=_source.index("                    st.markdown(f\"### ",_keep_end)
        _keep_start=_source.index("                    st.markdown(f\"**{UI_CONFIG['subsection_projection_title']}",_labels_start)
        _after=_source.index("\n    if tab_projeto.open:",_keep_start)
        _detail=_source[_b:_des]+_source[_keep_start:_after]
        _detail=_op_detalhe_tabs(_detail,(
            'st.markdown(f"**{UI_CONFIG[\'subsection_projection_title\']}', 'st.markdown(f"**{UI_CONFIG[\'subsection_demand_title\']}',
            'd_comp = ', 'd_fab = ',
        ),_j+"        ")
        _fragment=f"""f = operacao_busca(mg,termo,_mrp_codigo_mask)
if tipo_operacao != "TODOS": f=f[f["Tipo"].astype(str).eq(tipo_operacao)]
if status != "TODOS": f=f[f["Status"].astype(str).eq(status)]
f=fix_columns(f.reset_index(drop=True),MRP_COLS)
st.caption(operacao_rotulo_grade(len(f)))
_idx=operacao_grade(_df_exibicao_br(f),_colunas,"consulta_mrp_table")
if _idx is not None:
    _linha=f.iloc[_idx]
    selecionado=str(_linha["Código"])
    def _render_detalhe_consulta():
"""
        _source=_source[:_a]+_operacao_text.indent(_fragment,_j)+_detail.rstrip("\n")+f'\n{_j}    operacao_detalhe("consulta_mrp_table",selecionado,_linha["Descrição"],_df_exibicao_br(f.iloc[[_idx]]).iloc[0],_render_detalhe_consulta)\n'+_source[_after:]
    else:
        _a=_source.index(_j+"v=macro.copy()")
        _b=_source.index("            w=proj[proj",_a)
        _after=_source.index("\nif tab2.open:",_b)
        _detail=_op_detalhe_tabs(_source[_b:_after],("w=proj[","d=demanda_projeto[","compras=cp[","f=fab_det["),_j+"        ")
        _fragment=f"""v=operacao_busca(macro,termo,_mrp_codigo_mask)
if status != "TODOS": v=v[v["Status"].astype(str).eq(status)]
if tipo_operacao != "TODOS": v=v[v["Tipo"].astype(str).eq(tipo_operacao)]
v=v.reset_index(drop=True)
v["_ord_status"]=v["Status"].map({{"CRIAR S.C.":0,"OK":1}}).fillna(2)
v=v.sort_values(["_ord_status","Código"]).drop(columns="_ord_status")
st.caption(operacao_rotulo_grade(len(v)))
_idx=operacao_grade(_df_exibicao_br(v[macro_cols]),_colunas,"demanda_geral_tabela")
if _idx is not None:
    _linha=v.iloc[_idx]
    code=int(_linha["Código"])
    def _render_detalhe_admin():
"""
        _source=_source[:_a]+_operacao_text.indent(_fragment,_j)+_detail.rstrip("\n")+f'\n{_j}    operacao_detalhe("demanda_geral_tabela",str(code).zfill(8),_linha["Descrição"],_df_exibicao_br(v.iloc[[_idx]]).iloc[0],_render_detalhe_admin)\n'+_source[_after:]

    _a=_source.index(_i+f'if st.button("ANÁLISE DE COMPRA",key="{_prefix}_compra_abrir"')
    _b=_source.index(_i+f'if st.session_state.get("{_prefix}_compra_aberta",False):',_a)
    _c=_source.index("\n",_source.index(_i+"    render_validacao_compra_mrp(",_b))
    _original=_source[_a:_b]
    _export_expr=_original.index(_i+'with st.expander("Exportar resultados do MRP"):')
    _exports=_original[_export_expr:].replace('st.expander("Exportar resultados do MRP")','_exp.popover("Exportar", icon=":material/download:", width="stretch")')
    _exports="\n".join(
        linha.replace("with b1: st.", "st.").replace("with b2: st.", "st.").replace("with b3: st.", "st.")
        .replace("c1.download_button", "st.download_button").replace("c2.download_button", "st.download_button")
        .replace("c3.download_button", "st.download_button")
        for linha in _exports.splitlines()
        if " = st.columns(3)" not in linha and "=st.columns(3)" not in linha
    )+"\n"
    _purchase=_source[_b:_c].splitlines()[1].strip()
    _actions_block=f"""{_i}with {_actions}:
{_i}    _exp,_ana=st.columns([1,1.2],vertical_alignment="bottom")
{_i}    _ana.button("ANÁLISE DE COMPRA",key="{_prefix}_compra_abrir",type="primary",width="stretch",on_click=_compra_abrir,args=("{_prefix}",))
"""+_operacao_text.indent(_operacao_text.dedent(_exports)," "* (len(_i)+4))
    _source=_source[:_a]+_actions_block+f"""{_i}if st.session_state.get("{_prefix}_compra_aberta",False):
{_i}    with {_buy}.container():
{_i}        {_purchase}"""+_source[_c:]
_op_replace('    st.markdown("### Exportação de relatórios")\n    sheets = {','    sheets = {',"faixa exportação consulta")
_op_replace("""st.markdown('<div class="topic-divider"></div>', unsafe_allow_html=True); st.markdown('<div class="section-band"><div class="section-band-kicker">03 · RELATÓRIOS</div><div class="section-band-title">RELATÓRIOS</div></div>', unsafe_allow_html=True)
if UI_CONFIG.get("section_export_description"):
    st.caption(UI_CONFIG["section_export_description"])
""","","faixa relatórios")
'''
