MRP_PADRAO_FINAL_PATCH = r'''
# =========================================================
# PADRÃO FINAL SETTA — CABEÇALHO + FILTROS
# Aplicado por último para não ser sobrescrito por patches antigos.
# =========================================================

# 1) Cabeçalho superior: usa EXATAMENTE o mesmo componente do Conversor MRP.
_old_brand_call = '_render_brand_header(UI_CONFIG)\n'
if _source.count(_old_brand_call) != 1:
    raise RuntimeError("Renderização antiga do cabeçalho do MRP não encontrada.")
_source = _source.replace(_old_brand_call, '', 1)

_header_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_header_css = """
<style>
/* Fundo principal sólido: remove qualquer degradê herdado de temas/patches anteriores. */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"],
.stMain{
  background:#F4F7FB!important;
  background-image:none!important;
}
.block-container{
  max-width:1780px!important;
  padding-top:3.2rem!important;
  padding-left:2.7rem!important;
  padding-right:2.7rem!important;
  padding-bottom:3rem!important;
  width:100%!important;
}
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] .main,
[data-testid="stMain"],
.stMain{
  width:100%!important;
  max-width:100%!important;
  margin-left:0!important;
  margin-right:0!important;
}
[data-testid="stAppViewContainer"] .main .block-container,
[data-testid="stMain"] .block-container,
.stMain .block-container{
  width:100%!important;
  max-width:100%!important;
  margin-left:0!important;
  margin-right:0!important;
}
.setta-logo-card{
  width:100%!important;
  min-height:128px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  background:#fff!important;
  border:1px solid #e5e8ee!important;
  border-radius:16px!important;
  box-shadow:0 4px 14px rgba(24,39,75,.08)!important;
  box-sizing:border-box!important;
  margin:0 0 2.55rem 0!important;
  padding:1.1rem 2rem!important;
}
.setta-logo-card img{
  display:block!important;
  width:auto!important;
  height:auto!important;
  max-width:205px!important;
  max-height:86px!important;
  object-fit:contain!important;
}
.app-title{
  margin:0!important;
  padding:0!important;
  font-size:2.55rem!important;
  line-height:1.08!important;
  font-weight:800!important;
  letter-spacing:-.04em!important;
  color:#050505!important;
}
.app-subtitle,.app-sub{
  margin-top:.72rem!important;
  margin-bottom:1.65rem!important;
  color:#4f5661!important;
  font-size:.94rem!important;
  line-height:1.35!important;
  text-transform:uppercase!important;
}
div[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] p{
  text-transform:uppercase!important;
  font-weight:800!important;
}
@media(max-width:900px){
  .block-container{
    padding-top:2rem!important;
    padding-left:1rem!important;
    padding-right:1rem!important;
    padding-bottom:2rem!important;
  }
  .setta-logo-card{
    min-height:105px!important;
    margin-bottom:1.8rem!important;
    padding:.9rem 1rem!important;
  }
  .setta-logo-card img{
    max-width:170px!important;
    max-height:72px!important;
  }
  .app-title{font-size:2rem!important}
}
</style>
"""
if _source.count(_header_anchor) != 1:
    raise RuntimeError("Título principal do MRP não encontrado para o padrão final do cabeçalho.")
_header_render = """_mrp_logo_src = str(UI_CONFIG.get("logo_data") or "")
if _mrp_logo_src:
    _mrp_logo_html = f'<img src="{_mrp_logo_src}" alt="SETTA">'
else:
    _mrp_logo_html = '<div style="font-size:2rem;font-weight:800;color:#202124">SETTA</div>'
st.markdown(
    _header_css + f'<div class="setta-logo-card">{_mrp_logo_html}</div>',
    unsafe_allow_html=True,
)
"""
_source = _source.replace(
    _header_anchor,
    _header_render + _header_anchor,
    1,
)

# Normaliza códigos de material digitados com menos de 8 posições.
_codigo_helper_anchor = 'def render_consulta_view():\n'
_codigo_helper_impl = """def _normalizar_busca_codigo_8(chave):
    valor = str(st.session_state.get(chave) or "").strip()
    if re.fullmatch(r"\\d{1,7}", valor):
        st.session_state[chave] = valor.zfill(8)

"""
if _source.count(_codigo_helper_anchor) != 1:
    raise RuntimeError("Ponto de inclusão da normalização de código não encontrado.")
_source = _source.replace(_codigo_helper_anchor, _codigo_helper_impl + _codigo_helper_anchor, 1)

# 2) CONSULTA — Demanda Geral:
# busca livre digitável + STATUS e TIPO por alternativa única.
_old = """        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3, c4 = st.columns(4)
            codigo = c1.selectbox("Código", ["Todos"] + cods, key="consulta_codigo")
            descricao = c2.selectbox("Descrição", ["Todos"] + descricoes, key="consulta_descricao")
            tipo = c3.selectbox("Tipo", ["Todos"] + tipos, key="consulta_tipo")
            status = c4.selectbox("Status", ["Todos"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_codigo","consulta_descricao","consulta_tipo","consulta_status"))"""
_new = """        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3 = st.columns(3)
            busca_consulta = c1.text_input("CÓDIGO / DESCRIÇÃO", key="consulta_busca_geral", placeholder="DIGITE O CÓDIGO OU PARTE DA DESCRIÇÃO")
            status = c2.selectbox("STATUS", ["TODOS"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            tipo = c3.selectbox("TIPO", ["TODOS"] + tipos, key="consulta_tipo")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary", on_click=_normalizar_busca_codigo_8, args=("consulta_busca_geral",))
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_busca_geral","consulta_tipo","consulta_status"))"""
if _source.count(_old) != 1:
    raise RuntimeError("Filtro final da Consulta Geral não encontrado.")
_source = _source.replace(_old, _new, 1)

_old_logic = """        f = mg.copy()
        if codigo != "Todos": f = f[f["Código"].astype(str) == codigo]
        if descricao != "Todos": f = f[f["Descrição"].astype(str) == descricao]
        if tipo != "Todos": f = f[f["Tipo"].astype(str) == tipo]
        if status != "Todos": f = f[f["Status"].astype(str) == status]"""
_new_logic = """        f = mg.copy()
        if busca_consulta:
            _bc = busca_consulta.strip()
            _codigo_txt = (
                f["Código"].fillna("").astype(str).str.strip()
                .str.replace(r"\\.0$", "", regex=True)
            )
            # Código numérico = padroniza para 8 posições e compara EXATO.
            # Ex.: 50646 -> 00050646.
            if re.fullmatch(r"\\d+", _bc):
                _alvo_codigo = _bc.zfill(8) if len(_bc) < 8 else _bc
                _codigo_norm = _codigo_txt.str.zfill(8)
                f = f[_codigo_norm.eq(_alvo_codigo)]
            else:
                # Texto = pesquisa literal (não regex) por código ou descrição.
                f = f[
                    _codigo_txt.str.contains(_bc, case=False, na=False, regex=False)
                    | f["Descrição"].fillna("").astype(str).str.contains(
                        _bc, case=False, na=False, regex=False
                    )
                ]
        if tipo != "TODOS": f = f[f["Tipo"].astype(str) == tipo]
        if status != "TODOS": f = f[f["Status"].astype(str) == status]
        f = f.reset_index(drop=True)"""
if _source.count(_old_logic) != 1:
    raise RuntimeError("Lógica final da Consulta Geral não encontrada.")
_source = _source.replace(_old_logic, _new_logic, 1)

# 3) CONSULTA — Demanda por Projeto:
# pesquisa digitável + semana por alternativa única.
_old = """        with st.form("consulta_projeto_filtros", border=False):
            c1, c2, c3 = st.columns(3)
            projeto = c1.selectbox("Projeto", ["Todos"] + projetos, key="consulta_projeto")
            produto = c2.selectbox("Produto", ["Todos"] + produtos, key="consulta_produto")
            semana = c3.selectbox("Semana de Necessidade", ["Todas"] + semanas, key="consulta_semana")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_projeto","consulta_produto","consulta_semana"))"""
_new = """        with st.form("consulta_projeto_filtros", border=False):
            c1, c2 = st.columns(2)
            busca_projeto_consulta = c1.text_input("PROJETO / PRODUTO", key="consulta_busca_projeto", placeholder="DIGITE O PROJETO OU PRODUTO")
            semana = c2.selectbox("SEMANA DE NECESSIDADE", ["TODAS"] + semanas, key="consulta_semana")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_busca_projeto","consulta_semana"))"""
if _source.count(_old) != 1:
    raise RuntimeError("Filtro final da Consulta por Projeto não encontrado.")
_source = _source.replace(_old, _new, 1)

_old_logic = """        f = dem.copy()
        if projeto != "Todos": f = f[f["Projeto"].astype(str) == projeto]
        if produto != "Todos": f = f[f["Produto"].astype(str) == produto]
        if semana != "Todas": f = f[f["Semana de Necessidade"].astype(str) == semana]"""
_new_logic = """        f = dem.copy()
        if busca_projeto_consulta:
            _bp = busca_projeto_consulta.strip()
            f = f[
                f["Projeto"].astype(str).str.contains(_bp, case=False, na=False)
                | f["Produto"].astype(str).str.contains(_bp, case=False, na=False)
            ]
        if semana != "TODAS": f = f[f["Semana de Necessidade"].astype(str) == semana]"""
if _source.count(_old_logic) != 1:
    raise RuntimeError("Lógica final da Consulta por Projeto não encontrada.")
_source = _source.replace(_old_logic, _new_logic, 1)

# 4) ADMIN — Demanda Geral:
# remove multiselect/chips e usa selectbox de alternativa única.
_old = """    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3=st.columns(3)
        with c1: busca=st.text_input("Código / descrição", key="admin_busca_geral")
        with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."], key="admin_status_geral")
        with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipos_geral")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_geral","admin_status_geral","admin_tipos_geral"))"""
_new = """    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3=st.columns(3)
        with c1: busca=st.text_input("CÓDIGO / DESCRIÇÃO", key="admin_busca_geral", placeholder="DIGITE O CÓDIGO OU PARTE DA DESCRIÇÃO")
        with c2: status=st.selectbox("STATUS",["TODOS","OK","CRIAR S.C."], key="admin_status_geral")
        with c3: tipo_filtro=st.selectbox("TIPO",["TODOS"]+sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipo_geral")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary", on_click=_normalizar_busca_codigo_8, args=("admin_busca_geral",))
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_geral","admin_status_geral","admin_tipo_geral"))"""
if _source.count(_old) != 1:
    raise RuntimeError("Filtro final ADMIN da Demanda Geral não encontrado.")
_source = _source.replace(_old, _new, 1)

_old_logic = """    if status: v=v[v["Status"].isin(status)]
    if tipos: v=v[v["Tipo"].isin(tipos)]"""
_new_logic = """    if status != "TODOS": v=v[v["Status"].astype(str).eq(status)]
    if tipo_filtro != "TODOS": v=v[v["Tipo"].astype(str).eq(tipo_filtro)]"""
if _source.count(_old_logic) != 1:
    raise RuntimeError("Lógica final ADMIN da Demanda Geral não encontrada.")
_source = _source.replace(_old_logic, _new_logic, 1)

# Pesquisa ADMIN — código numérico exato; descrição permanece pesquisa literal parcial.
_old_admin_search = """    if busca:
        b=busca.strip(); v=v[v["Código"].astype(str).str.contains(b,na=False)|v["Descrição"].str.contains(b,case=False,na=False)]"""
_new_admin_search = """    if busca:
        b=busca.strip()
        _admin_codigo_txt = (
            v["Código"].fillna("").astype(str).str.strip()
            .str.replace(r"\\.0$", "", regex=True)
        )
        if re.fullmatch(r"\\d+", b):
            _admin_alvo = b.zfill(8) if len(b) < 8 else b
            _admin_codigo_norm = _admin_codigo_txt.str.zfill(8)
            v = v[_admin_codigo_norm.eq(_admin_alvo)]
        else:
            v = v[
                _admin_codigo_txt.str.contains(b, case=False, na=False, regex=False)
                | v["Descrição"].fillna("").astype(str).str.contains(
                    b, case=False, na=False, regex=False
                )
            ]
        v = v.reset_index(drop=True)"""
if _source.count(_old_admin_search) != 1:
    raise RuntimeError("Pesquisa ADMIN da Demanda Geral não encontrada.")
_source = _source.replace(_old_admin_search, _new_admin_search, 1)

# 5) ADMIN — Demanda por Projeto:
# pesquisa livre + semana única.
_old = """    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2=st.columns(2)
        with c1: busca2=st.text_input("Código / projeto", key="admin_busca_projeto")
        with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else [], key="admin_semana_projeto")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_projeto","admin_semana_projeto"))"""
_new = """    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2=st.columns(2)
        with c1: busca2=st.text_input("CÓDIGO / PROJETO", key="admin_busca_projeto", placeholder="DIGITE O CÓDIGO OU PROJETO")
        with c2: semana_filtro=st.selectbox("SEMANA",["TODAS"]+sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else ["TODAS"], key="admin_semana_projeto")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_projeto","admin_semana_projeto"))"""
if _source.count(_old) != 1:
    raise RuntimeError("Filtro final ADMIN da Demanda por Projeto não encontrado.")
_source = _source.replace(_old, _new, 1)

_old_logic = '    if semana_filtro: d=d[d["Semana de Necessidade"].isin(semana_filtro)]'
_new_logic = '    if semana_filtro != "TODAS": d=d[d["Semana de Necessidade"] == semana_filtro]'
if _source.count(_old_logic) != 1:
    raise RuntimeError("Lógica final ADMIN da Demanda por Projeto não encontrada.")
_source = _source.replace(_old_logic, _new_logic, 1)
'''
