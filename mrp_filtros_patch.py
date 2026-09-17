FILTROS_PATCH = r'''
# =========================================================
# FILTROS COM CONFIRMAÇÃO — EVITA RERUN A CADA SELEÇÃO
# =========================================================

# CONSULTA — DEMANDA GERAL
_old_consulta_geral = '''        c1, c2, c3, c4 = st.columns(4)
        cods = sorted(mg["Código"].dropna().astype(str).unique().tolist())
        codigo = c1.selectbox("Código", ["Todos"] + cods, key="consulta_codigo")
        descricoes = sorted(mg["Descrição"].fillna("").astype(str).unique().tolist())
        descricao = c2.selectbox("Descrição", ["Todos"] + descricoes, key="consulta_descricao")
        tipos = sorted(mg["Tipo"].fillna("").astype(str).unique().tolist())
        tipo = c3.selectbox("Tipo", ["Todos"] + tipos, key="consulta_tipo")
        status = c4.selectbox("Status", ["Todos"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
'''
_new_consulta_geral = '''        cods = sorted(mg["Código"].dropna().astype(str).unique().tolist())
        descricoes = sorted(mg["Descrição"].fillna("").astype(str).unique().tolist())
        tipos = sorted(mg["Tipo"].fillna("").astype(str).unique().tolist())
        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3, c4 = st.columns(4)
            codigo = c1.selectbox("Código", ["Todos"] + cods, key="consulta_codigo")
            descricao = c2.selectbox("Descrição", ["Todos"] + descricoes, key="consulta_descricao")
            tipo = c3.selectbox("Tipo", ["Todos"] + tipos, key="consulta_tipo")
            status = c4.selectbox("Status", ["Todos"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
'''
if _old_consulta_geral not in _source:
    raise RuntimeError("Filtros da Consulta Geral não encontrados para inclusão do botão de pesquisa.")
_source = _source.replace(_old_consulta_geral, _new_consulta_geral, 1)

# CONSULTA — DEMANDA POR PROJETO
_old_consulta_projeto = '''        c1, c2, c3 = st.columns(3)
        projetos = sorted(dem["Projeto"].fillna("").astype(str).unique().tolist())
        produtos = sorted(dem["Produto"].fillna("").astype(str).unique().tolist())
        semanas = sorted([x for x in dem["Semana de Necessidade"].dropna().astype(str).unique().tolist() if x])
        projeto = c1.selectbox("Projeto", ["Todos"] + projetos, key="consulta_projeto")
        produto = c2.selectbox("Produto", ["Todos"] + produtos, key="consulta_produto")
        semana = c3.selectbox("Semana de Necessidade", ["Todas"] + semanas, key="consulta_semana")
'''
_new_consulta_projeto = '''        projetos = sorted(dem["Projeto"].fillna("").astype(str).unique().tolist())
        produtos = sorted(dem["Produto"].fillna("").astype(str).unique().tolist())
        semanas = sorted([x for x in dem["Semana de Necessidade"].dropna().astype(str).unique().tolist() if x])
        with st.form("consulta_projeto_filtros", border=False):
            c1, c2, c3 = st.columns(3)
            projeto = c1.selectbox("Projeto", ["Todos"] + projetos, key="consulta_projeto")
            produto = c2.selectbox("Produto", ["Todos"] + produtos, key="consulta_produto")
            semana = c3.selectbox("Semana de Necessidade", ["Todas"] + semanas, key="consulta_semana")
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
'''
if _old_consulta_projeto not in _source:
    raise RuntimeError("Filtros da Demanda por Projeto na consulta não encontrados.")
_source = _source.replace(_old_consulta_projeto, _new_consulta_projeto, 1)

# ADMIN / BASES CARREGADAS — DEMANDA GERAL
_old_admin_geral = '''    st.subheader(UI_CONFIG["title_demanda_geral"]); c1,c2,c3=st.columns(3)
    with c1: busca=st.text_input("Código / descrição")
    with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."])
    with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]))
'''
_new_admin_geral = '''    st.subheader(UI_CONFIG["title_demanda_geral"])
    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3=st.columns(3)
        with c1: busca=st.text_input("Código / descrição", key="admin_busca_geral")
        with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."], key="admin_status_geral")
        with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipos_geral")
        st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
'''
if _old_admin_geral not in _source:
    raise RuntimeError("Filtros da Demanda Geral com bases carregadas não encontrados.")
_source = _source.replace(_old_admin_geral, _new_admin_geral, 1)

# ADMIN / BASES CARREGADAS — DEMANDA POR PROJETO
_old_admin_projeto = '''    st.subheader(UI_CONFIG["title_demanda_projeto"]); c1,c2=st.columns(2)
    with c1: busca2=st.text_input("Código / projeto")
    with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else [])
'''
_new_admin_projeto = '''    st.subheader(UI_CONFIG["title_demanda_projeto"])
    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2=st.columns(2)
        with c1: busca2=st.text_input("Código / projeto", key="admin_busca_projeto")
        with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else [], key="admin_semana_projeto")
        st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
'''
if _old_admin_projeto not in _source:
    raise RuntimeError("Filtros da Demanda por Projeto com bases carregadas não encontrados.")
_source = _source.replace(_old_admin_projeto, _new_admin_projeto, 1)
'''
