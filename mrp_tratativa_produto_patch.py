TRATATIVA_PRODUTO_PATCH = r'''
# =========================================================
# TRATATIVA DE PRODUTOS POR PROJETO
# Chave composta: Projeto + Produto
# RESÍDUO aqui zera somente o material dentro da OP.
# =========================================================

# ---------------------------------------------------------
# HELPERS / PERSISTÊNCIA
# ---------------------------------------------------------
_helpers_anchor = 'def render_tratativa_projetos():\n'
_helpers = r"""
def _produto_key(valor):
    if pd.isna(valor):
        return ""
    txt=str(valor).strip()
    if not txt:
        return ""
    try:
        return str(int(float(txt.replace(",","."))))
    except Exception:
        return re.sub(r"\.0$","",txt)

def _carregar_tratativas_produto_arquivo(uploaded):
    cols=["Projeto","Produto","OBS"]
    if uploaded is None:
        return pd.DataFrame(columns=cols)
    nome=str(getattr(uploaded,"name","")).lower()
    dados=uploaded.getvalue()
    if nome.endswith(".csv"):
        try:
            base=pd.read_csv(BytesIO(dados),sep=None,engine="python",dtype=str)
        except Exception:
            base=pd.read_csv(BytesIO(dados),sep=";",dtype=str)
    else:
        base=pd.read_excel(BytesIO(dados),dtype=str)
    if base is None or base.empty or base.shape[1]<3:
        return pd.DataFrame(columns=cols)
    norm={c:_texto_normalizado(c) for c in base.columns}
    projeto_col=next((c for c,n in norm.items() if n in {"PROJETO","NUMERO DO PROJETO","N PROJETO","Nº PROJETO","OP"}),base.columns[0])
    produto_col=next((c for c,n in norm.items() if n in {"PRODUTO","CODIGO","CODIGO PRODUTO","MATERIAL","COD MATERIAL"}),base.columns[1])
    obs_col=next((c for c,n in norm.items() if n in {"OBS","OBSERVACAO","COMENTARIO","TRATATIVA"}),base.columns[2])
    out=pd.DataFrame({
        "Projeto":base[projeto_col].map(_projeto_key),
        "Produto":base[produto_col].map(_produto_key),
        "OBS":base[obs_col].fillna("").astype(str).str.strip(),
    })
    out=out[out["Projeto"].ne("") & out["Produto"].ne("")].copy()
    return out.drop_duplicates(["Projeto","Produto"],keep="last").reset_index(drop=True)

def _tratativas_produto_request(method, params=None, payload=None, prefer=None, timeout=30):
    headers=_sb_headers().copy()
    if prefer:
        headers["Prefer"]=prefer
    url=f"{SUPABASE_URL}/rest/v1/mrp_project_product_treatments"
    request_kwargs={"headers":headers,"params":params or {},"timeout":timeout}
    if payload is not None:
        request_kwargs["json"]=payload
    r=requests.request(method,url,**request_kwargs)
    if r.status_code == 401 and _refresh_supabase_session():
        headers=_sb_headers().copy()
        if prefer:
            headers["Prefer"]=prefer
        request_kwargs["headers"]=headers
        r=requests.request(method,url,**request_kwargs)
    r.raise_for_status()
    if not r.text.strip():
        return []
    try:
        return r.json()
    except Exception:
        return []

def _carregar_tratativas_produto_salvas():
    rows=_tratativas_produto_request(
        "GET",
        params={"select":"projeto,produto,obs,updated_at,updated_by","order":"updated_at.desc"},
        timeout=20,
    )
    if not rows:
        return pd.DataFrame(columns=["Projeto","Produto","OBS","Atualizado em","Atualizado por"])
    out=pd.DataFrame(rows)
    for c in ["projeto","produto","obs","updated_at","updated_by"]:
        if c not in out.columns:
            out[c]=""
    out["Projeto"]=out["projeto"].map(_projeto_key)
    out["Produto"]=out["produto"].map(_produto_key)
    out["OBS"]=out["obs"].fillna("").astype(str).str.strip()
    _dt=pd.to_datetime(out["updated_at"],errors="coerce",utc=True)
    _dt=_dt.dt.tz_convert("America/Sao_Paulo")
    out["Atualizado em"]=_dt.dt.strftime("%d/%m/%Y %H:%M").fillna("")
    out["Atualizado por"]=out["updated_by"].fillna("").astype(str)
    return out[["Projeto","Produto","OBS","Atualizado em","Atualizado por"]].drop_duplicates(["Projeto","Produto"],keep="first").reset_index(drop=True)

def _salvar_tratativas_produto_db(df):
    if st.session_state.get("auth_role")!="ADMIN":
        raise PermissionError("Somente usuários ADMIN podem alterar tratativas de produtos.")
    if df is None or df.empty:
        return 0
    base=df[["Projeto","Produto","OBS"]].copy()
    base["Projeto"]=base["Projeto"].map(_projeto_key)
    base["Produto"]=base["Produto"].map(_produto_key)
    base["OBS"]=base["OBS"].fillna("").astype(str).str.strip()
    base=base[base["Projeto"].ne("") & base["Produto"].ne("")].drop_duplicates(["Projeto","Produto"],keep="last")
    usuario=str(st.session_state.get("auth_nome") or st.session_state.get("auth_email") or "")
    agora=pd.Timestamp.utcnow().isoformat()

    remover=base[base["OBS"].eq("")]
    for _,r in remover.iterrows():
        _tratativas_produto_request(
            "DELETE",
            params={"projeto":f"eq.{r['Projeto']}","produto":f"eq.{r['Produto']}"},
            prefer="return=minimal",
        )

    gravar=base[base["OBS"].ne("")]
    if len(gravar):
        payload=[
            {
                "projeto":str(r["Projeto"]),
                "produto":str(r["Produto"]),
                "obs":str(r["OBS"]),
                "updated_at":agora,
                "updated_by":usuario,
            }
            for _,r in gravar.iterrows()
        ]
        _tratativas_produto_request(
            "POST",
            params={"on_conflict":"projeto,produto"},
            payload=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
    return len(base)

def render_tratativa_produtos():
    st.markdown("### Tratativa de Produtos por Projeto")
    st.caption("Use Projeto + Produto para tratar apenas um material da OP. RESÍDUO zera somente esse produto; os demais materiais do projeto continuam normalmente no MRP.")

    if st.session_state.get("auth_role")=="ADMIN":
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

    try:
        salvas=_carregar_tratativas_produto_salvas()
    except Exception as e:
        st.error(f"Não foi possível carregar as tratativas de produtos salvas: {e}")
        return

    if salvas.empty:
        st.info("Nenhuma tratativa por produto está salva no momento.")
        return

    atualizadores=sorted([x for x in salvas["Atualizado por"].fillna("").astype(str).unique().tolist() if x])
    with st.form("tratativa_produto_filtros",border=False):
        c1,c2,c3,c4=st.columns(4)
        projeto_filtro=c1.text_input("Projeto",key="trat_prod_projeto",placeholder="Digite o projeto")
        produto_filtro=c2.text_input("Produto",key="trat_prod_produto",placeholder="Digite o código")
        obs_filtro=c3.text_input("OBS / Tratativa",key="trat_prod_obs",placeholder="Ex.: RESÍDUO")
        atualizado_filtro=c4.selectbox("Atualizado por",["Todos"]+atualizadores,key="trat_prod_atualizado")
        _bp,_bl=st.columns([8,1])
        with _bp:
            st.form_submit_button("INICIAR PESQUISA",use_container_width=True,type="primary")
        with _bl:
            st.form_submit_button(
                "LIMPAR",
                use_container_width=True,
                type="secondary",
                on_click=_limpar_filtros_mrp,
                args=("trat_prod_projeto","trat_prod_produto","trat_prod_obs","trat_prod_atualizado"),
            )

    filtradas=salvas.copy()
    if projeto_filtro:
        filtradas=filtradas[filtradas["Projeto"].astype(str).str.contains(projeto_filtro.strip(),case=False,na=False)]
    if produto_filtro:
        filtradas=filtradas[filtradas["Produto"].astype(str).str.contains(produto_filtro.strip(),case=False,na=False)]
    if obs_filtro:
        filtradas=filtradas[filtradas["OBS"].astype(str).str.contains(obs_filtro.strip(),case=False,na=False)]
    if atualizado_filtro!="Todos":
        filtradas=filtradas[filtradas["Atualizado por"].astype(str).eq(atualizado_filtro)]

    st.dataframe(filtradas,use_container_width=True,hide_index=True)
    st.caption(f"{len(filtradas)} de {len(salvas)} tratativa(s) por produto exibida(s).")
"""
if _helpers_anchor not in _source:
    raise RuntimeError("Função de Tratativa de Projetos não encontrada para incluir tratamento por produto.")
_source = _source.replace(_helpers_anchor, _helpers + "\n" + _helpers_anchor, 1)

# Exibe a área de produto ao final da aba de Tratativa de Projetos.
_project_ui_end = '        st.caption(f"{len(filtradas)} de {len(salvas)} tratativa(s) exibida(s). Para alterar uma observação, envie novamente o mesmo projeto com a nova OBS. Para remover, envie o projeto com a OBS em branco.")\n'
_project_ui_new = _project_ui_end + '    st.divider()\n    render_tratativa_produtos()\n'
if _project_ui_end not in _source:
    raise RuntimeError("Fim da interface de Tratativa de Projetos não encontrado.")
_source = _source.replace(_project_ui_end, _project_ui_new, 1)

# ---------------------------------------------------------
# DEMANDA GERAL / PROJEÇÃO — EXCLUI SOMENTE O ITEM TRATADO
# ---------------------------------------------------------
_general_anchor = 'rg_mrp_efetivo["OBS Tratativa"]=rg_mrp_efetivo["Projeto"].map(_tratativa_demanda_map).fillna("")\n'
_general_insert = r"""rg_mrp_efetivo["OBS Tratativa"]=rg_mrp_efetivo["Projeto"].map(_tratativa_demanda_map).fillna("")
try:
    _tratativas_produto_demanda=_carregar_tratativas_produto_salvas()
except Exception as _trat_prod_geral_err:
    st.error(f"Não foi possível carregar as tratativas por produto para cálculo da Demanda Geral: {_trat_prod_geral_err}")
    st.stop()
_tratativa_produto_demanda_map={
    (_projeto_key(r["Projeto"]),_produto_key(r["Produto"])):str(r["OBS"] or "")
    for _,r in _tratativas_produto_demanda.iterrows()
} if len(_tratativas_produto_demanda) else {}
rg_mrp_efetivo["_ProdutoChave"]=rg_mrp_efetivo["Código"].map(_produto_key)
rg_mrp_efetivo["OBS Tratativa Produto"]=[
    _tratativa_produto_demanda_map.get((_projeto_key(p),_produto_key(c)),"")
    for p,c in zip(rg_mrp_efetivo["Projeto"],rg_mrp_efetivo["_ProdutoChave"])
]
"""
if _general_anchor not in _source:
    raise RuntimeError("Mapa de tratativa da Demanda Geral não encontrado.")
_source = _source.replace(_general_anchor, _general_insert, 1)

_general_zero_old = 'rg_mrp_efetivo.loc[_condicao_desconsiderada|_residuo_desconsiderado,"Pendência"]=0.0'
_general_zero_new = '_residuo_produto_desconsiderado=rg_mrp_efetivo["OBS Tratativa Produto"].map(_texto_normalizado).eq("RESIDUO")\nrg_mrp_efetivo.loc[_condicao_desconsiderada|_residuo_desconsiderado|_residuo_produto_desconsiderado,"Pendência"]=0.0'
if _general_zero_old not in _source:
    raise RuntimeError("Regra de zeragem da Demanda Geral não encontrada.")
_source = _source.replace(_general_zero_old, _general_zero_new, 1)

# ---------------------------------------------------------
# DEMANDA POR PROJETO — CARREGA E APLICA PROJETO + PRODUTO
# ---------------------------------------------------------
_project_map_anchor = 'tratativa_map=tratativas_projeto.set_index("Projeto")["OBS"].to_dict() if len(tratativas_projeto) else {}\n'
_project_map_new = r"""tratativa_map=tratativas_projeto.set_index("Projeto")["OBS"].to_dict() if len(tratativas_projeto) else {}
try:
    tratativas_produto=_carregar_tratativas_produto_salvas()
except Exception as e:
    st.error(f"Não foi possível carregar as tratativas por produto salvas: {e}")
    st.stop()
tratativa_produto_map={
    (_projeto_key(r["Projeto"]),_produto_key(r["Produto"])):str(r["OBS"] or "")
    for _,r in tratativas_produto.iterrows()
} if len(tratativas_produto) else {}
"""
if _project_map_anchor not in _source:
    raise RuntimeError("Mapa de Tratativa de Projetos não encontrado para inclusão dos produtos.")
_source = _source.replace(_project_map_anchor, _project_map_new, 1)

_base_obs_anchor = 'demanda_projeto_base["OBS Tratativa"]=demanda_projeto_base["Projeto"].map(tratativa_map).fillna("")\n'
_base_obs_new = r"""demanda_projeto_base["OBS Tratativa"]=demanda_projeto_base["Projeto"].map(tratativa_map).fillna("")
demanda_projeto_base["_ProdutoChave"]=demanda_projeto_base["Produto"].map(_produto_key)
demanda_projeto_base["OBS Tratativa Produto"]=[
    tratativa_produto_map.get((_projeto_key(p),_produto_key(c)),"")
    for p,c in zip(demanda_projeto_base["Projeto"],demanda_projeto_base["_ProdutoChave"])
]
"""
if _base_obs_anchor not in _source:
    raise RuntimeError("OBS da Tratativa de Projetos não encontrada para inclusão do produto.")
_source = _source.replace(_base_obs_anchor, _base_obs_new, 1)

# Resumo: mantém OBS do projeto e identifica claramente a tratativa do produto.
_resumo_anchor = r"""    obs=str(row.get("OBS Tratativa","") or "").strip()
    if obs:
        partes.append("RESÍDUO" if _texto_normalizado(obs)=="RESIDUO" else obs)
    return " | ".join(partes)
"""
_resumo_new = r"""    obs=str(row.get("OBS Tratativa","") or "").strip()
    if obs:
        partes.append("RESÍDUO" if _texto_normalizado(obs)=="RESIDUO" else obs)
    obs_produto=str(row.get("OBS Tratativa Produto","") or "").strip()
    if obs_produto:
        partes.append("PRODUTO: RESÍDUO" if _texto_normalizado(obs_produto)=="RESIDUO" else f"PRODUTO: {obs_produto}")
    return " | ".join(partes)
"""
if _resumo_anchor not in _source:
    raise RuntimeError("Resumo da Demanda por Projeto não encontrado para tratativa por produto.")
_source = _source.replace(_resumo_anchor, _resumo_new, 1)

_zero_project_old = 'residuo_zerar=demanda_projeto_base["OBS Tratativa"].map(_texto_normalizado).eq("RESIDUO")\ndemanda_projeto_base.loc[cond_zerar|residuo_zerar,"Necessidade"]=0.0'
_zero_project_new = 'residuo_zerar=demanda_projeto_base["OBS Tratativa"].map(_texto_normalizado).eq("RESIDUO")\nresiduo_produto_zerar=demanda_projeto_base["OBS Tratativa Produto"].map(_texto_normalizado).eq("RESIDUO")\ndemanda_projeto_base.loc[cond_zerar|residuo_zerar|residuo_produto_zerar,"Necessidade"]=0.0'
if _zero_project_old not in _source:
    raise RuntimeError("Regra de zeragem da Demanda por Projeto não encontrada.")
_source = _source.replace(_zero_project_old, _zero_project_new, 1)

# Ação: diferencia resíduo do projeto inteiro de resíduo apenas do produto.
_action_obs_old = '            obs_norm=_texto_normalizado(r.get("OBS Tratativa",""))\n'
_action_obs_new = '            obs_norm=_texto_normalizado(r.get("OBS Tratativa",""))\n            obs_produto_norm=_texto_normalizado(r.get("OBS Tratativa Produto",""))\n'
if _action_obs_old not in _source:
    raise RuntimeError("Leitura da OBS de projeto não encontrada no cálculo da demanda.")
_source = _source.replace(_action_obs_old, _action_obs_new, 1)

_action_old = r"""            if necessidade<=1e-9 and pendencia_original>1e-9 and obs_norm=="RESIDUO":
                acoes=[f"RESÍDUO {pendencia_original:g}"]
                semana_atendimento="N/A"
            elif necessidade<=1e-9 and pendencia_original>1e-9 and cond in {"CANCELADO","SUSPENSO"}:
"""
_action_new = r"""            if necessidade<=1e-9 and pendencia_original>1e-9 and obs_norm=="RESIDUO":
                acoes=[f"RESÍDUO {pendencia_original:g}"]
                semana_atendimento="N/A"
            elif necessidade<=1e-9 and pendencia_original>1e-9 and obs_produto_norm=="RESIDUO":
                acoes=[f"RESÍDUO PRODUTO {pendencia_original:g}"]
                semana_atendimento="N/A"
            elif necessidade<=1e-9 and pendencia_original>1e-9 and cond in {"CANCELADO","SUSPENSO"}:
"""
if _action_old not in _source:
    raise RuntimeError("Regra de ação RESÍDUO não encontrada para diferenciar produto.")
_source = _source.replace(_action_old, _action_new, 1)

# ---------------------------------------------------------
# SNAPSHOT / EXPORTAÇÃO — CONSIDERA ALTERAÇÃO POR PRODUTO
# ---------------------------------------------------------
_hash_old = ' + json.dumps(tratativas_projeto[["Projeto","OBS"]].sort_values("Projeto").to_dict("records"),ensure_ascii=False,sort_keys=True).encode("utf-8")'
_hash_new = _hash_old + ' + json.dumps(tratativas_produto[["Projeto","Produto","OBS"]].sort_values(["Projeto","Produto"]).to_dict("records"),ensure_ascii=False,sort_keys=True).encode("utf-8")'
if _hash_old not in _source:
    raise RuntimeError("Hash das tratativas não encontrado para incluir tratamento por produto.")
_source = _source.replace(_hash_old, _hash_new, 1)

_export_old = '"Tratativas_Projetos":tratativas_projeto,"Compra_MRP"'
_export_new = '"Tratativas_Projetos":tratativas_projeto,"Tratativas_Produtos":tratativas_produto,"Compra_MRP"'
if _export_old not in _source:
    raise RuntimeError("Exportação das tratativas não encontrada para incluir produtos.")
_source = _source.replace(_export_old, _export_new, 1)
'''
