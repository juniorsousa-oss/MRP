COMPARATIVO_PATCH = r"""
# =========================================================
# COMPARATIVO MRP — ABA EXCLUSIVA E EXECUÇÃO SOB DEMANDA
# =========================================================

# Botões de formulários operacionais no padrão preto do app.
_black_form_anchor = '_apply_visual_theme(UI_CONFIG)\n'
_black_form_replacement = '_apply_visual_theme(UI_CONFIG)\nst.markdown(\'<style>div[data-testid="stFormSubmitButton"] button{background:#050505 !important;border-color:#050505 !important;color:#ffffff !important;}div[data-testid="stFormSubmitButton"] button:hover{background:#171717 !important;border-color:#171717 !important;color:#ffffff !important;}</style>\', unsafe_allow_html=True)\n'
if _black_form_anchor not in _source:
    raise RuntimeError("Ponto do tema visual não encontrado para padronizar botões pretos.")
_source = _source.replace(_black_form_anchor, _black_form_replacement, 1)

# O comparativo só carrega snapshots e calcula resultados após o clique.
_compare_pattern = r"def render_mrp_history\(\):\n.*?\ndef render_consulta_view\(\):"
_compare_replacement = '''def render_mrp_history():
    st.subheader("COMPARATIVO MRP")
    if UI_CONFIG.get("section_history_description"):
        st.caption(UI_CONFIG["section_history_description"])
    try:
        history=load_snapshot_history()
    except Exception as e:
        st.warning(f"Não foi possível acessar o histórico compartilhado: {e}")
        return
    if not history:
        st.info("Ainda não existem MRP salvos no histórico.")
        return
    if len(history)<2:
        st.info("Salve pelo menos dois MRP para gerar um comparativo.")
        return

    labels={int(x["id"]):f"MRP {x['id']} | semana {x.get('semana_mrp') or '-'} | {formatar_data_br(x.get('created_at'))} | {x.get('usuario') or '-'}" for x in history}
    ids=list(labels)

    with st.form("mrp_comparativo_form", border=False):
        c1,c2=st.columns(2)
        new_id=c1.selectbox(UI_CONFIG["history_current_label"],ids,index=0,format_func=lambda x:labels[x],key="mrp_history_current_form")
        old_id=c2.selectbox(UI_CONFIG["history_previous_label"],ids,index=1 if len(ids)>1 else 0,format_func=lambda x:labels[x],key="mrp_history_previous_form")
        comparar=st.form_submit_button("INICIAR COMPARAÇÃO",use_container_width=True,type="primary")

    if not comparar:
        st.caption("Selecione os dois MRP e clique em INICIAR COMPARAÇÃO para gerar o comparativo.")
        return
    if new_id==old_id:
        st.warning("Selecione dois MRP diferentes para realizar a comparação.")
        return

    try:
        with st.spinner("Gerando comparativo MRP..."):
            old=load_snapshot(old_id)
            new=load_snapshot(new_id)
            cmp=compare_mrp_general(old,new)
            classes=cmp["Classificação"] if "Classificação" in cmp.columns else pd.Series(dtype=str)
            k1,k2,k3,k4,k5=st.columns(5)
            k1.metric("Novo",int((classes=="NOVO").sum()))
            k2.metric("Removido",int((classes=="REMOVIDO").sum()))
            k3.metric("Alterado",int((classes=="ALTERADO").sum()))
            k4.metric("Novo S.C.",int((classes=="NOVO S.C.").sum()))
            k5.metric("Normalizado",int((classes=="NORMALIZADO").sum()))
            st.dataframe(cmp,use_container_width=True,hide_index=True)

            proj_cmp=compare_simple(snapshot_df(old,"projecao_semanal"),snapshot_df(new,"projecao_semanal"),["Código","Semana"])
            dem_cmp=compare_simple(snapshot_df(old,"demanda_projeto"),snapshot_df(new,"demanda_projeto"),["Projeto","Produto","Semana de Necessidade"])
            comp_old=snapshot_df(old,"compra_mrp")
            comp_new=snapshot_df(new,"compra_mrp")
            comp_cmp=compare_simple(comp_old,comp_new,["produto","op"])
            report={
                "MRP_Geral_Comparativo":cmp,
                "Projecao_Comparativo":proj_cmp,
                "Demanda_Projeto_Comparativo":dem_cmp,
                "Compras_Comparativo":comp_cmp,
                "MRP_Anterior":snapshot_df(old,"mrp_geral"),
                "MRP_Atual":snapshot_df(new,"mrp_geral"),
                "Compra_Anterior":comp_old,
                "Compra_Atual":comp_new,
            }
            st.download_button("BAIXAR RELATÓRIO COMPARATIVO",excel_bytes(report),"Comparativo_MRP.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="download_comparativo_mrp")
    except Exception as e:
        st.error(f"Erro ao gerar o comparativo: {e}")

def render_consulta_view():'''
_sub_once(_compare_pattern, _compare_replacement, "comparativo MRP sob demanda", flags=re.S)

# CONSULTA / ÚLTIMO MRP: adiciona aba exclusiva para ADMIN.
_old_consulta_tabs = '    tab_geral, tab_projeto, tab_tratativa = st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])'
_new_consulta_tabs = '''    if st.session_state.get("auth_role") == "ADMIN":
        tab_geral, tab_projeto, tab_tratativa, tab_comparativo = st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS", "COMPARATIVO MRP"])
    else:
        tab_geral, tab_projeto, tab_tratativa = st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])
        tab_comparativo = None'''
if _old_consulta_tabs not in _source:
    raise RuntimeError("Abas da consulta não encontradas para incluir Comparativo MRP.")
_source = _source.replace(_old_consulta_tabs, _new_consulta_tabs, 1)

_old_consulta_tratativa = '''    with tab_tratativa:
        render_tratativa_projetos()

    st.markdown("### Exportação de relatórios")'''
_new_consulta_tratativa = '''    with tab_tratativa:
        render_tratativa_projetos()

    if tab_comparativo is not None:
        with tab_comparativo:
            render_mrp_history()

    st.markdown("### Exportação de relatórios")'''
if _old_consulta_tratativa not in _source:
    raise RuntimeError("Bloco da Tratativa na consulta não encontrado para posicionar Comparativo MRP.")
_source = _source.replace(_old_consulta_tratativa, _new_consulta_tratativa, 1)

# Remove o comparativo antigo exibido abaixo da consulta.
_old_latest_history = '''            render_consulta_view()
            if st.session_state.get("auth_role") == "ADMIN":
                render_mrp_history()'''
_new_latest_history = '''            render_consulta_view()'''
if _old_latest_history not in _source:
    raise RuntimeError("Comparativo antigo abaixo da consulta não encontrado.")
_source = _source.replace(_old_latest_history, _new_latest_history, 1)

# PROCESSAMENTO ADMIN: quarta aba exclusiva.
_old_admin_tabs = 'tab1,tab2,tab3=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])'
_new_admin_tabs = 'tab1,tab2,tab3,tab4=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS", "COMPARATIVO MRP"])'
if _old_admin_tabs not in _source:
    raise RuntimeError("Abas do processamento não encontradas para incluir Comparativo MRP.")
_source = _source.replace(_old_admin_tabs, _new_admin_tabs, 1)

_old_admin_tratativa = '''with tab3:
    render_tratativa_projetos()
st.divider(); st.subheader(UI_CONFIG["section_export_title"])'''
_new_admin_tratativa = '''with tab3:
    render_tratativa_projetos()
with tab4:
    render_mrp_history()
st.divider(); st.subheader(UI_CONFIG["section_export_title"])'''
if _old_admin_tratativa not in _source:
    raise RuntimeError("Bloco da Tratativa no processamento não encontrado para posicionar Comparativo MRP.")
_source = _source.replace(_old_admin_tratativa, _new_admin_tratativa, 1)

# Remove o comparativo antigo do rodapé do processamento.
_old_footer_history = '''st.divider()
if st.session_state.get("auth_role") == "ADMIN":
    render_mrp_history()'''
_new_footer_history = '''st.divider()'''
if _old_footer_history not in _source:
    raise RuntimeError("Comparativo antigo do rodapé não encontrado.")
_source = _source.replace(_old_footer_history, _new_footer_history, 1)
"""
