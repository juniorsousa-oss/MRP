ADEQUACOES_FILTROS_TRATATIVAS_PATCH = r'''
# =========================================================
# ADEQUAÇÕES — FILTROS, RESÍDUOS, KPIs E TRATATIVAS
# Aplicado por último para preservar os demais patches.
# =========================================================

def _final_replace(old, new, label):
    global _source
    if _source.count(old) != 1:
        raise RuntimeError(f"Adequação final não localizada: {label}.")
    _source = _source.replace(old, new, 1)

# ---------------------------------------------------------
# 1) HELPERS — número brasileiro e identificação de resíduos.
# ---------------------------------------------------------
_helper_anchor = "def render_consulta_view():\n"
_helper_impl = """def _mrp_numero_br(valor, max_casas=2):
    try:
        numero=float(valor)
    except (TypeError, ValueError, OverflowError):
        return str(valor)
    if pd.isna(numero):
        return ""
    casas=0 if abs(numero-round(numero))<1e-9 else max_casas
    texto=f"{numero:,.{casas}f}"
    texto=texto.replace(",", "#").replace(".", ",").replace("#", ".")
    if casas:
        texto=texto.rstrip("0").rstrip(",")
    return texto

def _mrp_demanda_nao_apta_mask(df):
    # RESÍDUO, SUSPENSO e CANCELADO não são demandas aptas.
    mask=pd.Series(False,index=df.index,dtype=bool)
    for coluna in ("Ação","Resumo","Condição","OBS Tratativa"):
        if coluna in df.columns:
            serie=df[coluna].fillna("").astype(str).map(_texto_normalizado)
            mask=(
                mask
                | serie.str.contains("RESIDUO",regex=False,na=False)
                | serie.str.contains("SUSPENSO",regex=False,na=False)
                | serie.str.contains("CANCELADO",regex=False,na=False)
            )
    return mask

def _mrp_residuo_mask(df):
    return _mrp_demanda_nao_apta_mask(df)

def _mrp_sinaleiro_semana(semana_necessidade, semana_atendimento):
    # 🟢 atendimento <= necessidade; 🟡 atraso de 1 ou 2 semanas; 🔴 >2 semanas ou sem previsão.
    atendimento_txt=str(semana_atendimento if semana_atendimento is not None else "").strip().upper()
    if atendimento_txt in {"N/A","NA"}:
        return "⚪"
    if atendimento_txt in {"","NN","A DEFINIR","NAN","NONE"}:
        return "🔴"
    try:
        inicio_necessidade=_inicio_semana(semana_necessidade)
        inicio_atendimento=_inicio_semana(semana_atendimento)
        if inicio_necessidade is None or inicio_atendimento is None:
            return "🔴"
        diferenca_semanas=int((inicio_atendimento-inicio_necessidade).days//7)
    except Exception:
        return "🔴"
    if diferenca_semanas<=0:
        return "🟢"
    if diferenca_semanas<=2:
        return "🟡"
    return "🔴"

def _mrp_status_atendimento_series(df):
    if df is None or df.empty:
        return pd.Series(dtype=str,index=getattr(df,"index",None))
    status=df.apply(
        lambda _r:_mrp_sinaleiro_semana(
            _r.get("Semana de Necessidade"),
            _r.get("Semana de Atendimento"),
        ),
        axis=1,
    )
    nao_aptas=_mrp_demanda_nao_apta_mask(df)
    status.loc[nao_aptas]="⚪"
    return status

def _mrp_codigo_mask(serie, valor):
    alvo=str(valor or "").strip()
    if not alvo:
        return pd.Series(True,index=serie.index,dtype=bool)
    codigos=serie.fillna("").astype(str).str.strip().str.replace(r"\\.0$","",regex=True)
    if re.fullmatch(r"\\d+",alvo):
        alvo=alvo.zfill(8) if len(alvo)<8 else alvo
        return codigos.str.zfill(8).eq(alvo)
    return codigos.str.contains(alvo,case=False,na=False,regex=False)

def _mrp_dashboard_navigate(status_key, mostrar_nao_aptas):
    st.session_state["mrp_admin_tabs"]=UI_CONFIG["title_demanda_projeto"]
    st.session_state["admin_status_atendimento"]=status_key
    st.session_state["admin_mostrar_residuos"]=bool(mostrar_nao_aptas)
    for _key in ("admin_projeto_busca","admin_produto_busca","admin_proj_descricao","admin_semana_projeto"):
        st.session_state.pop(_key,None)

def _mrp_dashboard_card(col,titulo,valor,cor,subtitulo,key,status_key,mostrar_nao_aptas=False):
    html=(
        f'<div class="mrp-dashboard-card" style="--mrp-kpi-color:{cor};">'
        f'<div class="mrp-dashboard-card-title">'
        f'<span class="mrp-dashboard-card-dot"></span>{titulo}</div>'
        f'<div class="mrp-dashboard-card-value">{valor}</div>'
        f'<div class="mrp-dashboard-card-subtitle">{subtitulo}</div>'
        '</div>'
    )
    with col:
        with st.container(key=f"mrp_kpi_{key}"):
            st.markdown(html,unsafe_allow_html=True)
            st.button(
                f"ABRIR {titulo}",
                key=f"mrp_kpi_action_{key}",
                use_container_width=True,
                on_click=_mrp_dashboard_navigate,
                args=(status_key,mostrar_nao_aptas),
                help=f"Abrir Demanda por Projeto · {titulo}",
            )

"""
_final_replace(_helper_anchor, _helper_impl + _helper_anchor, "helpers de filtros e números")

# ---------------------------------------------------------
# 1.2) NAVEGAÇÃO DOS KPIs — abre Demanda por Projeto.
# ---------------------------------------------------------
_admin_tabs_options = [
    'tab1,tab2,tab3,tab4=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS", "COMPARATIVO MRP"])',
    'tab1,tab2,tab3=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])',
    'tab1,tab2=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"]])',
]
_admin_tabs_found=[_x for _x in _admin_tabs_options if _x in _source]
if len(_admin_tabs_found)!=1:
    raise RuntimeError("Adequação final não localizada: atalho do dashboard para Demanda por Projeto.")
_admin_tabs_old=_admin_tabs_found[0]
_admin_tabs_new=(
    _admin_tabs_old[:-1]
    +', key="mrp_admin_tabs", on_change="rerun")'
)
_source=_source.replace(_admin_tabs_old,_admin_tabs_new,1)

# ---------------------------------------------------------
# 2) KPIs — ponto para milhar e vírgula para decimal.
# ---------------------------------------------------------
_metric_old = """m=st.columns(5); m[0].metric("Materiais no MRP",f"{len(macro):,}"); m[1].metric("Demanda total",f"{macro['Demanda'].sum():,.0f}"); m[2].metric("P.C.",f"{macro['P.C.'].sum():,.0f}"); m[3].metric("S.C.",f"{macro['S.C.'].sum():,.0f}"); m[4].metric("Criar S.C.",f"{(-macro.loc[macro['DIV']<0,'DIV']).sum():,.0f}")"""
_metric_new = """st.markdown("<style>[class*=st-key-mrp_kpi_]{position:relative}[class*=st-key-mrp_kpi_] .mrp-dashboard-card{position:relative;pointer-events:none;min-height:104px;padding:12px 14px;border:1px solid #dfe5ec;border-left:5px solid var(--mrp-kpi-color);border-radius:12px;background:#fff;box-shadow:0 2px 10px rgba(15,23,42,.04);display:flex;flex-direction:column;transition:transform .16s ease,box-shadow .16s ease}[class*=st-key-mrp_kpi_]:hover .mrp-dashboard-card{transform:translateY(-2px);box-shadow:0 7px 20px rgba(15,23,42,.10)}.mrp-dashboard-card-title{display:flex;align-items:center;gap:7px;color:#475569;font-size:11px;font-weight:800;letter-spacing:.025em;text-transform:uppercase;line-height:1.2}.mrp-dashboard-card-dot{width:9px;height:9px;border-radius:999px;background:var(--mrp-kpi-color);box-shadow:0 0 0 4px rgba(148,163,184,.14);flex:0 0 auto}.mrp-dashboard-card-value{margin-top:8px;color:#0f172a;font-size:24px;font-weight:850;line-height:1;letter-spacing:-.035em}.mrp-dashboard-card-subtitle{margin-top:auto;padding-top:9px;color:#718096;font-size:9px;font-weight:750;letter-spacing:.03em;text-transform:uppercase}[class*=st-key-mrp_kpi_] [data-testid=stElementContainer]:has([data-testid=stButton]){position:absolute!important;inset:0!important;z-index:50!important;margin:0!important;padding:0!important;width:100%!important;height:100%!important}[class*=st-key-mrp_kpi_] [data-testid=stButton]{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;margin:0!important;padding:0!important}[class*=st-key-mrp_kpi_] [data-testid=stButton] button{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-height:104px!important;border-radius:12px!important;opacity:0!important;cursor:pointer!important}</style>",unsafe_allow_html=True)
_status_dashboard=_mrp_status_atendimento_series(demanda_projeto)
m=st.columns(5)
_mrp_dashboard_card(m[0],"Demandas no MRP",_mrp_numero_br(len(demanda_projeto)),"#2563eb","TOTAL DA DEMANDA POR PROJETO","total","TODOS",True)
_mrp_dashboard_card(m[1],"Dentro do Prazo",_mrp_numero_br((_status_dashboard=="🟢").sum()),"#16a34a","ATENDIMENTO NO PRAZO OU ANTES","verde","🟢 DENTRO DO PRAZO",False)
_mrp_dashboard_card(m[2],"Atenção ao Prazo",_mrp_numero_br((_status_dashboard=="🟡").sum()),"#f59e0b","ATÉ 2 SEMANAS APÓS A NECESSIDADE","amarelo","🟡 ATENÇÃO AO PRAZO",False)
_mrp_dashboard_card(m[3],"Atendimento Crítico",_mrp_numero_br((_status_dashboard=="🔴").sum()),"#ef4444","ACIMA DE 2 SEMANAS OU SEM PREVISÃO","vermelho","🔴 ATENDIMENTO CRÍTICO",False)
_mrp_dashboard_card(m[4],"Demandas Não Aptas",_mrp_numero_br((_status_dashboard=="⚪").sum()),"#94a3b8","RESÍDUOS, SUSPENSAS E CANCELADAS","cinza","⚪ DEMANDAS NÃO APTAS",True)"""
_final_replace(_metric_old, _metric_new, "formatação brasileira dos indicadores")

# ---------------------------------------------------------
# 3) CONSULTA — DEMANDA GERAL: filtros separados.
# ---------------------------------------------------------
_consulta_geral_form_old = """        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3 = st.columns(3)
            busca_consulta = c1.text_input("CÓDIGO / DESCRIÇÃO", key="consulta_busca_geral", placeholder="DIGITE O CÓDIGO OU PARTE DA DESCRIÇÃO")
            status = c2.selectbox("STATUS", ["TODOS"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            tipo = c3.selectbox("TIPO", ["TODOS"] + tipos, key="consulta_tipo")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary", on_click=_normalizar_busca_codigo_8, args=("consulta_busca_geral",))
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_busca_geral","consulta_tipo","consulta_status"))"""
_consulta_geral_form_new = """        with st.form("consulta_geral_filtros", border=False):
            c1, c2, c3, c4 = st.columns(4)
            codigo_consulta = c1.text_input("CÓDIGO", key="consulta_codigo_busca", placeholder="DIGITE O CÓDIGO")
            descricao_consulta = c2.text_input("DESCRIÇÃO", key="consulta_descricao_busca", placeholder="DIGITE PARTE DA DESCRIÇÃO")
            tipo = c3.selectbox("TIPO", ["TODOS"] + tipos, key="consulta_tipo")
            status = c4.selectbox("STATUS", ["TODOS"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary", on_click=_normalizar_busca_codigo_8, args=("consulta_codigo_busca",))
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_codigo_busca","consulta_descricao_busca","consulta_tipo","consulta_status"))"""
_final_replace(_consulta_geral_form_old, _consulta_geral_form_new, "filtros separados da Demanda Geral em consulta")

_consulta_geral_logic_old = """        f = mg.copy()
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
_consulta_geral_logic_new = """        f = mg.copy()
        if codigo_consulta:
            f=f[_mrp_codigo_mask(f["Código"],codigo_consulta)]
        if descricao_consulta:
            _dc=descricao_consulta.strip()
            f=f[f["Descrição"].fillna("").astype(str).str.contains(_dc,case=False,na=False,regex=False)]
        if tipo != "TODOS": f = f[f["Tipo"].astype(str) == tipo]
        if status != "TODOS": f = f[f["Status"].astype(str) == status]
        f = f.reset_index(drop=True)"""
_final_replace(_consulta_geral_logic_old, _consulta_geral_logic_new, "lógica dos filtros separados da Demanda Geral em consulta")

# ---------------------------------------------------------
# 4) CONSULTA — DEMANDA POR PROJETO: 4 filtros + resíduos.
# ---------------------------------------------------------
_consulta_proj_form_old = """        with st.form("consulta_projeto_filtros", border=False):
            c1, c2 = st.columns(2)
            busca_projeto_consulta = c1.text_input("PROJETO / PRODUTO", key="consulta_busca_projeto", placeholder="DIGITE O PROJETO OU PRODUTO")
            semana = c2.selectbox("SEMANA DE NECESSIDADE", ["TODAS"] + semanas, key="consulta_semana")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_busca_projeto","consulta_semana"))"""
_consulta_proj_form_new = """        with st.form("consulta_projeto_filtros", border=False):
            c1, c2, c3, c4 = st.columns(4)
            projeto_consulta = c1.text_input("PROJETO", key="consulta_projeto_busca", placeholder="DIGITE O PROJETO")
            produto_consulta = c2.text_input("PRODUTO", key="consulta_produto_busca", placeholder="DIGITE O CÓDIGO")
            descricao_projeto_consulta = c3.text_input("DESCRIÇÃO", key="consulta_projeto_descricao", placeholder="DIGITE PARTE DA DESCRIÇÃO")
            _semana_opts = ["TODAS"] + semanas
            semana = c4.selectbox("SEMANA", _semana_opts, key="consulta_semana", format_func=lambda x: "TODAS" if x=="TODAS" else formatar_semana(x))
            mostrar_residuos_consulta = st.checkbox("MOSTRAR DEMANDAS NÃO APTAS", value=False, key="consulta_mostrar_residuos", help="Inclui resíduos, demandas suspensas e canceladas.")
            _bpesq, _blimpa = st.columns([8,1])
            with _bpesq:
                st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
            with _blimpa:
                st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("consulta_projeto_busca","consulta_produto_busca","consulta_projeto_descricao","consulta_semana","consulta_mostrar_residuos"))"""
_final_replace(_consulta_proj_form_old, _consulta_proj_form_new, "filtros separados da Demanda por Projeto em consulta")

_consulta_proj_logic_old = """        f = dem.copy()
        if busca_projeto_consulta:
            _bp = busca_projeto_consulta.strip()
            f = f[
                f["Projeto"].astype(str).str.contains(_bp, case=False, na=False)
                | f["Produto"].astype(str).str.contains(_bp, case=False, na=False)
            ]
        if semana != "TODAS": f = f[f["Semana de Necessidade"].astype(str) == semana]"""
_consulta_proj_logic_new = """        f = dem.copy()
        if not mostrar_residuos_consulta:
            f=f[~_mrp_demanda_nao_apta_mask(f)]
        if projeto_consulta:
            _pc=projeto_consulta.strip()
            f=f[f["Projeto"].fillna("").astype(str).str.contains(_pc,case=False,na=False,regex=False)]
        if produto_consulta:
            f=f[_mrp_codigo_mask(f["Produto"],produto_consulta)]
        if descricao_projeto_consulta:
            _dpc=descricao_projeto_consulta.strip()
            f=f[f["Descrição"].fillna("").astype(str).str.contains(_dpc,case=False,na=False,regex=False)]
        if semana != "TODAS": f = f[f["Semana de Necessidade"].astype(str) == str(semana)]
        f=f.reset_index(drop=True)"""
_final_replace(_consulta_proj_logic_old, _consulta_proj_logic_new, "lógica da Demanda por Projeto em consulta")

# ---------------------------------------------------------
# 5) ADMIN — DEMANDA GERAL: filtros separados.
# ---------------------------------------------------------
_admin_geral_form_old = """    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3=st.columns(3)
        with c1: busca=st.text_input("CÓDIGO / DESCRIÇÃO", key="admin_busca_geral", placeholder="DIGITE O CÓDIGO OU PARTE DA DESCRIÇÃO")
        with c2: status=st.selectbox("STATUS",["TODOS","OK","CRIAR S.C."], key="admin_status_geral")
        with c3: tipo_filtro=st.selectbox("TIPO",["TODOS"]+sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipo_geral")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary", on_click=_normalizar_busca_codigo_8, args=("admin_busca_geral",))
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_geral","admin_status_geral","admin_tipo_geral"))"""
_admin_geral_form_new = """    with st.form("admin_demanda_geral_filtros", border=False):
        c1,c2,c3,c4=st.columns(4)
        with c1: codigo_admin=st.text_input("CÓDIGO", key="admin_codigo_geral", placeholder="DIGITE O CÓDIGO")
        with c2: descricao_admin=st.text_input("DESCRIÇÃO", key="admin_descricao_geral", placeholder="DIGITE PARTE DA DESCRIÇÃO")
        with c3: tipo_filtro=st.selectbox("TIPO",["TODOS"]+sorted([x for x in cad["Tipo"].unique() if x]), key="admin_tipo_geral")
        with c4: status=st.selectbox("STATUS",["TODOS","OK","CRIAR S.C."], key="admin_status_geral")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary", on_click=_normalizar_busca_codigo_8, args=("admin_codigo_geral",))
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_codigo_geral","admin_descricao_geral","admin_status_geral","admin_tipo_geral"))"""
_final_replace(_admin_geral_form_old, _admin_geral_form_new, "filtros separados da Demanda Geral ADMIN")

_admin_search_old = """    if busca:
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
_admin_search_new = """    if codigo_admin:
        v=v[_mrp_codigo_mask(v["Código"],codigo_admin)]
    if descricao_admin:
        _da=descricao_admin.strip()
        v=v[v["Descrição"].fillna("").astype(str).str.contains(_da,case=False,na=False,regex=False)]
    v=v.reset_index(drop=True)"""
_final_replace(_admin_search_old, _admin_search_new, "lógica dos filtros separados da Demanda Geral ADMIN")

# ---------------------------------------------------------
# 6) ADMIN — DEMANDA POR PROJETO: 4 filtros + resíduos.
# ---------------------------------------------------------
_admin_proj_form_old = """    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2=st.columns(2)
        with c1: busca2=st.text_input("CÓDIGO / PROJETO", key="admin_busca_projeto", placeholder="DIGITE O CÓDIGO OU PROJETO")
        with c2: semana_filtro=st.selectbox("SEMANA",["TODAS"]+sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else ["TODAS"], key="admin_semana_projeto")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_busca_projeto","admin_semana_projeto"))"""
_admin_proj_form_new = """    with st.form("admin_demanda_projeto_filtros", border=False):
        c1,c2,c3,c4=st.columns(4)
        with c1: projeto_admin=st.text_input("PROJETO", key="admin_projeto_busca", placeholder="DIGITE O PROJETO")
        with c2: produto_admin=st.text_input("PRODUTO", key="admin_produto_busca", placeholder="DIGITE O CÓDIGO")
        with c3: descricao_proj_admin=st.text_input("DESCRIÇÃO", key="admin_proj_descricao", placeholder="DIGITE PARTE DA DESCRIÇÃO")
        _semana_admin_opts=["TODAS"]+sorted(demanda_projeto["Semana de Necessidade"].dropna().unique().tolist()) if len(demanda_projeto) else ["TODAS"]
        with c4: semana_filtro=st.selectbox("SEMANA",_semana_admin_opts, key="admin_semana_projeto", format_func=lambda x: "TODAS" if x=="TODAS" else formatar_semana(x))
        _status_opts=["TODOS","🟢 DENTRO DO PRAZO","🟡 ATENÇÃO AO PRAZO","🔴 ATENDIMENTO CRÍTICO","⚪ DEMANDAS NÃO APTAS"]
        status_atendimento_admin=st.selectbox("STATUS DE ATENDIMENTO",_status_opts,key="admin_status_atendimento")
        mostrar_residuos_admin=st.checkbox("MOSTRAR DEMANDAS NÃO APTAS", value=False, key="admin_mostrar_residuos", help="Inclui resíduos, demandas suspensas e canceladas.")
        _bpesq, _blimpa = st.columns([8,1])
        with _bpesq:
            st.form_submit_button("INICIAR PESQUISA", use_container_width=True, type="primary")
        with _blimpa:
            st.form_submit_button("LIMPAR", use_container_width=True, type="secondary", on_click=_limpar_filtros_mrp, args=("admin_projeto_busca","admin_produto_busca","admin_proj_descricao","admin_semana_projeto","admin_status_atendimento","admin_mostrar_residuos"))"""
_final_replace(_admin_proj_form_old, _admin_proj_form_new, "filtros separados da Demanda por Projeto ADMIN")

_admin_proj_logic_old = """    d=demanda_projeto.copy()
    if busca2:
        b2=busca2.strip(); d=d[d["Produto"].astype(str).str.contains(b2,na=False)|d["Projeto"].str.contains(b2,case=False,na=False)]
    if semana_filtro != "TODAS": d=d[d["Semana de Necessidade"] == semana_filtro]"""
_admin_proj_logic_new = """    d=demanda_projeto.copy()
    _status_alvo={"🟢 DENTRO DO PRAZO":"🟢","🟡 ATENÇÃO AO PRAZO":"🟡","🔴 ATENDIMENTO CRÍTICO":"🔴","⚪ DEMANDAS NÃO APTAS":"⚪"}.get(status_atendimento_admin)
    if not mostrar_residuos_admin and _status_alvo!="⚪":
        d=d[~_mrp_demanda_nao_apta_mask(d)]
    if _status_alvo:
        _status_linhas=_mrp_status_atendimento_series(d)
        d=d[_status_linhas==_status_alvo]
    if projeto_admin:
        _pa=projeto_admin.strip()
        d=d[d["Projeto"].fillna("").astype(str).str.contains(_pa,case=False,na=False,regex=False)]
    if produto_admin:
        d=d[_mrp_codigo_mask(d["Produto"],produto_admin)]
    if descricao_proj_admin:
        _dpa=descricao_proj_admin.strip()
        d=d[d["Descrição"].fillna("").astype(str).str.contains(_dpa,case=False,na=False,regex=False)]
    if semana_filtro != "TODAS": d=d[d["Semana de Necessidade"] == semana_filtro]
    d=d.reset_index(drop=True)
    if "Status de Atendimento" in d.columns:
        d=d.drop(columns=["Status de Atendimento"])
    _sinal_pos=list(d.columns).index("Semana de Atendimento")+1 if "Semana de Atendimento" in d.columns else len(d.columns)
    d.insert(_sinal_pos,"Status de Atendimento",_mrp_status_atendimento_series(d))"""
_final_replace(_admin_proj_logic_old, _admin_proj_logic_new, "lógica da Demanda por Projeto ADMIN")

# ---------------------------------------------------------
# 6.1) DETALHAMENTO DA DEMANDA GERAL — somente demandas aptas.
# ---------------------------------------------------------
_consulta_detail_old = '                d_dem = fix_columns(dem[dem["Produto"].astype(str) == selecionado], DEM_COLS)'
_consulta_detail_new = '                d_dem = fix_columns(dem[dem["Produto"].astype(str) == selecionado], DEM_COLS)\n                d_dem = d_dem[~_mrp_demanda_nao_apta_mask(d_dem)].reset_index(drop=True)'
_final_replace(_consulta_detail_old, _consulta_detail_new, "detalhe da Demanda Geral CONSULTA sem demandas não aptas")

_admin_detail_old = '        d=demanda_projeto[demanda_projeto["Produto"]==code]'
_admin_detail_new = '        d=demanda_projeto[demanda_projeto["Produto"]==code].copy()\n        d=d[~_mrp_demanda_nao_apta_mask(d)].reset_index(drop=True)'
_final_replace(_admin_detail_old, _admin_detail_new, "detalhe da Demanda Geral ADMIN sem demandas não aptas")

# ---------------------------------------------------------
# 6.2) STATUS DE ATENDIMENTO — comparação Necessidade x Atendimento.
# ---------------------------------------------------------
_final_replace(
    'DEM_COLS = ["Projeto", "Produto", "Descrição", "Última Solicitação", "Data CM", "Semana de Necessidade", "Semana de Atendimento", "Necessidade", "Estoque", "Pré Nota", "P.C.", "Fabricação", "S.C.", "Ação", "Resumo"]',
    'DEM_COLS = ["Projeto", "Produto", "Descrição", "Última Solicitação", "Data CM", "Semana de Necessidade", "Semana de Atendimento", "Status de Atendimento", "Necessidade", "Estoque", "Pré Nota", "P.C.", "Fabricação", "S.C.", "Ação", "Resumo"]',
    "Status de Atendimento na ordem oficial da consulta"
)

_final_replace(
    '    dem = fix_columns(dem, DEM_COLS)',
    '    dem = fix_columns(dem, DEM_COLS)\n    dem["Status de Atendimento"]=_mrp_status_atendimento_series(dem)',
    "recalcula Status de Atendimento em snapshots antigos e atuais"
)

# ---------------------------------------------------------
# 7) TRATATIVA DE PROJETOS — gestão de carga recolhida e só ADMIN.
# ---------------------------------------------------------
_project_admin_old = """    if st.session_state.get("auth_role")=="ADMIN":
        modelo=pd.DataFrame({"Projeto":["EXEMPLO"],"OBS":["RESÍDUO"]})
        c1,c2=st.columns([1,1])
        with c1:
            st.download_button(
                "BAIXAR MODELO DE CARGA",
                excel_bytes({"Tratativas":modelo}),
                "Modelo_Tratativa_Projetos.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_modelo_tratativas",
            )
        with c2:
            uploaded=st.file_uploader(
                "Subir carga de tratativas",
                type=["xlsx","xlsm","csv"],
                key="tratativa_projetos_upload",
                help="Use as colunas Projeto e OBS. OBS em branco remove a tratativa já salva para o projeto.",
            )

        if uploaded is not None:
            try:
                carga=_carregar_tratativas_arquivo(uploaded)
                sig=hashlib.sha256(uploaded.getvalue()).hexdigest()
                if st.session_state.get("_tratativa_upload_saved_sig")!=sig:
                    total=_salvar_tratativas_db(carga)
                    st.session_state["_tratativa_upload_saved_sig"]=sig
                    st.success(f"{total} tratativa(s) processada(s) e salva(s) no banco.")
                    st.rerun()
            except Exception as e:
                st.error(f"Não foi possível salvar a carga de tratativas: {e}")
"""
_project_admin_new = """    if st.session_state.get("auth_role")=="ADMIN":
        with st.expander("GERENCIAR CARGA — TRATATIVA DE PROJETOS", expanded=False):
            st.caption("Baixe o modelo ou importe uma carga de tratativas. Esta área é exclusiva para ADMIN.")
            modelo=pd.DataFrame({"Projeto":["EXEMPLO"],"OBS":["RESÍDUO"]})
            c1,c2=st.columns([1,1])
            with c1:
                st.download_button(
                    "BAIXAR MODELO DE CARGA",
                    excel_bytes({"Tratativas":modelo}),
                    "Modelo_Tratativa_Projetos.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_modelo_tratativas",
                )
            with c2:
                uploaded=st.file_uploader(
                    "IMPORTAR CARGA",
                    type=["xlsx","xlsm","csv"],
                    key="tratativa_projetos_upload",
                    help="Use as colunas Projeto e OBS. OBS em branco remove a tratativa já salva para o projeto.",
                )

            if uploaded is not None:
                try:
                    carga=_carregar_tratativas_arquivo(uploaded)
                    sig=hashlib.sha256(uploaded.getvalue()).hexdigest()
                    if st.session_state.get("_tratativa_upload_saved_sig")!=sig:
                        total=_salvar_tratativas_db(carga)
                        st.session_state["_tratativa_upload_saved_sig"]=sig
                        st.success(f"{total} tratativa(s) processada(s) e salva(s) no banco.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Não foi possível salvar a carga de tratativas: {e}")
"""
_final_replace(_project_admin_old, _project_admin_new, "gestão recolhida da Tratativa de Projetos")

# ---------------------------------------------------------
# 8) TRATATIVA DE PRODUTOS POR PROJETO — mesma regra.
# ---------------------------------------------------------
_product_admin_old = """    if st.session_state.get("auth_role")=="ADMIN":
        modelo=pd.DataFrame({"Projeto":["EXEMPLO"],"Produto":["00000001"],"OBS":["RESÍDUO"]})
        c1,c2=st.columns([1,1])
        with c1:
            st.download_button(
                "BAIXAR MODELO — PRODUTO",
                excel_bytes({"Tratativas_Produtos":modelo}),
                "Modelo_Tratativa_Produtos_Projeto.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_modelo_tratativas_produto",
            )
        with c2:
            uploaded=st.file_uploader(
                "Subir tratativa por produto",
                type=["xlsx","xlsm","csv"],
                key="tratativa_produto_upload",
                help="Use as colunas Projeto, Produto e OBS. OBS em branco remove a tratativa desse produto no projeto.",
            )

        if uploaded is not None:
            try:
                carga=_carregar_tratativas_produto_arquivo(uploaded)
                sig=hashlib.sha256(uploaded.getvalue()).hexdigest()
                if st.session_state.get("_tratativa_produto_upload_saved_sig")!=sig:
                    total=_salvar_tratativas_produto_db(carga)
                    st.session_state["_tratativa_produto_upload_saved_sig"]=sig
                    st.success(f"{total} tratativa(s) de produto processada(s) e salva(s) no banco.")
                    st.rerun()
            except Exception as e:
                st.error(f"Não foi possível salvar a carga de tratativas por produto: {e}")
"""
_product_admin_new = """    if st.session_state.get("auth_role")=="ADMIN":
        with st.expander("GERENCIAR CARGA — PRODUTOS POR PROJETO", expanded=False):
            st.caption("Baixe o modelo ou importe uma carga por Projeto + Produto. Esta área é exclusiva para ADMIN.")
            modelo=pd.DataFrame({"Projeto":["EXEMPLO"],"Produto":["00000001"],"OBS":["RESÍDUO"]})
            c1,c2=st.columns([1,1])
            with c1:
                st.download_button(
                    "BAIXAR MODELO — PRODUTO",
                    excel_bytes({"Tratativas_Produtos":modelo}),
                    "Modelo_Tratativa_Produtos_Projeto.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_modelo_tratativas_produto",
                )
            with c2:
                uploaded=st.file_uploader(
                    "IMPORTAR CARGA",
                    type=["xlsx","xlsm","csv"],
                    key="tratativa_produto_upload",
                    help="Use as colunas Projeto, Produto e OBS. OBS em branco remove a tratativa desse produto no projeto.",
                )

            if uploaded is not None:
                try:
                    carga=_carregar_tratativas_produto_arquivo(uploaded)
                    sig=hashlib.sha256(uploaded.getvalue()).hexdigest()
                    if st.session_state.get("_tratativa_produto_upload_saved_sig")!=sig:
                        total=_salvar_tratativas_produto_db(carga)
                        st.session_state["_tratativa_produto_upload_saved_sig"]=sig
                        st.success(f"{total} tratativa(s) de produto processada(s) e salva(s) no banco.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Não foi possível salvar a carga de tratativas por produto: {e}")
"""
_final_replace(_product_admin_old, _product_admin_new, "gestão recolhida da Tratativa de Produtos por Projeto")
'''
