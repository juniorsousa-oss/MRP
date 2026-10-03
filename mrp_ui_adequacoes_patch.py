UI_ADEQUACOES_PATCH = r"""
# =========================================================
# ADEQUAÇÕES DE INTERFACE — FILTROS, TRATATIVAS E SIDEBAR
# =========================================================

def _limpar_filtros_mrp(*keys):
    for key in keys:
        st.session_state.pop(key, None)

# CONSULTA — DEMANDA GERAL: adiciona botão LIMPAR ao lado da pesquisa.
_old = '''        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3, c4 = st.columns(4)
            codigo = c1.selectbox("Código", ["Todos"] + cods, key="consulta_codigo")
            descricao = c2.selectbox("Descrição", ["Todos"] + descricoes, key="consulta_descricao")
            tipo = c3.selectbox("Tipo", ["Todos"] + tipos, key="consulta_tipo")
            status = c4.selectbox("Status", ["Todos"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")'''
_new = '''        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3, c4 = st.columns(4)
            codigo = c1.selectbox("Código", ["Todos"] + cods, key="consulta_codigo")
            descricao = c2.selectbox("Descrição", ["Todos"] + descricoes, key="consulta_descricao")
            tipo = c3.selectbox("Tipo", ["Todos"] + tipos, key="consulta_tipo")
            status = c4.selectbox("Status", ["Todos"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_codigo","consulta_descricao","consulta_tipo","consulta_status"))'''
if _old not in _source:
    raise RuntimeError("Formulário da Consulta Geral não encontrado para botão Limpar.")
_source = _source.replace(_old, _new, 1)

# CONSULTA — DEMANDA POR PROJETO.
_old = '''        with st.form("consulta_projeto_filtros", border=False):
            c1, c2, c3 = st.columns(3)
            projeto = c1.selectbox("Projeto", ["Todos"] + projetos, key="consulta_projeto")
            produto = c2.selectbox("Produto", ["Todos"] + produtos, key="consulta_produto")
            semana = c3.selectbox("Semana de Necessidade", ["Todas"] + semanas, key="consulta_semana")
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")'''
_new = '''        with st.form("consulta_projeto_filtros", border=False):
            c1, c2, c3 = st.columns(3)
            projeto = c1.selectbox("Projeto", ["Todos"] + projetos, key="consulta_projeto")
            produto = c2.selectbox("Produto", ["Todos"] + produtos, key="consulta_produto")
            semana = c3.selectbox("Semana de Necessidade", ["Todas"] + semanas, key="consulta_semana")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_projeto","consulta_produto","consulta_semana"))'''
if _old not in _source:
    raise RuntimeError("Formulário da Demanda por Projeto na consulta não encontrado para botão Limpar.")
_source = _source.replace(_old, _new, 1)

# ADMIN — DEMANDA GERAL.
_old = '''    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3=st.columns(3)
        with c1: busca=st.text_input("Código / descrição", key="admin_busca_geral")
        with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."], key="admin_status_geral")
        with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipos_geral")
        st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")'''
_new = '''    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3=st.columns(3)
        with c1: busca=st.text_input("Código / descrição", key="admin_busca_geral")
        with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."], key="admin_status_geral")
        with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipos_geral")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_geral","admin_status_geral","admin_tipos_geral"))'''
if _old not in _source:
    raise RuntimeError("Formulário da Demanda Geral ADMIN não encontrado para botão Limpar.")
_source = _source.replace(_old, _new, 1)

# ADMIN — DEMANDA POR PROJETO.
_old = '''    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2=st.columns(2)
        with c1: busca2=st.text_input("Código / projeto", key="admin_busca_projeto")
        with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else [], key="admin_semana_projeto")
        st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")'''
_new = '''    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2=st.columns(2)
        with c1: busca2=st.text_input("Código / projeto", key="admin_busca_projeto")
        with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else [], key="admin_semana_projeto")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_projeto","admin_semana_projeto"))'''
if _old not in _source:
    raise RuntimeError("Formulário da Demanda por Projeto ADMIN não encontrado para botão Limpar.")
_source = _source.replace(_old, _new, 1)

# TRATATIVA DE PROJETOS — filtros com confirmação e limpeza.
_old = '''    if salvas.empty:
        st.info("Nenhuma tratativa de projeto está salva no momento.")
    else:
        st.markdown("**Tratativas salvas**")
        st.dataframe(salvas,use_container_width=True,hide_index=True)
        st.caption("Para alterar uma observação, envie novamente o mesmo projeto com a nova OBS. Para remover, envie o projeto com a OBS em branco.")'''
_new = '''    if salvas.empty:
        st.info("Nenhuma tratativa de projeto está salva no momento.")
    else:
        st.markdown("**Tratativas salvas**")
        atualizadores=sorted([x for x in salvas["Atualizado por"].fillna("").astype(str).unique().tolist() if x])
        with st.form("tratativa_projetos_filtros", border=False):
            c1,c2,c3=st.columns(3)
            projeto_filtro=c1.text_input("Projeto", key="trat_filtro_projeto", placeholder="Digite o projeto")
            obs_filtro=c2.text_input("OBS / Tratativa", key="trat_filtro_obs", placeholder="Ex.: RESÍDUO")
            atualizado_filtro=c3.selectbox("Atualizado por", ["Todos"]+atualizadores, key="trat_filtro_atualizado")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("trat_filtro_projeto","trat_filtro_obs","trat_filtro_atualizado"))

        filtradas=salvas.copy()
        if projeto_filtro:
            _pf=projeto_filtro.strip()
            filtradas=filtradas[filtradas["Projeto"].astype(str).str.contains(_pf,case=False,na=False)]
        if obs_filtro:
            _of=obs_filtro.strip()
            filtradas=filtradas[filtradas["OBS"].astype(str).str.contains(_of,case=False,na=False)]
        if atualizado_filtro!="Todos":
            filtradas=filtradas[filtradas["Atualizado por"].astype(str).eq(atualizado_filtro)]

        st.dataframe(filtradas,use_container_width=True,hide_index=True)
        st.caption(f"{len(filtradas)} de {len(salvas)} tratativa(s) exibida(s). Para alterar uma observação, envie novamente o mesmo projeto com a nova OBS. Para remover, envie o projeto com a OBS em branco.")'''
if _old not in _source:
    raise RuntimeError("Tabela da Tratativa de Projetos não encontrada para inclusão dos filtros.")
_source = _source.replace(_old, _new, 1)

# Remove o aviso azul do conteúdo principal; a orientação já fica no menu lateral.
_old_notice = '''if UI_CONFIG.get("main_notice"):
    st.markdown(f'<div class="app-info">{UI_CONFIG["main_notice"]}</div>', unsafe_allow_html=True)'''
if _old_notice in _source:
    _source = _source.replace(_old_notice, '', 1)

# CSS interno: apenas o botão LIMPAR. A sidebar é propriedade do shell SETTA.
_ui_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_ui_css_html = '''<style>
div[data-testid="stFormSubmitButton"] button[kind="secondary"] {
    background:#ffffff !important;
    border:1px solid #cfd4dc !important;
    color:#252a31 !important;
    font-weight:600 !important;
}
div[data-testid="stFormSubmitButton"] button[kind="secondary"]:hover {
    background:#f4f5f7 !important;
    border-color:#aeb5bf !important;
    color:#111111 !important;
}
</style>'''
_ui_css = 'st.markdown(' + repr(_ui_css_html) + ', unsafe_allow_html=True)\n'
if _ui_anchor not in _source:
    raise RuntimeError("Ponto principal do layout não encontrado para CSS das adequações.")
_source = _source.replace(_ui_anchor, _ui_css + _ui_anchor, 1)
"""
