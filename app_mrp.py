from pathlib import Path
import re

_original = Path(__file__).with_name("app_mrp_original.py")
_source = _original.read_text(encoding="utf-8")


def _replace_once(old, new, label):
    global _source
    if old not in _source:
        raise RuntimeError(f"Bloco do MRP não encontrado para adequação: {label}.")
    _source = _source.replace(old, new, 1)


def _sub_once(pattern, replacement, label, flags=0):
    global _source
    new_source, count = re.subn(pattern, lambda _m: replacement, _source, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"Bloco do MRP não encontrado para adequação: {label}.")
    _source = new_source


# =========================================================
# OTIMIZAÇÕES DE LEITURA / SNAPSHOTS
# =========================================================
_source = _source.replace(
    "def _public_login_config():\n",
    "@st.cache_data(ttl=1800, show_spinner=False)\ndef _public_login_config():\n",
    1,
)

_pattern = re.compile(
    r"def load_latest_snapshot\(\):\n"
    r".*?"
    r"def save_snapshot\(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None\):\n"
    r".*?"
    r"    return _sb_post\(payload\)",
    re.S,
)

_replacement = '''@st.cache_data(ttl=60, show_spinner=False)
def load_latest_snapshot_meta():
    rows=_sb_get({"select":"id,created_at,semana_mrp,usuario","order":"created_at.desc","limit":"1"})
    return rows[0] if rows else None

@st.cache_data(ttl=120, show_spinner=False)
def load_snapshot_history(limit=50):
    return _sb_get({"select":"id,created_at,semana_mrp,usuario","order":"created_at.desc","limit":str(limit)})

@st.cache_data(ttl=3600, show_spinner=False)
def load_snapshot(snapshot_id):
    rows=_sb_get({"select":"*","id":f"eq.{int(snapshot_id)}","limit":"1"})
    return rows[0] if rows else None

def load_latest_snapshot():
    meta=load_latest_snapshot_meta()
    if not meta:
        return None
    return load_snapshot(meta["id"])

def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):
    def records(df):
        if df is None or df.empty: return []
        return json.loads(df.to_json(orient="records",force_ascii=False,date_format="iso"))
    payload={"semana_mrp":int(semana) if semana is not None else None,"usuario":usuario or "Não informado","mrp_geral":records(mrp_geral),"projecao_semanal":records(projecao_semanal),"demanda_projeto":records(demanda_projeto),"compra_mrp":records(compra_mrp),"compras":records(compras)}
    result=_sb_post(payload)
    load_latest_snapshot_meta.clear()
    load_snapshot_history.clear()
    load_snapshot.clear()
    return result'''

_source, _count = _pattern.subn(_replacement, _source, count=1)
if _count != 1:
    raise RuntimeError("Bloco de snapshots do MRP não encontrado para otimização.")


# =========================================================
# TRATATIVAS DE PROJETOS — PERSISTÊNCIA SUPABASE
# =========================================================
_sb_post_anchor = '''def _sb_post(payload):
    r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)
    if r.status_code == 401 and _refresh_supabase_session():
        r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)
    r.raise_for_status(); return r.json()
'''

_tratativas_helpers = r'''
def _texto_normalizado(valor):
    import unicodedata
    txt="" if pd.isna(valor) else str(valor).strip()
    return "".join(c for c in unicodedata.normalize("NFD",txt) if unicodedata.category(c)!="Mn").upper()

def _projeto_key(valor):
    txt="" if pd.isna(valor) else str(valor).strip()
    return re.sub(r"\.0$","",txt)

def _carregar_tratativas_arquivo(uploaded):
    cols=["Projeto","OBS"]
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
    if base is None or base.empty or base.shape[1]<2:
        return pd.DataFrame(columns=cols)
    norm={c:_texto_normalizado(c) for c in base.columns}
    projeto_col=next((c for c,n in norm.items() if n in {"PROJETO","NUMERO DO PROJETO","N PROJETO","Nº PROJETO","OP"}),base.columns[0])
    obs_col=next((c for c,n in norm.items() if n in {"OBS","OBSERVACAO","COMENTARIO","TRATATIVA"}),base.columns[1])
    out=pd.DataFrame({
        "Projeto":base[projeto_col].map(_projeto_key),
        "OBS":base[obs_col].fillna("").astype(str).str.strip(),
    })
    out=out[out["Projeto"].astype(str).str.strip().ne("")].copy()
    return out.drop_duplicates("Projeto",keep="last").reset_index(drop=True)

def _tratativas_request(method, params=None, payload=None, prefer=None, timeout=30):
    headers=_sb_headers().copy()
    if prefer:
        headers["Prefer"]=prefer
    url=f"{SUPABASE_URL}/rest/v1/mrp_project_treatments"
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

def _carregar_tratativas_salvas():
    rows=_tratativas_request(
        "GET",
        params={"select":"projeto,obs,updated_at,updated_by","order":"updated_at.desc"},
        timeout=20,
    )
    if not rows:
        return pd.DataFrame(columns=["Projeto","OBS","Atualizado em","Atualizado por"])
    out=pd.DataFrame(rows)
    for c in ["projeto","obs","updated_at","updated_by"]:
        if c not in out.columns:
            out[c]=""
    out["Projeto"]=out["projeto"].map(_projeto_key)
    out["OBS"]=out["obs"].fillna("").astype(str).str.strip()
    out["Atualizado em"]=out["updated_at"].fillna("").astype(str)
    out["Atualizado por"]=out["updated_by"].fillna("").astype(str)
    return out[["Projeto","OBS","Atualizado em","Atualizado por"]].drop_duplicates("Projeto",keep="first").reset_index(drop=True)

def _salvar_tratativas_db(df):
    if st.session_state.get("auth_role")!="ADMIN":
        raise PermissionError("Somente usuários ADMIN podem alterar tratativas de projetos.")
    if df is None or df.empty:
        return 0
    base=df[["Projeto","OBS"]].copy()
    base["Projeto"]=base["Projeto"].map(_projeto_key)
    base["OBS"]=base["OBS"].fillna("").astype(str).str.strip()
    base=base[base["Projeto"].ne("")].drop_duplicates("Projeto",keep="last")
    usuario=str(st.session_state.get("auth_nome") or st.session_state.get("auth_email") or "")
    agora=pd.Timestamp.utcnow().isoformat()

    remover=base[base["OBS"].eq("")]
    for projeto in remover["Projeto"].tolist():
        _tratativas_request("DELETE",params={"projeto":f"eq.{projeto}"},prefer="return=minimal")

    gravar=base[base["OBS"].ne("")]
    if len(gravar):
        payload=[
            {"projeto":str(r["Projeto"]),"obs":str(r["OBS"]),"updated_at":agora,"updated_by":usuario}
            for _,r in gravar.iterrows()
        ]
        _tratativas_request(
            "POST",
            params={"on_conflict":"projeto"},
            payload=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
    return len(base)

def render_tratativa_projetos():
    st.subheader("Tratativa de Projetos")
    st.caption("As tratativas ficam salvas no banco compartilhado. RESÍDUO zera a necessidade da Demanda por Projeto; outros comentários são acrescentados ao final do Resumo.")

    if st.session_state.get("auth_role")=="ADMIN":
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

    try:
        salvas=_carregar_tratativas_salvas()
    except Exception as e:
        st.error(f"Não foi possível carregar as tratativas salvas: {e}")
        return

    if salvas.empty:
        st.info("Nenhuma tratativa de projeto está salva no momento.")
    else:
        st.markdown("**Tratativas salvas**")
        st.dataframe(salvas,use_container_width=True,hide_index=True)
        st.caption("Para alterar uma observação, envie novamente o mesmo projeto com a nova OBS. Para remover, envie o projeto com a OBS em branco.")
'''

_replace_once(_sb_post_anchor, _sb_post_anchor + _tratativas_helpers, "funções persistentes de tratativa")


# =========================================================
# PADRÃO VISUAL — MESMO LAYOUT DO CONVERSOR MRP
# =========================================================
_visual_anchor = '''_render_brand_header(UI_CONFIG)
# === END VISUAL CONFIG SETTA V1 ==='''

_visual_replacement = '''_render_brand_header(UI_CONFIG)
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: var(--setta-background);
}
[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.96) !important;
}
.block-container {
    max-width: 1780px !important;
    padding-top: 3.2rem !important;
    padding-left: 2.7rem !important;
    padding-right: 2.7rem !important;
    padding-bottom: 3rem !important;
}
.setta-brand {
    width: 100% !important;
    min-height: 128px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #ffffff !important;
    border: 1px solid #e5e8ee !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(24, 39, 75, 0.08) !important;
    box-sizing: border-box !important;
    margin: 0 0 2.55rem 0 !important;
    padding: 1.1rem 2rem !important;
}
.setta-brand-logo {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.setta-brand-logo img {
    display: block !important;
    width: auto !important;
    height: auto !important;
    max-width: 205px !important;
    max-height: 86px !important;
    object-fit: contain !important;
    margin: 0 !important;
}
.app-title {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 2.55rem !important;
    line-height: 1.08 !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: #050505 !important;
}
.app-subtitle {
    margin-top: 0.72rem !important;
    margin-bottom: 0 !important;
    font-size: 0.94rem !important;
    color: #4f5661 !important;
}
.app-info {
    margin: 1.05rem 0 1.65rem 0 !important;
    padding: 1rem 1.05rem !important;
    background: #dce8f9 !important;
    color: #1457b6 !important;
    border-radius: 9px !important;
    font-size: 0.98rem !important;
    line-height: 1.35 !important;
}
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e8ebf0 !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.6rem !important;
}
div[data-testid="stFileUploader"] section {
    border-radius: 10px !important;
}
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e7eaf0 !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
}
div.stButton > button[kind="primary"],
div.stDownloadButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
}
@media (max-width: 900px) {
    .block-container {
        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .setta-brand {
        min-height: 105px !important;
        margin-bottom: 1.8rem !important;
    }
    .setta-brand-logo img {
        max-width: 170px !important;
        max-height: 72px !important;
    }
    .app-title {
        font-size: 2rem !important;
    }
}
</style>
""", unsafe_allow_html=True)
# === END VISUAL CONFIG SETTA V1 ==='''

_replace_once(_visual_anchor, _visual_replacement, "padronização visual com Conversor MRP")

_main_title_anchor = '''st.title(UI_CONFIG["section_main_title"])
if UI_CONFIG.get("section_main_description"):
    st.markdown(f'<div class="setta-main-description">{UI_CONFIG["section_main_description"]}</div>', unsafe_allow_html=True)'''

_main_title_replacement = '''st.markdown(f'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>', unsafe_allow_html=True)
if UI_CONFIG.get("section_main_description"):
    st.markdown(f'<p class="app-subtitle">{UI_CONFIG["section_main_description"]}</p>', unsafe_allow_html=True)
if UI_CONFIG.get("main_notice"):
    st.markdown(f'<div class="app-info">{UI_CONFIG["main_notice"]}</div>', unsafe_allow_html=True)'''

_replace_once(_main_title_anchor, _main_title_replacement, "título e aviso principal padronizados")
_replace_once('    st.info(UI_CONFIG["main_notice"])\n', '', "remoção do aviso duplicado")


# =========================================================
# ADEQUAÇÃO 15/09/2026 — RELATORIO GERAL TRATADO
# B Projeto | C Código | E Última Solicitação | H Pendência
# M Data MRP | N Data CM | O Condição | P Semana Necessidade
# S Vinculação da Data
# =========================================================
_old_rg = '''    gr=pd.read_excel(BytesIO(gb),sheet_name="RelatorioTratado"); rg=pd.DataFrame({"Código":num(gr.iloc[:,2]),"Pendência":num(gr.iloc[:,6]).fillna(0),"Data Solicitação":pd.to_datetime(gr.iloc[:,3],errors="coerce",dayfirst=True),"Semana":num(gr.iloc[:,13]),"Projeto":gr.iloc[:,1].fillna("").astype(str).str.strip(),"Data CM":pd.to_datetime(gr.iloc[:,12],errors="coerce",dayfirst=True)}).dropna(subset=["Código"]); rg["Código"]=rg["Código"].astype("int64"); rg_mrp=rg[rg["Semana"].notna()&rg["Semana"].between(1,53)].copy(); rg_mrp["Semana"]=rg_mrp["Semana"].astype("int64")'''

_new_rg = '''    gr=pd.read_excel(BytesIO(gb),sheet_name="RelatorioTratado")
    if gr.shape[1]<=18: raise ValueError("A base RelatorioGeral_Tratado não possui até a coluna S na estrutura esperada.")
    rg=pd.DataFrame({
        "Código":num(gr.iloc[:,2]),
        "Pendência":num(gr.iloc[:,7]).fillna(0),
        "Data Solicitação":pd.to_datetime(gr.iloc[:,4],errors="coerce",dayfirst=True),
        "Data MRP":pd.to_datetime(gr.iloc[:,12],errors="coerce",dayfirst=True),
        "Data CM":pd.to_datetime(gr.iloc[:,13],errors="coerce",dayfirst=True),
        "Condição":gr.iloc[:,14].fillna("").astype(str).str.strip(),
        "Semana":num(gr.iloc[:,15]),
        "Projeto":gr.iloc[:,1].fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.strip(),
        "Vinculação da Data":gr.iloc[:,18].fillna("").astype(str).str.strip(),
    }).dropna(subset=["Código"])
    rg["Código"]=rg["Código"].astype("int64")
    rg_mrp=rg[rg["Semana"].notna()&rg["Semana"].between(1,53)].copy()
    rg_mrp["Semana"]=rg_mrp["Semana"].astype("int64")'''

_replace_once(_old_rg, _new_rg, "nova estrutura do RelatorioGeral_Tratado")

_replace_once(
    'fonte_semana="RelatorioGeral_Tratado — coluna N"',
    'fonte_semana="RelatorioGeral_Tratado — coluna P"',
    "fonte da semana atual",
)


# =========================================================
# CORREÇÃO — DEMANDA GERAL E PROJEÇÃO SEMANAL
# Projetos CANCELADO/SUSPENSO/RESÍDUO permanecem no detalhe,
# mas não podem compor Demanda S.A. nem projeção semanal.
# =========================================================
_sa_week_anchor = 'sa_week=rg_mrp.groupby(["Código","Semana"],as_index=False)["Pendência"].sum().rename(columns={"Pendência":"Demanda S.A."})'
_sa_week_replacement = '''try:
    _tratativas_demanda_geral=_carregar_tratativas_salvas()
except Exception as _trat_geral_err:
    st.error(f"Não foi possível carregar as tratativas para cálculo da Demanda Geral: {_trat_geral_err}")
    st.stop()

_tratativa_demanda_map=(
    _tratativas_demanda_geral.set_index("Projeto")["OBS"].to_dict()
    if len(_tratativas_demanda_geral) else {}
)
rg_mrp_efetivo=rg_mrp.copy()
rg_mrp_efetivo["Projeto"]=rg_mrp_efetivo["Projeto"].map(_projeto_key)
rg_mrp_efetivo["OBS Tratativa"]=rg_mrp_efetivo["Projeto"].map(_tratativa_demanda_map).fillna("")
_condicao_desconsiderada=rg_mrp_efetivo["Condição"].map(_texto_normalizado).isin({"CANCELADO","SUSPENSO"})
_residuo_desconsiderado=rg_mrp_efetivo["OBS Tratativa"].map(_texto_normalizado).eq("RESIDUO")
rg_mrp_efetivo.loc[_condicao_desconsiderada|_residuo_desconsiderado,"Pendência"]=0.0
sa_week=rg_mrp_efetivo.groupby(["Código","Semana"],as_index=False)["Pendência"].sum().rename(columns={"Pendência":"Demanda S.A."})'''
_replace_once(_sa_week_anchor, _sa_week_replacement, "Demanda S.A. líquida de projetos desconsiderados")


# =========================================================
# DEMANDA POR PROJETO + TRATATIVAS PERSISTENTES
# =========================================================
_demanda_pattern = (
    r'ultima_solicitacao=rg\.groupby\(\["Projeto","Código"\],as_index=False\)\["Data Solicitação"\]\.max\(\).*?'
    r'demanda_projeto=calcular_demanda_projeto\(demanda_projeto_base\)'
)

_demanda_replacement = '''try:
    tratativas_projeto=_carregar_tratativas_salvas()
except Exception as e:
    st.error(f"Não foi possível carregar as tratativas de projetos salvas: {e}")
    st.stop()
tratativa_map=tratativas_projeto.set_index("Projeto")["OBS"].to_dict() if len(tratativas_projeto) else {}

ultima_solicitacao=rg.groupby(["Projeto","Código"],as_index=False)["Data Solicitação"].max().rename(columns={"Código":"Produto","Data Solicitação":"Última Solicitação"})
ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)

demanda_projeto_base=rg_mrp[(~rg_mrp["Código"].isin(codigos_ii))&rg_mrp["Pendência"].ne(0)].copy()
demanda_projeto_base=demanda_projeto_base[["Projeto","Código","Pendência","Semana","Data CM","Condição","Vinculação da Data"]].rename(columns={"Código":"Produto","Pendência":"Necessidade","Semana":"Semana de Necessidade"})
demanda_projeto_base=demanda_projeto_base.merge(cad[["Código","Descrição"]].rename(columns={"Código":"Produto"}),on="Produto",how="left")
demanda_projeto_base=demanda_projeto_base.merge(ultima_solicitacao,on=["Projeto","Produto"],how="left")
demanda_projeto_base["Projeto"]=demanda_projeto_base["Projeto"].map(_projeto_key)
demanda_projeto_base["_DataCM"]=pd.to_datetime(demanda_projeto_base["Data CM"],errors="coerce",dayfirst=True)
demanda_projeto_base["Data CM"]=demanda_projeto_base["_DataCM"].apply(lambda x:formatar_data_br(x) if pd.notna(x) else "NI")
demanda_projeto_base["Última Solicitação"]=demanda_projeto_base["Última Solicitação"].fillna("NI")
demanda_projeto_base["Condição"]=demanda_projeto_base["Condição"].fillna("").astype(str).str.strip()
demanda_projeto_base["Vinculação da Data"]=demanda_projeto_base["Vinculação da Data"].fillna("").astype(str).str.strip()
demanda_projeto_base["OBS Tratativa"]=demanda_projeto_base["Projeto"].map(tratativa_map).fillna("")
demanda_projeto_base["Pendência Original"]=pd.to_numeric(demanda_projeto_base["Necessidade"],errors="coerce").fillna(0.0)

def _condicao_resumo(condicao):
    c=_texto_normalizado(condicao)
    if c in {"NORMAL","FINALIZADO","CANCELADO","SUSPENSO"}:
        return c
    return "NÃO INFORMADO"

def _montar_resumo(row):
    partes=[]
    vinculacao=str(row.get("Vinculação da Data","") or "").strip()
    partes.append(vinculacao if vinculacao else "NÃO INFORMADO")
    partes.append("CM OK" if pd.notna(row.get("_DataCM")) else "CM N")
    partes.append(_condicao_resumo(row.get("Condição","")))
    obs=str(row.get("OBS Tratativa","") or "").strip()
    if obs:
        partes.append("RESÍDUO" if _texto_normalizado(obs)=="RESIDUO" else obs)
    return " | ".join(partes)

demanda_projeto_base["Resumo"]=demanda_projeto_base.apply(_montar_resumo,axis=1)
cond_zerar=demanda_projeto_base["Condição"].map(_texto_normalizado).isin({"CANCELADO","SUSPENSO"})
residuo_zerar=demanda_projeto_base["OBS Tratativa"].map(_texto_normalizado).eq("RESIDUO")
demanda_projeto_base.loc[cond_zerar|residuo_zerar,"Necessidade"]=0.0
demanda_projeto_base=demanda_projeto_base.sort_values(["Produto","Semana de Necessidade","_DataCM","Projeto"],na_position="last").reset_index(drop=True)

pre_nota_map=cp.groupby("Código")["Saldo em Pré Nota"].max().to_dict()
stock_pool=est.set_index("Código")["Saldo em Estoque"].to_dict()

def calcular_demanda_projeto(df):
    cols=["Projeto","Produto","Descrição","Última Solicitação","Data CM","Semana de Necessidade","Semana de Atendimento","Necessidade","Estoque","Pré Nota","P.C.","Fabricação","S.C.","Ação","Resumo"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    out=[]
    for code,rows in df.groupby("Produto",sort=False):
        rows=rows.sort_values(["Semana de Necessidade","_DataCM","Projeto"],na_position="last").copy()
        estoque_restante=float(stock_pool.get(int(code),0.0))
        pc_pool=[{"qty":float(r["Quantidade P.C."]),"week":r["Semana P.C."]} for _,r in cp[(cp["Código"]==int(code))&(cp["Quantidade P.C."]>0)].sort_values("Semana P.C.",na_position="last").iterrows()]
        fab_pool=[{"qty":1.0,"week":r["Semana Entrega"]} for _,r in op[op["Código Produto"]==int(code)].sort_values("Semana Entrega",na_position="last").iterrows()]
        sc_pool=[{"qty":float(r["Quantidade S.C."]),"week":r["Semana S.C."]} for _,r in cp[(cp["Código"]==int(code))&(cp["Quantidade S.C."]>0)].sort_values("Semana S.C.",na_position="last").iterrows()]

        for _,r in rows.iterrows():
            necessidade=float(r["Necessidade"])
            pendencia_original=float(r.get("Pendência Original",necessidade))
            restante=necessidade
            saldo_estoque_inicial=estoque_restante
            pc_inicial=sum(item["qty"] for item in pc_pool)
            fab_inicial=sum(item["qty"] for item in fab_pool)
            sc_inicial=sum(item["qty"] for item in sc_pool)
            ultima_semana=None
            acoes=[]
            cond=_texto_normalizado(r.get("Condição",""))
            obs_norm=_texto_normalizado(r.get("OBS Tratativa",""))

            if necessidade<=1e-9 and pendencia_original>1e-9 and obs_norm=="RESIDUO":
                acoes=[f"RESÍDUO {pendencia_original:g}"]
                semana_atendimento="N/A"
            elif necessidade<=1e-9 and pendencia_original>1e-9 and cond in {"CANCELADO","SUSPENSO"}:
                acoes=[f"{cond} {pendencia_original:g}"]
                semana_atendimento="N/A"
            else:
                if restante>1e-9 and estoque_restante>1e-9:
                    take=min(restante,estoque_restante)
                    estoque_restante-=take
                    restante-=take
                    ultima_semana=semana_atual
                    acoes.append(f"Estoque {take:g}")

                for pool,label in [(pc_pool,"P.C."),(fab_pool,"Fabricação"),(sc_pool,"S.C.")]:
                    while restante>1e-9 and pool:
                        item=pool[0]
                        if item["qty"]<=1e-9:
                            pool.pop(0)
                            continue
                        take=min(restante,item["qty"])
                        item["qty"]-=take
                        restante-=take
                        ultima_semana=item["week"] if pd.notna(item["week"]) and float(item["week"])>0 else None
                        semana_txt=str(int(float(item["week"]))) if pd.notna(item["week"]) and float(item["week"])>0 else "a definir"
                        acoes.append(f"{label} {take:g} (sem. {semana_txt})")
                        if item["qty"]<=1e-9:
                            pool.pop(0)

                if restante>1e-9:
                    semana_criacao=int(r["Semana de Necessidade"])
                    acoes.append(f"CRIAR S.C. {restante:g} para semana {semana_criacao}")
                    semana_atendimento="NN"
                else:
                    semana_atendimento="A definir" if ultima_semana is None else str(int(float(ultima_semana)))

            out.append({
                "Projeto":r["Projeto"],
                "Produto":int(code),
                "Descrição":r["Descrição"],
                "Última Solicitação":r["Última Solicitação"],
                "Data CM":r["Data CM"],
                "Semana de Necessidade":int(r["Semana de Necessidade"]),
                "Semana de Atendimento":semana_atendimento,
                "Necessidade":necessidade,
                "Estoque":saldo_estoque_inicial,
                "Pré Nota":float(pre_nota_map.get(int(code),0.0)),
                "P.C.":pc_inicial,
                "Fabricação":fab_inicial,
                "S.C.":sc_inicial,
                "Ação":"; ".join(acoes) if acoes else "OK",
                "Resumo":r["Resumo"],
                "_DataCM":r.get("_DataCM")
            })

    result=pd.DataFrame(out).sort_values(["Produto","Semana de Necessidade","_DataCM","Projeto"],na_position="last").reset_index(drop=True)
    return result[cols]

demanda_projeto=calcular_demanda_projeto(demanda_projeto_base)'''

_sub_once(_demanda_pattern, _demanda_replacement, "Demanda por Projeto e tratativas persistentes", flags=re.S)

_replace_once(
    'DEM_COLS = ["Projeto", "Produto", "Descrição", "Última Solicitação", "Data CM", "Semana de Necessidade", "Semana de Atendimento", "Necessidade", "Estoque", "Pré Nota", "P.C.", "Fabricação", "S.C.", "Ação"]',
    'DEM_COLS = ["Projeto", "Produto", "Descrição", "Última Solicitação", "Data CM", "Semana de Necessidade", "Semana de Atendimento", "Necessidade", "Estoque", "Pré Nota", "P.C.", "Fabricação", "S.C.", "Ação", "Resumo"]',
    "coluna Resumo na consulta",
)


# =========================================================
# TRATATIVA COMO TERCEIRA ABA — CONSULTA E PROCESSAMENTO
# =========================================================
_replace_once(
    'tab_geral, tab_projeto = st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"]])',
    'tab_geral, tab_projeto, tab_tratativa = st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])',
    "aba de tratativas na consulta",
)

_consulta_export_anchor = '    st.markdown("### Exportação de relatórios")'
_consulta_export_replacement = '''    with tab_tratativa:
        render_tratativa_projetos()

    st.markdown("### Exportação de relatórios")'''
_replace_once(_consulta_export_anchor, _consulta_export_replacement, "conteúdo da tratativa na consulta")

_replace_once(
    'tab1,tab2=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"]])',
    'tab1,tab2,tab3=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])',
    "aba de tratativas no processamento",
)

_tratativa_anchor = '    st.dataframe(d,use_container_width=True,height=600,hide_index=True)\nst.divider(); st.subheader(UI_CONFIG["section_export_title"])'
_tratativa_block = '''    st.dataframe(d,use_container_width=True,height=600,hide_index=True)
with tab3:
    render_tratativa_projetos()
st.divider(); st.subheader(UI_CONFIG["section_export_title"])'''
_replace_once(_tratativa_anchor, _tratativa_block, "conteúdo da aba Tratativa de Projetos")


# =========================================================
# SNAPSHOT E EXPORTAÇÃO CONSIDERAM AS TRATATIVAS SALVAS
# =========================================================
_replace_once(
    'b"".join([f.getvalue() for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]])',
    'b"".join([f.getvalue() for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]]) + json.dumps(tratativas_projeto[["Projeto","OBS"]].sort_values("Projeto").to_dict("records"),ensure_ascii=False,sort_keys=True).encode("utf-8")',
    "hash das tratativas persistentes",
)

_replace_once(
    'sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"Compra_MRP":compras_mrp_export,"Compras":cp,"Fabricacao":fab_det,"Cadastro_Base":cad}',
    'sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"Tratativas_Projetos":tratativas_projeto,"Compra_MRP":compras_mrp_export,"Compras":cp,"Fabricacao":fab_det,"Cadastro_Base":cad}',
    "tratativas na exportação completa",
)

# Formatação brasileira da data/hora exibida nas tratativas salvas.
_source = _source.replace(
    '    out["Atualizado em"]=out["updated_at"].fillna("").astype(str)\n',
    '    _dt_tratativa=pd.to_datetime(out["updated_at"],errors="coerce",utc=True)\n    _dt_tratativa=_dt_tratativa.dt.tz_convert("America/Sao_Paulo")\n    out["Atualizado em"]=_dt_tratativa.dt.strftime("%d/%m/%Y %H:%M").fillna("")\n',
    1,
)

exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())
