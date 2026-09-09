import streamlit as st
import pandas as pd
import requests
import json
import hashlib
import re
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import date, timedelta

st.set_page_config(page_title="MRP | SETTA", page_icon="📦", layout="wide")

def num(s): return pd.to_numeric(s, errors="coerce")
def col_by_pos(df,pos,name):
    if df.shape[1]<=pos: raise ValueError(f"A base MRP_TC_TP não possui a coluna {name} na posição esperada.")
    df[name]=num(df.iloc[:,pos])
def excel_bytes(sheets):
    bio=BytesIO()
    with pd.ExcelWriter(bio,engine="openpyxl") as writer:
        for name,df in sheets.items(): df.to_excel(writer,sheet_name=name[:31],index=False)
    bio.seek(0); return bio.getvalue()
def csv_bytes(df): return df.to_csv(index=False,sep=";",decimal=",").encode("utf-8-sig")
def normalizar_compra_mrp(df):
    """Formato oficial da Compra MRP, identico no ADMIN e no CONSULTA."""
    cols=["produto","qnt","data","psy","cc","op","obs","prioridade"]
    out=df.copy() if df is not None else pd.DataFrame()
    for c in cols:
        if c not in out.columns: out[c]=""
    if "produto" in out.columns:
        def fmt_produto(x):
            if pd.isna(x) or str(x).strip()=="": return ""
            txt=str(x).strip()
            try:
                txt=str(int(float(txt)))
            except Exception:
                pass
            return txt.zfill(8)
        out["produto"]=out["produto"].apply(fmt_produto)
    if "qnt" in out.columns:
        out["qnt"]=pd.to_numeric(out["qnt"],errors="coerce").fillna(0)
        out["qnt"]=out["qnt"].apply(lambda x:int(x) if float(x).is_integer() else float(x))
    if "data" in out.columns:
        out["data"]=out["data"].apply(formatar_data_br)
    for c in ["psy","cc","op","obs","prioridade"]:
        out[c]=out[c].fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.strip()
    return out[cols].reset_index(drop=True)

def zip_bytes(files):
    bio=BytesIO()
    with ZipFile(bio,"w",ZIP_DEFLATED) as z:
        for name,data in files.items(): z.writestr(name,data)
    bio.seek(0); return bio.getvalue()
def periodo_semana(semana,ano=2026):
    try: semana=int(semana)
    except (TypeError,ValueError): return ""
    if not 1<=semana<=53: return ""
    primeiro_domingo=date(ano,1,1); primeiro_domingo+=timedelta(days=(6-primeiro_domingo.weekday())%7); inicio=primeiro_domingo+timedelta(weeks=semana-1); fim=inicio+timedelta(days=6); return f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
def ultimo_dia_util_semana(semana,ano=2026):
    try: semana=int(semana)
    except (TypeError,ValueError): return ""
    if not 1<=semana<=53: return ""
    primeiro_domingo=date(ano,1,1); primeiro_domingo+=timedelta(days=(6-primeiro_domingo.weekday())%7); sexta=primeiro_domingo+timedelta(weeks=semana-1,days=5); return sexta.strftime('%d/%m/%Y')
def formatar_data_br(s):
    dt=pd.to_datetime(s,errors="coerce",dayfirst=True); return "" if pd.isna(dt) else dt.strftime("%d/%m/%Y")

# =========================================================
# HISTÓRICO COMPARTILHADO DO MRP — SUPABASE
# Guarda somente os resultados finais do MRP, nunca as planilhas-base.
# =========================================================
SUPABASE_URL="https://cuixazpxkvniqldmmnth.supabase.co"
SUPABASE_KEY="sb_publishable_ZTqIgmA9Ez6AVQsoXa0P8Q_6CYHDFye"

# =========================================================
# AUTENTICAÇÃO E PERFIS — SUPABASE AUTH
# ADMIN = pode carregar/processar/salvar MRP
# CONSULTA = somente consulta/histórico
# =========================================================
def _auth_headers(token=None):
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {token or SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def _login_supabase(email, password):
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=20,
    )
    if r.status_code >= 400:
        try: msg = r.json().get("error_description") or r.json().get("msg") or "Login inválido"
        except Exception: msg = "Login inválido"
        raise ValueError(msg)
    return r.json()

def _load_my_role(access_token, user_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/user_roles",
        headers=_auth_headers(access_token),
        params={"select":"user_id,nome,role", "user_id":f"eq.{user_id}", "limit":"1"},
        timeout=20,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None

def _logout():
    for k in ["auth_access_token", "auth_refresh_token", "auth_user_id", "auth_email", "auth_nome", "auth_role"]:
        st.session_state.pop(k, None)
    st.rerun()

def _require_login():
    if st.session_state.get("auth_access_token") and st.session_state.get("auth_role") in {"ADMIN", "CONSULTA"}:
        return True
    st.title("MRP — SETTA")
    st.subheader("Acesso ao sistema")
    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("ENTRAR", use_container_width=True)
    if entrar:
        usuario = usuario.strip().lower()
        email_map = {
            "almoxsetta": "almoxarifado.energy@gruposetta.com",
            "consulta": "consulta.mrp@gruposetta.com",
        }
        email = email_map.get(usuario, usuario)
        if not usuario or not password:
            st.error("Informe usuário e senha.")
        else:
            try:
                auth = _login_supabase(email, password)
                user = auth.get("user") or {}
                token = auth.get("access_token")
                role = _load_my_role(token, user.get("id")) if token and user.get("id") else None
                if not role or role.get("role") not in {"ADMIN", "CONSULTA"}:
                    st.error("Usuário autenticado, mas sem perfil autorizado no MRP.")
                else:
                    st.session_state["auth_access_token"] = token
                    st.session_state["auth_refresh_token"] = auth.get("refresh_token")
                    st.session_state["auth_user_id"] = user.get("id")
                    st.session_state["auth_email"] = user.get("email", email.strip())
                    st.session_state["auth_nome"] = role.get("nome") or user.get("email", "")
                    st.session_state["auth_role"] = role.get("role")
                    st.rerun()
            except Exception as e:
                st.error(f"Não foi possível entrar: {e}")
    return False

if not _require_login():
    st.stop()

def _sb_headers():
    token = st.session_state.get("auth_access_token") or SUPABASE_KEY
    return _auth_headers(token)

def _refresh_supabase_session():
    refresh_token = st.session_state.get("auth_refresh_token")
    if not refresh_token:
        return False
    try:
        r = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
            json={"refresh_token": refresh_token},
            timeout=20,
        )
        if r.status_code >= 400:
            return False
        auth = r.json()
        if not auth.get("access_token"):
            return False
        st.session_state["auth_access_token"] = auth.get("access_token")
        if auth.get("refresh_token"):
            st.session_state["auth_refresh_token"] = auth.get("refresh_token")
        return True
    except Exception:
        return False

def _sb_get(params=None):
    r=requests.get(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers=_sb_headers(),params=params or {},timeout=20)
    if r.status_code == 401 and _refresh_supabase_session():
        r=requests.get(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers=_sb_headers(),params=params or {},timeout=20)
    r.raise_for_status(); return r.json()

def _sb_post(payload):
    r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)
    if r.status_code == 401 and _refresh_supabase_session():
        r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)
    r.raise_for_status(); return r.json()

# === VISUAL CONFIG SETTA V1 ===
DEFAULT_UI_CONFIG = {
    "logo_data": "",
    "logo_width": 220,
    "app_title": "MRP | SETTA",
    "objective": "Planejamento de necessidades de materiais e acompanhamento da demanda.",
    "title_demanda_geral": "DEMANDA GERAL",
    "title_demanda_projeto": "DEMANDA POR PROJETO",
    "color_primary": "#1F4E78",
    "color_title": "#1F4E78",
    "color_header": "#FFFFFF",
    "color_background": "#F5F7FA",
    "color_text": "#1F2937",
}


def _config_get():
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/mrp_app_config",
            headers=_sb_headers(),
            params={"select":"*", "id":"eq.1", "limit":"1"},
            timeout=20,
        )
        if r.status_code == 401 and _refresh_supabase_session():
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/mrp_app_config",
                headers=_sb_headers(),
                params={"select":"*", "id":"eq.1", "limit":"1"},
                timeout=20,
            )
        r.raise_for_status()
        rows = r.json()
        if rows:
            cfg = {**DEFAULT_UI_CONFIG, **rows[0]}
            return cfg
    except Exception as e:
        st.session_state["ui_config_error"] = str(e)
    return DEFAULT_UI_CONFIG.copy()


def _config_save(cfg):
    payload = {k: cfg.get(k, DEFAULT_UI_CONFIG[k]) for k in DEFAULT_UI_CONFIG}
    payload["updated_at"] = pd.Timestamp.utcnow().isoformat()
    payload["updated_by"] = st.session_state.get("auth_nome", "")
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/mrp_app_config",
        headers={**_sb_headers(), "Prefer":"return=representation"},
        params={"id":"eq.1"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _hex_ok(value, fallback):
    value = str(value or "").strip()
    return value if re.fullmatch(r"#[0-9A-Fa-f]{6}", value) else fallback


def _render_visual_settings(cfg):
    if st.session_state.get("auth_role") != "ADMIN":
        return
    with st.sidebar.expander("CONFIGURAÇÃO VISUAL", expanded=False):
        st.caption("As alterações são salvas no banco compartilhado e aparecem para todos os usuários.")
        logo = st.file_uploader("Cabeçalho / logotipo da empresa", type=["png", "jpg", "jpeg", "webp"], key="ui_logo_upload")
        if cfg.get("logo_data"):
            st.image(cfg["logo_data"], width=int(cfg.get("logo_width") or 220))
            remover_logo = st.checkbox("Remover cabeçalho atual", key="ui_remove_logo")
        else:
            remover_logo = False

        logo_width = st.slider("Largura do cabeçalho", min_value=120, max_value=900, value=max(120, min(900, int(cfg.get("logo_width") or 220))), step=10)
        app_title = st.text_input("Título principal", value=str(cfg.get("app_title") or DEFAULT_UI_CONFIG["app_title"]), key="ui_app_title")
        objective = st.text_area("Objetivo do aplicativo", value=str(cfg.get("objective") or DEFAULT_UI_CONFIG["objective"]), height=90, key="ui_objective")
        title_geral = st.text_input("Título — Demanda Geral", value=str(cfg.get("title_demanda_geral") or DEFAULT_UI_CONFIG["title_demanda_geral"]), key="ui_title_geral")
        title_projeto = st.text_input("Título — Demanda por Projeto", value=str(cfg.get("title_demanda_projeto") or DEFAULT_UI_CONFIG["title_demanda_projeto"]), key="ui_title_projeto")
        color_primary = st.color_picker("Cor principal", value=_hex_ok(cfg.get("color_primary"), DEFAULT_UI_CONFIG["color_primary"]), key="ui_color_primary")
        color_title = st.color_picker("Cor dos títulos", value=_hex_ok(cfg.get("color_title"), DEFAULT_UI_CONFIG["color_title"]), key="ui_color_title")
        color_header = st.color_picker("Cor do cabeçalho", value=_hex_ok(cfg.get("color_header"), DEFAULT_UI_CONFIG["color_header"]), key="ui_color_header")
        color_background = st.color_picker("Cor de fundo", value=_hex_ok(cfg.get("color_background"), DEFAULT_UI_CONFIG["color_background"]), key="ui_color_background")
        color_text = st.color_picker("Cor do texto", value=_hex_ok(cfg.get("color_text"), DEFAULT_UI_CONFIG["color_text"]), key="ui_color_text")

        if st.button("SALVAR CONFIGURAÇÃO", use_container_width=True, type="primary", key="save_ui_config"):
            new_cfg = {
                **cfg,
                "logo_data": "" if remover_logo else cfg.get("logo_data", ""),
                "logo_width": logo_width,
                "app_title": app_title.strip() or DEFAULT_UI_CONFIG["app_title"],
                "objective": objective.strip() or DEFAULT_UI_CONFIG["objective"],
                "title_demanda_geral": title_geral.strip() or DEFAULT_UI_CONFIG["title_demanda_geral"],
                "title_demanda_projeto": title_projeto.strip() or DEFAULT_UI_CONFIG["title_demanda_projeto"],
                "color_primary": color_primary,
                "color_title": color_title,
                "color_header": color_header,
                "color_background": color_background,
                "color_text": color_text,
            }
            if logo is not None:
                import base64
                mime = logo.type or "image/png"
                new_cfg["logo_data"] = f"data:{mime};base64,{base64.b64encode(logo.getvalue()).decode('ascii')}"
            try:
                _config_save(new_cfg)
                st.session_state["ui_config"] = _config_get()
                st.success("Configuração visual salva.")
                st.rerun()
            except Exception as e:
                st.error(f"Não foi possível salvar a configuração visual: {e}")


def _apply_visual_theme(cfg):
    primary = _hex_ok(cfg.get("color_primary"), DEFAULT_UI_CONFIG["color_primary"])
    title = _hex_ok(cfg.get("color_title"), DEFAULT_UI_CONFIG["color_title"])
    header = _hex_ok(cfg.get("color_header"), DEFAULT_UI_CONFIG["color_header"])
    background = _hex_ok(cfg.get("color_background"), DEFAULT_UI_CONFIG["color_background"])
    text = _hex_ok(cfg.get("color_text"), DEFAULT_UI_CONFIG["color_text"])
    st.markdown(f"""
    <style>
      :root {{
        --setta-primary: {primary};
        --setta-title: {title};
        --setta-header: {header};
        --setta-background: {background};
        --setta-text: {text};
      }}
      .stApp {{ background: var(--setta-background); color: var(--setta-text); }}
      h1, h2, h3, h4, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{ color: var(--setta-title) !important; }}
      [data-testid="stHeader"] {{ background: var(--setta-header) !important; }}
      [data-testid="stSidebar"] {{ border-right: 1px solid rgba(0,0,0,.08); }}
      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 22px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); }}
      .setta-brand-title {{ color: var(--setta-title); font-size: 2rem; font-weight: 750; line-height: 1.15; margin: 0; }}
      .setta-brand-objective {{ color: var(--setta-text); font-size: 1rem; line-height: 1.5; margin-top: 6px; opacity: .82; }}
      .setta-brand img {{ display: block; max-width: 100%; height: auto; margin-bottom: 12px; }}
      div.stButton > button[kind="primary"], div.stDownloadButton > button {{ background: var(--setta-primary) !important; border-color: var(--setta-primary) !important; color: #fff !important; }}
      div[data-baseweb="tab-list"] button[aria-selected="true"] {{ color: var(--setta-primary) !important; border-bottom-color: var(--setta-primary) !important; }}
      div[data-testid="stMetricValue"] {{ color: var(--setta-primary); }}
    </style>
    """, unsafe_allow_html=True)


def _render_brand_header(cfg):
    title = str(cfg.get("app_title") or DEFAULT_UI_CONFIG["app_title"])
    objective = str(cfg.get("objective") or "")
    logo = cfg.get("logo_data") or ""
    width = max(120, min(900, int(cfg.get("logo_width") or 220)))
    logo_html = f'<img src="{logo}" style="width:{width}px;" />' if logo else ""
    st.markdown(f'<div class="setta-brand">{logo_html}<div class="setta-brand-title">{title}</div><div class="setta-brand-objective">{objective}</div></div>', unsafe_allow_html=True)


UI_CONFIG = _config_get()
st.session_state["ui_config"] = UI_CONFIG
_apply_visual_theme(UI_CONFIG)
_render_visual_settings(UI_CONFIG)
_render_brand_header(UI_CONFIG)
# === END VISUAL CONFIG SETTA V1 ===

def snapshot_df(snap,key): return pd.DataFrame(snap.get(key) or [])

def load_latest_snapshot():
    rows=_sb_get({"select":"*","order":"created_at.desc","limit":"1"})
    return rows[0] if rows else None

def load_snapshot_history(limit=50):
    return _sb_get({"select":"id,created_at,semana_mrp,usuario","order":"created_at.desc","limit":str(limit)})

def load_snapshot(snapshot_id):
    rows=_sb_get({"select":"*","id":f"eq.{int(snapshot_id)}","limit":"1"})
    return rows[0] if rows else None

def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):
    def records(df):
        if df is None or df.empty: return []
        return json.loads(df.to_json(orient="records",force_ascii=False,date_format="iso"))
    payload={"semana_mrp":int(semana) if semana is not None else None,"usuario":usuario or "Não informado","mrp_geral":records(mrp_geral),"projecao_semanal":records(projecao_semanal),"demanda_projeto":records(demanda_projeto),"compra_mrp":records(compra_mrp),"compras":records(compras)}
    return _sb_post(payload)

def compare_mrp_general(old,new):
    a=snapshot_df(old,"mrp_geral").copy(); b=snapshot_df(new,"mrp_geral").copy()
    if a.empty and b.empty: return pd.DataFrame()
    for d in (a,b):
        if "Código" in d: d["Código"]=pd.to_numeric(d["Código"],errors="coerce").fillna(0).astype(int)
    a=a.set_index("Código") if "Código" in a else pd.DataFrame(); b=b.set_index("Código") if "Código" in b else pd.DataFrame()
    codes=sorted(set(a.index.tolist())|set(b.index.tolist())); numeric=["Saldo em Estoque","Demanda","P.C.","S.C.","Produzindo","DIV"]; rows=[]
    for code in codes:
        ao=a.loc[code] if code in a.index else None; bo=b.loc[code] if code in b.index else None
        if ao is None: classification="NOVO"
        elif bo is None: classification="REMOVIDO"
        else:
            changed=False
            for c in numeric:
                ov=float(pd.to_numeric(ao.get(c,0),errors="coerce") or 0); nv=float(pd.to_numeric(bo.get(c,0),errors="coerce") or 0)
                if abs(nv-ov)>1e-9: changed=True; break
            if not changed:
                for c in ["Tipo","Status","Semana de Atendimento","Período de Atendimento"]:
                    if str(ao.get(c,""))!=str(bo.get(c,"")): changed=True; break
            classification="ALTERADO" if changed else "SEM ALTERAÇÃO"
            if str(ao.get("Status",""))=="CRIAR S.C." and str(bo.get("Status",""))=="OK": classification="NORMALIZADO"
            elif str(ao.get("Status",""))!="CRIAR S.C." and str(bo.get("Status",""))=="CRIAR S.C.": classification="NOVO S.C."
        base=bo if bo is not None else ao
        row={"Código":int(code),"Descrição":str(base.get("Descrição","")),"Tipo":str(base.get("Tipo","")),"Classificação":classification}
        for c in numeric:
            ov=float(pd.to_numeric(ao.get(c,0),errors="coerce") or 0) if ao is not None else 0.0; nv=float(pd.to_numeric(bo.get(c,0),errors="coerce") or 0) if bo is not None else 0.0
            row[f"{c} anterior"]=ov; row[f"{c} atual"]=nv; row[f"Δ {c}"]=nv-ov
        row["Status anterior"]=str(ao.get("Status","")) if ao is not None else ""; row["Status atual"]=str(bo.get("Status","")) if bo is not None else ""
        row["Atendimento anterior"]=str(ao.get("Semana de Atendimento","")) if ao is not None else ""; row["Atendimento atual"]=str(bo.get("Semana de Atendimento","")) if bo is not None else ""
        rows.append(row)
    return pd.DataFrame(rows)

def compare_simple(old_df,new_df,key_cols):
    a=old_df.copy() if old_df is not None else pd.DataFrame(); b=new_df.copy() if new_df is not None else pd.DataFrame()
    if a.empty and b.empty: return pd.DataFrame()
    for d in (a,b):
        for c in key_cols:
            if c in d: d[c]=d[c].astype(str)
    if a.empty: a=pd.DataFrame(columns=key_cols); 
    if b.empty: b=pd.DataFrame(columns=key_cols)
    a["__key__"]=a[key_cols].astype(str).agg("|".join,axis=1) if len(a) else pd.Series(dtype=str); b["__key__"]=b[key_cols].astype(str).agg("|".join,axis=1) if len(b) else pd.Series(dtype=str)
    ai=a.set_index("__key__",drop=False); bi=b.set_index("__key__",drop=False); keys=sorted(set(ai.index)|set(bi.index)); rows=[]
    for k in keys:
        ao=ai.loc[k] if k in ai.index else None; bo=bi.loc[k] if k in bi.index else None
        if ao is None: cls="NOVO"
        elif bo is None: cls="REMOVIDO"
        else:
            ao2=ao.drop(labels=["__key__"],errors="ignore").to_dict(); bo2=bo.drop(labels=["__key__"],errors="ignore").to_dict(); cls="SEM ALTERAÇÃO" if ao2==bo2 else "ALTERADO"
        base=bo if bo is not None else ao; row={c:base.get(c,"") for c in key_cols}; row["Classificação"]=cls; rows.append(row)
    return pd.DataFrame(rows)

def render_mrp_history():
    st.subheader("Histórico e comparativo de MRP")
    try: history=load_snapshot_history()
    except Exception as e: st.warning(f"Não foi possível acessar o histórico compartilhado: {e}"); return
    if not history: st.info("Ainda não existem MRP salvos no histórico."); return
    labels={int(x["id"]):f"MRP {x['id']} | semana {x.get('semana_mrp') or '-'} | {formatar_data_br(x.get('created_at'))} | {x.get('usuario') or '-'}" for x in history}; ids=list(labels)
    c1,c2=st.columns(2); new_id=c1.selectbox("MRP atual",ids,index=0,format_func=lambda x:labels[x],key="mrp_history_current"); old_ids=[x for x in ids if x!=new_id]
    if not old_ids: st.info("Salve pelo menos dois MRP para gerar um comparativo."); return
    old_id=c2.selectbox("MRP anterior",old_ids,index=0,format_func=lambda x:labels[x],key="mrp_history_previous")
    try:
        old=load_snapshot(old_id); new=load_snapshot(new_id); cmp=compare_mrp_general(old,new)
        k1,k2,k3,k4,k5=st.columns(5); k1.metric("Novo",int((cmp["Classificação"]=="NOVO").sum())); k2.metric("Removido",int((cmp["Classificação"]=="REMOVIDO").sum())); k3.metric("Alterado",int((cmp["Classificação"]=="ALTERADO").sum())); k4.metric("Novo S.C.",int((cmp["Classificação"]=="NOVO S.C.").sum())); k5.metric("Normalizado",int((cmp["Classificação"]=="NORMALIZADO").sum()))
        st.dataframe(cmp,use_container_width=True,hide_index=True)
        proj_cmp=compare_simple(snapshot_df(old,"projecao_semanal"),snapshot_df(new,"projecao_semanal"),["Código","Semana"])
        proj_old=snapshot_df(old,"projecao_semanal"); proj_new=snapshot_df(new,"projecao_semanal")
        dem_cmp=compare_simple(snapshot_df(old,"demanda_projeto"),snapshot_df(new,"demanda_projeto"),["Projeto","Produto","Semana de Necessidade"])
        comp_old=snapshot_df(old,"compra_mrp"); comp_new=snapshot_df(new,"compra_mrp"); comp_cmp=compare_simple(comp_old,comp_new,["produto","op"])
        report={"MRP_Geral_Comparativo":cmp,"Projecao_Comparativo":proj_cmp,"Demanda_Projeto_Comparativo":dem_cmp,"Compras_Comparativo":comp_cmp,"MRP_Anterior":snapshot_df(old,"mrp_geral"),"MRP_Atual":snapshot_df(new,"mrp_geral"),"Compra_Anterior":comp_old,"Compra_Atual":comp_new}
        st.download_button("BAIXAR RELATÓRIO COMPARATIVO",excel_bytes(report),"Comparativo_MRP.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="download_comparativo_mrp")
    except Exception as e: st.error(f"Erro ao gerar o comparativo: {e}")

def render_consulta_view():
    """Visualização CONSULTA: mesma ordem de colunas do ADMIN, sem edição do MRP."""
    try:
        snap = load_latest_snapshot()
    except Exception as e:
        st.error(f"Não foi possível carregar o MRP compartilhado: {e}")
        return
    if not snap:
        st.info("Ainda não existe MRP salvo para consulta.")
        return

    mg = snapshot_df(snap, "mrp_geral").copy()
    proj = snapshot_df(snap, "projecao_semanal").copy()
    dem = snapshot_df(snap, "demanda_projeto").copy()
    comp = normalizar_compra_mrp(snapshot_df(snap, "compra_mrp"))
    compras = snapshot_df(snap, "compras").copy()

    # Espelho do ADMIN: snapshots antigos podem não ter o campo Período da Semana.
    # Nesse caso, reconstruímos exatamente pela mesma regra de semana usada no ADMIN.
    if "Semana" in proj.columns:
        if "Período da Semana" not in proj.columns:
            proj["Período da Semana"] = proj["Semana"].apply(periodo_semana)
        else:
            faltantes = proj["Período da Semana"].isna() | proj["Período da Semana"].astype(str).str.strip().eq("")
            proj.loc[faltantes, "Período da Semana"] = proj.loc[faltantes, "Semana"].apply(periodo_semana)

    # Ordem oficial das colunas: nunca depender da ordem do JSON/Supabase.
    MRP_COLS = ["Código", "Descrição", "Tipo", "Saldo em Estoque", "Demanda", "P.C.", "S.C.", "Produzindo", "DIV", "Status", "Semana de Atendimento", "Período de Atendimento"]
    PROJ_COLS = ["Código", "Descrição", "Tipo", "Semana", "Período da Semana", "Saldo Inicial", "Demanda", "P.C.", "S.C.", "Produzindo", "Resumo Final"]
    DEM_COLS = ["Projeto", "Produto", "Descrição", "Última Solicitação", "Data CM", "Semana de Necessidade", "Semana de Atendimento", "Necessidade", "Estoque", "Pré Nota", "P.C.", "Fabricação", "S.C.", "Ação"]

    def fix_columns(df, columns):
        out = df.copy()
        for c in columns:
            if c not in out.columns:
                out[c] = ""
        return out.loc[:, columns]

    mg = fix_columns(mg, MRP_COLS)
    proj = fix_columns(proj, PROJ_COLS)
    dem = fix_columns(dem, DEM_COLS)

    st.subheader("Consulta do MRP")
    st.caption(f"Último MRP salvo — semana {snap.get('semana_mrp') or '-'} | {formatar_data_br(snap.get('created_at'))} | {snap.get('usuario') or '-'}")

    tab_geral, tab_projeto = st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"]])

    with tab_geral:
        c1, c2, c3, c4 = st.columns(4)
        cods = sorted(mg["Código"].dropna().astype(str).unique().tolist())
        codigo = c1.selectbox("Código", ["Todos"] + cods, key="consulta_codigo")
        descricoes = sorted(mg["Descrição"].fillna("").astype(str).unique().tolist())
        descricao = c2.selectbox("Descrição", ["Todos"] + descricoes, key="consulta_descricao")
        tipos = sorted(mg["Tipo"].fillna("").astype(str).unique().tolist())
        tipo = c3.selectbox("Tipo", ["Todos"] + tipos, key="consulta_tipo")
        status = c4.selectbox("Status", ["Todos"] + sorted(mg["Status"].fillna("").astype(str).unique().tolist()), key="consulta_status")

        f = mg.copy()
        if codigo != "Todos": f = f[f["Código"].astype(str) == codigo]
        if descricao != "Todos": f = f[f["Descrição"].astype(str) == descricao]
        if tipo != "Todos": f = f[f["Tipo"].astype(str) == tipo]
        if status != "Todos": f = f[f["Status"].astype(str) == status]
        f = fix_columns(f, MRP_COLS)
        # Seleção por checkbox/linha: mantém o visualizador igual ao ADMIN e evita
        # um segundo seletor separado para escolher o material.
        selecao = st.dataframe(
            f,
            use_container_width=True,
            hide_index=True,
            column_order=MRP_COLS,
            on_select="rerun",
            selection_mode="single-row",
            key="consulta_mrp_table",
        )

        if not f.empty:
            linhas = getattr(getattr(selecao, "selection", None), "rows", []) or []
            if linhas:
                selecionado = str(f.iloc[linhas[0]]["Código"])
                d_proj = fix_columns(proj[proj["Código"].astype(str) == selecionado], PROJ_COLS)
                d_dem = fix_columns(dem[dem["Produto"].astype(str) == selecionado], DEM_COLS)
                desc = f.loc[f["Código"].astype(str) == selecionado, "Descrição"].iloc[0]
                st.markdown("### Detalhamento do material")
                st.caption(f"Material selecionado: {selecionado} — {desc}")
                st.markdown("**Projeção semanal**")
                st.dataframe(d_proj, use_container_width=True, hide_index=True, column_order=PROJ_COLS)
                st.markdown("**S.A. — projetos que geram a demanda**")
                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)

                d_comp = compras[(compras["Código"].astype(str) == selecionado)].copy() if "Código" in compras.columns else pd.DataFrame()
                if not d_comp.empty:
                    compras_cols = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]
                    for c in compras_cols:
                        if c not in d_comp.columns: d_comp[c] = ""
                    st.markdown("**Compras**")
                    st.dataframe(d_comp[compras_cols], use_container_width=True, hide_index=True, column_order=compras_cols)
                    st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")

    with tab_projeto:
        c1, c2, c3 = st.columns(3)
        projetos = sorted(dem["Projeto"].fillna("").astype(str).unique().tolist())
        produtos = sorted(dem["Produto"].fillna("").astype(str).unique().tolist())
        semanas = sorted([x for x in dem["Semana de Necessidade"].dropna().astype(str).unique().tolist() if x])
        projeto = c1.selectbox("Projeto", ["Todos"] + projetos, key="consulta_projeto")
        produto = c2.selectbox("Produto", ["Todos"] + produtos, key="consulta_produto")
        semana = c3.selectbox("Semana de Necessidade", ["Todas"] + semanas, key="consulta_semana")
        f = dem.copy()
        if projeto != "Todos": f = f[f["Projeto"].astype(str) == projeto]
        if produto != "Todos": f = f[f["Produto"].astype(str) == produto]
        if semana != "Todas": f = f[f["Semana de Necessidade"].astype(str) == semana]
        f = fix_columns(f, DEM_COLS)
        st.dataframe(f, use_container_width=True, hide_index=True, column_order=DEM_COLS)

    st.markdown("### Exportação de relatórios")
    sheets = {
        "MRP_Geral": mg,
        "Projecao_Semanal": proj,
        "Demanda_Projeto": dem,
        "Compra_MRP": comp,
        "Compras": compras,
    }
    c1, c2, c3, c4 = st.columns(4)
    c1.download_button("BAIXAR TODOS — EXCEL", data=excel_bytes(sheets), file_name="MRP_Consulta.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    c2.download_button("BAIXAR TODOS — ZIP/CSV", data=zip_bytes({f"{k}.csv": csv_bytes(v) for k,v in sheets.items()}), file_name="MRP_Consulta_CSV.zip", mime="application/zip", use_container_width=True)
    c3.download_button("BAIXAR MRP GERAL — CSV", data=csv_bytes(mg), file_name="MRP_Geral.csv", mime="text/csv", use_container_width=True)
    compra_excel_consulta = excel_bytes({"Compra_MRP": comp})
    c4.download_button("BAIXAR COMPRA MRP", data=compra_excel_consulta, file_name="Compra_MRP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


def load_sources(cb,eb,gb,pb,mb):
    raw=pd.read_excel(BytesIO(cb),sheet_name="Listagem do Browse",header=None); cad=raw.iloc[2:,[1,2,3]].copy(); cad.columns=["Código","Descrição","Tipo"]; cad["Código"]=num(cad["Código"]); cad=cad.dropna(subset=["Código"]); cad["Código"]=cad["Código"].astype("int64"); cad["Descrição"]=cad["Descrição"].fillna("").astype(str).str.strip(); cad["Tipo"]=cad["Tipo"].fillna("").astype(str).str.strip(); cad=cad.drop_duplicates("Código",keep="first").reset_index(drop=True)
    er=pd.read_excel(BytesIO(eb),sheet_name="EstoqueTratado"); est=pd.DataFrame({"Código":num(er.iloc[:,0]),"Saldo em Estoque":num(er.iloc[:,4]).fillna(0)}).dropna(subset=["Código"]); est["Código"]=est["Código"].astype("int64"); est=est.groupby("Código",as_index=False)["Saldo em Estoque"].sum()
    gr=pd.read_excel(BytesIO(gb),sheet_name="RelatorioTratado"); rg=pd.DataFrame({"Código":num(gr.iloc[:,2]),"Pendência":num(gr.iloc[:,6]).fillna(0),"Data Solicitação":pd.to_datetime(gr.iloc[:,3],errors="coerce",dayfirst=True),"Semana":num(gr.iloc[:,13]),"Projeto":gr.iloc[:,1].fillna("").astype(str).str.strip(),"Data CM":pd.to_datetime(gr.iloc[:,12],errors="coerce",dayfirst=True)}).dropna(subset=["Código"]); rg["Código"]=rg["Código"].astype("int64"); rg_mrp=rg[rg["Semana"].notna()&rg["Semana"].between(1,53)].copy(); rg_mrp["Semana"]=rg_mrp["Semana"].astype("int64")
    cr=pd.read_excel(BytesIO(pb),sheet_name="ComprasTratado");
    if cr.shape[1]<=14: raise ValueError("A base Compras_Tratado não possui a coluna O para o saldo de Pré Nota.")
    cp=pd.DataFrame({"Código":num(cr.iloc[:,0]),"Quantidade S.C.":num(cr.iloc[:,3]).fillna(0),"Semana S.C.":num(cr.iloc[:,5]),"Quantidade P.C.":num(cr.iloc[:,9]).fillna(0),"Semana P.C.":num(cr.iloc[:,11]),"Nº S.C.":cr.iloc[:,2],"Nº P.C.":cr.iloc[:,8],"Saldo em Pré Nota":num(cr.iloc[:,14]).fillna(0)}).dropna(subset=["Código"]); cp["Código"]=cp["Código"].astype("int64")
    for c in ["Nº S.C.","Nº P.C."]: cp[c]=cp[c].fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.strip()
    mt=pd.read_excel(BytesIO(mb),sheet_name="MRP_TC_TP"); col_by_pos(mt,1,"Código Produto"); col_by_pos(mt,4,"Semana Entrega"); col_by_pos(mt,7,"Material"); col_by_pos(mt,9,"Quantidade"); col_by_pos(mt,11,"Semana Necessidade"); mt["Código Produto"]=mt["Código Produto"].fillna(0).astype("int64"); mt["Semana Entrega"]=mt["Semana Entrega"].fillna(0).astype("int64"); mt["Material"]=mt["Material"].fillna(0).astype("int64"); mt["Semana Necessidade"]=mt["Semana Necessidade"].fillna(0).astype("int64"); mt["Quantidade"]=mt["Quantidade"].fillna(0.0); mt["ORDEM DE PRODUÇÃO"]=mt.get("ORDEM DE PRODUÇÃO",pd.Series(mt.index+1,index=mt.index))
    return cad,est,rg,rg_mrp,cp,mt

st.title("MRP — Planejamento de Necessidades de Materiais"); st.caption("Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. Projeção calculada semana a semana.")
with st.sidebar:
    st.header("Acesso")
    st.success(f"{st.session_state.get('auth_nome','Usuário')} — {st.session_state.get('auth_role','')}")
    if st.button("SAIR", use_container_width=True):
        _logout()
    st.divider()
    if st.session_state.get("auth_role") == "ADMIN":
        st.header("Bases do MRP")
        cadastro_file=st.file_uploader("1. CADASTROS",type=["xlsx","xlsm","xltx"])
        estoque_file=st.file_uploader("2. Estoque_Tratado",type=["xlsx","xlsm"])
        geral_file=st.file_uploader("3. RelatorioGeral_Tratado",type=["xlsx","xlsm"])
        compras_file=st.file_uploader("4. Compras_Tratado",type=["xlsx","xlsm"])
        mt_file=st.file_uploader("5. MRP_TC_TP_Tratado",type=["xlsx","xlsm"])
        usuario_mrp=st.text_input("Usuário responsável pelo MRP",value=st.session_state.get("auth_nome", ""),placeholder="Nome do responsável")
    else:
        cadastro_file=estoque_file=geral_file=compras_file=mt_file=None
        usuario_mrp=st.session_state.get("auth_nome", "")
if st.session_state.get("auth_role") == "CONSULTA":
    st.info("Modo CONSULTA: consulta, filtros, detalhamento e exportação liberados. Alimentação das 5 bases, processamento, gravação e histórico/comparativo permanecem bloqueados.")
    try:
        render_consulta_view()
    except Exception as e:
        st.error(f"Não foi possível carregar a consulta: {e}")
    st.stop()

if not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):
    st.info("Envie as 5 planilhas tratadas para calcular um novo MRP. O último MRP salvo fica disponível para consulta e comparação.")
    try:
        snap=load_latest_snapshot()
        if snap:
            # Quando as bases locais não estão carregadas, o último MRP deve ser
            # apresentado pelo MESMO layout operacional da consulta, nunca por uma
            # tabela simplificada. Isso garante que uma atualização automática do
            # Streamlit não faça desaparecer filtros, abas ou seleção de linha.
            render_consulta_view()
            if st.session_state.get("auth_role") == "ADMIN":
                render_mrp_history()
        else:
            st.info("Ainda não há MRP salvo no banco compartilhado.")
    except Exception as e:
        st.warning(f"Não foi possível carregar o último MRP: {e}")
    st.stop()
try: cad,est,rg,rg_mrp,cp,mt=load_sources(cadastro_file.getvalue(),estoque_file.getvalue(),geral_file.getvalue(),compras_file.getvalue(),mt_file.getvalue())
except Exception as e: st.error(f"Erro ao carregar as bases: {e}"); st.stop()
rg_semanas=num(rg_mrp["Semana"]).dropna(); rg_semanas=rg_semanas[(rg_semanas>=1)&(rg_semanas<=53)]
if len(rg_semanas): semana_atual=int(rg_semanas.min()); fonte_semana="RelatorioGeral_Tratado — coluna N"
else:
    semanas_base=[]
    for s in [cp["Semana P.C."],cp["Semana S.C."],mt["Semana Entrega"],mt["Semana Necessidade"]]:
        v=num(s).dropna(); v=v[(v>=1)&(v<=53)]
        if len(v): semanas_base.append(v.astype(int))
    if not semanas_base: st.error("Não foi possível identificar a semana atual nas planilhas carregadas."); st.stop()
    semana_atual=min(int(s.min()) for s in semanas_base); fonte_semana="demais bases — fallback"
with st.sidebar:
    st.divider(); st.markdown("**Semana atual identificada nas bases**"); st.number_input("Semana atual",min_value=1,max_value=53,value=semana_atual,disabled=True); st.caption(f"Fonte: {fonte_semana}")
codigos_ii=set(cad.loc[cad["Tipo"].str.upper().eq("II"),"Código"])
sa_week=rg_mrp.groupby(["Código","Semana"],as_index=False)["Pendência"].sum().rename(columns={"Pendência":"Demanda S.A."}); tc_rows=mt[(mt["Material"]>0)&mt["Semana Necessidade"].between(1,53)].copy(); tc_week=tc_rows.groupby(["Material","Semana Necessidade"],as_index=False)["Quantidade"].sum(); tc_week.columns=["Código","Semana","Demanda TC/TP"]; pc_week=cp[(cp["Quantidade P.C."]>0)&cp["Semana P.C."].between(1,53)].groupby(["Código","Semana P.C."],as_index=False)["Quantidade P.C."].sum(); pc_week.columns=["Código","Semana","P.C."]; sc_all=cp[cp["Quantidade S.C."]>0].groupby("Código",as_index=False)["Quantidade S.C."].sum().rename(columns={"Quantidade S.C.":"S.C."}); sc_week=cp[(cp["Quantidade S.C."]>0)&cp["Semana S.C."].between(1,53)].groupby(["Código","Semana S.C."],as_index=False)["Quantidade S.C."].sum(); sc_week.columns=["Código","Semana","S.C."]; op=mt[(mt["Código Produto"]>0)&mt["Semana Entrega"].between(1,53)].copy(); fab_week=op.groupby(["Código Produto","Semana Entrega"]).size().reset_index(name="Produzindo"); fab_week.columns=["Código","Semana","Produzindo"]
macro=cad.merge(est,on="Código",how="left")
for df in [sa_week.groupby("Código",as_index=False)["Demanda S.A."].sum(),tc_week.groupby("Código",as_index=False)["Demanda TC/TP"].sum(),pc_week.groupby("Código",as_index=False)["P.C."].sum(),sc_all,fab_week.groupby("Código",as_index=False)["Produzindo"].sum()]: macro=macro.merge(df,on="Código",how="left")
for c in ["Saldo em Estoque","Demanda S.A.","Demanda TC/TP","P.C.","S.C.","Produzindo"]: macro[c]=macro[c].fillna(0.0)
macro["Demanda"]=macro["Demanda S.A."]+macro["Demanda TC/TP"]; macro.loc[macro["Tipo"].str.upper().eq("II"),"Demanda"]=0.0; macro["DIV"]=macro["Saldo em Estoque"]+macro["P.C."]+macro["S.C."]+macro["Produzindo"]-macro["Demanda"]; macro["Status"]=macro["DIV"].apply(lambda x:"CRIAR S.C." if x<-1e-9 else "OK"); atividade=["Saldo em Estoque","Demanda","P.C.","S.C.","Produzindo"]; macro=macro[macro[atividade].abs().sum(axis=1)>1e-9].copy()
events=pd.concat([sa_week.assign(Demanda=sa_week["Demanda S.A."],Supply=0.0)[["Código","Semana","Demanda","Supply"]],tc_week.assign(Demanda=tc_week["Demanda TC/TP"],Supply=0.0)[["Código","Semana","Demanda","Supply"]],pc_week.assign(Demanda=0.0,Supply=pc_week["P.C."])[["Código","Semana","Demanda","Supply"]],sc_week.assign(Demanda=0.0,Supply=sc_week["S.C."])[["Código","Semana","Demanda","Supply"]],fab_week.assign(Demanda=0.0,Supply=fab_week["Produzindo"])[["Código","Semana","Demanda","Supply"]]],ignore_index=True); events=events[events["Semana"]>=semana_atual].copy(); events.loc[events["Código"].isin(codigos_ii),"Demanda"]=0.0; events=events.groupby(["Código","Semana"],as_index=False)[["Demanda","Supply"]].sum()
pc_idx=pc_week.set_index(["Código","Semana"])["P.C."]; sc_idx=sc_week.set_index(["Código","Semana"])["S.C."]; fab_idx=fab_week.set_index(["Código","Semana"])["Produzindo"]; stock_map=est.set_index("Código")["Saldo em Estoque"].to_dict(); proj_parts=[]
for code,g0 in events.groupby("Código",sort=False):
    g0=g0.sort_values("Semana"); ultima_semana=int(g0["Semana"].max()); g=pd.DataFrame({"Semana":range(semana_atual,ultima_semana+1)}).merge(g0,on="Semana",how="left"); g["Código"]=int(code); g["Demanda"]=g["Demanda"].fillna(0.0); g["Supply"]=g["Supply"].fillna(0.0); saldo=float(stock_map.get(code,0.0)); saldos=[]; finais=[]
    for _,row in g.iterrows(): saldos.append(saldo); saldo=saldo+float(row["Supply"])-float(row["Demanda"]); finais.append(saldo)
    g["Saldo Inicial"]=saldos; g["Resumo Final"]=finais; proj_parts.append(g[["Código","Semana","Saldo Inicial","Demanda","Resumo Final"]])
proj=pd.concat(proj_parts,ignore_index=True) if proj_parts else pd.DataFrame(columns=["Código","Semana","Saldo Inicial","Demanda","Resumo Final"])
if len(proj):
    keys=pd.MultiIndex.from_frame(proj[["Código","Semana"]]); proj["P.C."]=pc_idx.reindex(keys).fillna(0.0).to_numpy(); proj["S.C."]=sc_idx.reindex(keys).fillna(0.0).to_numpy(); proj["Produzindo"]=fab_idx.reindex(keys).fillna(0.0).to_numpy(); desc_map=cad.set_index("Código")["Descrição"].to_dict(); type_map=cad.set_index("Código")["Tipo"].to_dict(); proj["Descrição"]=proj["Código"].map(desc_map); proj["Tipo"]=proj["Código"].map(type_map)
atendimento_map={}
if len(proj):
    for code,g in proj.groupby("Código",sort=False):
        g=g.sort_values("Semana"); finais=pd.to_numeric(g["Resumo Final"],errors="coerce").fillna(-float("inf"))
        if (finais>=-1e-9).all(): atendimento_map[int(code)]=semana_atual
        elif float(finais.iloc[-1])<-1e-9: atendimento_map[int(code)]="NN"
        else:
            ok=g[finais>=-1e-9]; atendimento_map[int(code)]=int(ok.iloc[-1]["Semana"]) if len(ok) else "NN"
for _,row in macro.iterrows():
    if float(row["Saldo em Estoque"])>1e-9 and all(abs(float(row[c]))<=1e-9 for c in ["Demanda","P.C.","S.C.","Produzindo"]): atendimento_map[int(row["Código"])] = semana_atual
macro["Semana de Atendimento"]=macro["Código"].map(atendimento_map).fillna(""); macro["Período de Atendimento"]=macro["Semana de Atendimento"].apply(lambda x:"NN" if str(x).strip().upper()=="NN" else periodo_semana(x))
ultima_solicitacao=rg.groupby("Projeto",as_index=False)["Data Solicitação"].max().rename(columns={"Data Solicitação":"Última Solicitação"}); ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)
data_cm_projeto=rg.groupby("Projeto",as_index=False)["Data CM"].max().rename(columns={"Data CM":"Data CM"}); data_cm_projeto["Data CM"]=data_cm_projeto["Data CM"].apply(lambda x:formatar_data_br(x) if pd.notna(pd.to_datetime(x,errors="coerce")) else "NI")
demanda_projeto_base=rg_mrp[(~rg_mrp["Código"].isin(codigos_ii))&rg_mrp["Pendência"].ne(0)].copy(); demanda_projeto_base=demanda_projeto_base[["Projeto","Código","Pendência","Semana"]].rename(columns={"Código":"Produto","Pendência":"Necessidade","Semana":"Semana de Necessidade"}); demanda_projeto_base=demanda_projeto_base.merge(cad[["Código","Descrição"]].rename(columns={"Código":"Produto"}),on="Produto",how="left"); demanda_projeto_base=demanda_projeto_base.merge(ultima_solicitacao,on="Projeto",how="left"); demanda_projeto_base=demanda_projeto_base.merge(data_cm_projeto,on="Projeto",how="left"); demanda_projeto_base["Data CM"]=demanda_projeto_base["Data CM"].fillna("NI"); demanda_projeto_base["Última Solicitação"]=demanda_projeto_base["Última Solicitação"].fillna("NI"); demanda_projeto_base=demanda_projeto_base.sort_values(["Produto","Semana de Necessidade","Projeto"]).reset_index(drop=True)
pre_nota_map=cp.groupby("Código")["Saldo em Pré Nota"].max().to_dict(); stock_pool=est.set_index("Código")["Saldo em Estoque"].to_dict()
def calcular_demanda_projeto(df):
    cols=["Projeto","Produto","Descrição","Última Solicitação","Data CM","Semana de Necessidade","Semana de Atendimento","Necessidade","Estoque","Pré Nota","P.C.","Fabricação","S.C.","Ação"]
    if df.empty: return pd.DataFrame(columns=cols)
    out=[]
    for code,rows in df.groupby("Produto",sort=False):
        rows=rows.sort_values(["Semana de Necessidade","Projeto"]).copy(); estoque_restante=float(stock_pool.get(int(code),0.0)); pc_pool=[{"qty":float(r["Quantidade P.C."]),"week":r["Semana P.C."]} for _,r in cp[(cp["Código"]==int(code))&(cp["Quantidade P.C."]>0)].sort_values("Semana P.C.",na_position="last").iterrows()]; fab_pool=[{"qty":1.0,"week":r["Semana Entrega"]} for _,r in op[op["Código Produto"]==int(code)].sort_values("Semana Entrega",na_position="last").iterrows()]; sc_pool=[{"qty":float(r["Quantidade S.C."]),"week":r["Semana S.C."]} for _,r in cp[(cp["Código"]==int(code))&(cp["Quantidade S.C."]>0)].sort_values("Semana S.C.",na_position="last").iterrows()]
        for _,r in rows.iterrows():
            necessidade=float(r["Necessidade"]); restante=necessidade; saldo_estoque_inicial=estoque_restante; pc_inicial=sum(item["qty"] for item in pc_pool); fab_inicial=sum(item["qty"] for item in fab_pool); sc_inicial=sum(item["qty"] for item in sc_pool); usados={"Estoque":0.0,"P.C.":0.0,"Fabricação":0.0,"S.C.":0.0}; ultima_semana=None; acoes=[]
            if restante>1e-9 and estoque_restante>1e-9:
                take=min(restante,estoque_restante); estoque_restante-=take; restante-=take; usados["Estoque"]+=take; ultima_semana=semana_atual; acoes.append(f"Estoque {take:g}")
            for pool,key,label in [(pc_pool,"P.C.","P.C."),(fab_pool,"Fabricação","Fabricação"),(sc_pool,"S.C.","S.C.")]:
                while restante>1e-9 and pool:
                    item=pool[0]
                    if item["qty"]<=1e-9: pool.pop(0); continue
                    take=min(restante,item["qty"]); item["qty"]-=take; restante-=take; usados[key]+=take; ultima_semana=item["week"] if pd.notna(item["week"]) and float(item["week"])>0 else None; semana_txt=str(int(float(item["week"]))) if pd.notna(item["week"]) and float(item["week"])>0 else "a definir"; acoes.append(f"{label} {take:g} (sem. {semana_txt})")
                    if item["qty"]<=1e-9: pool.pop(0)
            if restante>1e-9:
                semana_criacao=int(r["Semana de Necessidade"]); acoes.append(f"CRIAR S.C. {restante:g} para semana {semana_criacao}"); semana_atendimento="NN"
            else: semana_atendimento="A definir" if ultima_semana is None else str(int(float(ultima_semana)))
            out.append({"Projeto":r["Projeto"],"Produto":int(code),"Descrição":r["Descrição"],"Última Solicitação":r["Última Solicitação"],"Data CM":r["Data CM"],"Semana de Necessidade":int(r["Semana de Necessidade"]),"Semana de Atendimento":semana_atendimento,"Necessidade":necessidade,"Estoque":saldo_estoque_inicial,"Pré Nota":float(pre_nota_map.get(int(code),0.0)),"P.C.":pc_inicial,"Fabricação":fab_inicial,"S.C.":sc_inicial,"Ação":"; ".join(acoes) if acoes else "OK"})
    return pd.DataFrame(out)[cols].sort_values(["Produto","Semana de Necessidade","Projeto"]).reset_index(drop=True)
demanda_projeto=calcular_demanda_projeto(demanda_projeto_base)
# Lista de compras: somente demandas de projeto que não normalizam e exigem nova S.C.
compras_mrp=pd.DataFrame(columns=["produto","qnt","data","psy","cc","op","obs","prioridade"])
if len(demanda_projeto):
    cp_mrp=demanda_projeto[demanda_projeto["Semana de Atendimento"].astype(str).str.strip().str.upper().eq("NN")].copy()
    if len(cp_mrp):
        cp_mrp["qnt"]=pd.to_numeric(cp_mrp["Ação"].str.extract(r"CRIAR S\.C\.\s*([0-9]+(?:\.[0-9]+)?)",expand=False),errors="coerce").fillna(0.0)
        cp_mrp=cp_mrp[cp_mrp["qnt"]>1e-9].copy()
        cp_mrp["produto"]=cp_mrp["Produto"].map(lambda x:f"{int(x):08d}")
        cp_mrp["data"]=cp_mrp["Semana de Necessidade"].map(ultimo_dia_util_semana)
        cp_mrp["psy"]=""
        cp_mrp["cc"]="600307"
        cp_mrp["op"]=cp_mrp["Projeto"].astype(str)
        cp_mrp["obs"]="MRP"
        cp_mrp["prioridade"]=""
        compras_mrp=cp_mrp[["produto","qnt","data","psy","cc","op","obs","prioridade"]].reset_index(drop=True)
        compras_mrp["qnt"]=compras_mrp["qnt"].map(lambda x:int(x) if float(x).is_integer() else float(x))
fab_det=op[["ORDEM DE PRODUÇÃO","Código Produto","Semana Entrega"]].sort_values(["Código Produto","Semana Entrega","ORDEM DE PRODUÇÃO"]).copy(); fab_det["Quantidade"]=1
# Salva apenas uma vez por conjunto de arquivos carregado.
if st.session_state.get("auth_role") == "ADMIN":
    try:
        _mrp_sig=hashlib.sha256(b"MRP-SNAPSHOT-V3-COMPRAS-PERIODO"+b"".join([f.getvalue() for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]])).hexdigest()
        if st.session_state.get("_mrp_saved_sig")!=_mrp_sig:
            save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp,cp)
            st.session_state["_mrp_saved_sig"]=_mrp_sig
            st.success("MRP salvo no histórico compartilhado.")
    except Exception as _save_err:
        st.warning(f"O MRP foi calculado, mas não foi possível salvar o histórico compartilhado: {_save_err}")
m=st.columns(5); m[0].metric("Materiais no MRP",f"{len(macro):,}"); m[1].metric("Demanda total",f"{macro['Demanda'].sum():,.0f}"); m[2].metric("P.C.",f"{macro['P.C.'].sum():,.0f}"); m[3].metric("S.C.",f"{macro['S.C.'].sum():,.0f}"); m[4].metric("Criar S.C.",f"{(-macro.loc[macro['DIV']<0,'DIV']).sum():,.0f}")
tab1,tab2=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"]])
macro_cols=["Código","Descrição","Tipo","Saldo em Estoque","Demanda","P.C.","S.C.","Produzindo","DIV","Status","Semana de Atendimento","Período de Atendimento"]
with tab1:
    st.subheader("Demanda Geral"); c1,c2,c3=st.columns(3)
    with c1: busca=st.text_input("Código / descrição")
    with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."])
    with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]))
    v=macro.copy()
    if busca:
        b=busca.strip(); v=v[v["Código"].astype(str).str.contains(b,na=False)|v["Descrição"].str.contains(b,case=False,na=False)]
    if status: v=v[v["Status"].isin(status)]
    if tipos: v=v[v["Tipo"].isin(tipos)]
    v["_ord_status"]=v["Status"].map({"CRIAR S.C.":0,"OK":1}).fillna(2); v=v.sort_values(["_ord_status","Código"]).drop(columns="_ord_status")
    st.markdown("**Clique em uma linha para abrir o detalhamento do material.**")
    selecao=st.dataframe(v[macro_cols],use_container_width=True,height=500,hide_index=True,on_select="rerun",selection_mode="single-row",key="demanda_geral_tabela")
    linhas=selecao.selection.rows if selecao is not None else []
    code=int(v.iloc[linhas[0]]["Código"]) if linhas and 0<=linhas[0]<len(v) else None
    if code is not None:
        st.divider(); st.subheader("Detalhamento do material"); desc_map=cad.set_index("Código")["Descrição"].to_dict(); st.markdown(f"**Material selecionado:** `{code}` — {desc_map.get(code,'')}")
        w=proj[proj["Código"]==code].copy()
        if len(w):
            st.markdown("**Projeção semanal**"); w["Período da Semana"]=w["Semana"].apply(periodo_semana); st.dataframe(w[["Código","Descrição","Tipo","Semana","Período da Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]],use_container_width=True,hide_index=True)
        d=demanda_projeto[demanda_projeto["Produto"]==code]
        if len(d): st.markdown("**S.A. — projetos que geram a demanda**"); st.dataframe(d,use_container_width=True,hide_index=True)
        compras=cp[(cp["Código"]==code)&((cp["Quantidade S.C."]>0)|(cp["Quantidade P.C."]>0))].copy()
        if len(compras): st.markdown("**Compras**"); st.dataframe(compras[["Código","Nº S.C.","Quantidade S.C.","Semana S.C.","Nº P.C.","Quantidade P.C.","Semana P.C."]],use_container_width=True,hide_index=True); st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")
        f=fab_det[fab_det["Código Produto"]==code]
        if len(f): st.markdown("**Produzindo — OPs (1 OP = 1 peça)**"); st.dataframe(f,use_container_width=True,hide_index=True)
with tab2:
    st.subheader("Demanda por Projeto"); c1,c2=st.columns(2)
    with c1: busca2=st.text_input("Código / projeto")
    with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana de Necessidade"].unique().tolist()) if len(demanda_projeto) else [])
    d=demanda_projeto.copy()
    if busca2:
        b2=busca2.strip(); d=d[d["Produto"].astype(str).str.contains(b2,na=False)|d["Projeto"].str.contains(b2,case=False,na=False)]
    if semana_filtro: d=d[d["Semana de Necessidade"].isin(semana_filtro)]
    st.dataframe(d,use_container_width=True,height=600,hide_index=True)
st.divider(); st.subheader("Exportação de relatórios"); st.caption("Os relatórios são exportados com os mesmos dados calculados na tela.")
compras_mrp_export=normalizar_compra_mrp(compras_mrp)
export_macro=macro[macro_cols].sort_values(["Status","Código"],key=lambda s:s.map({"CRIAR S.C.":0,"OK":1}).fillna(2) if s.name=="Status" else s).copy(); export_proj=proj.copy()
if len(export_proj): export_proj["Período da Semana"]=export_proj["Semana"].apply(periodo_semana)
export_proj=export_proj[["Código","Descrição","Tipo","Semana","Período da Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]].sort_values(["Código","Semana"])
sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"Compra_MRP":compras_mrp_export,"Compras":cp,"Fabricacao":fab_det,"Cadastro_Base":cad}
excel_data=excel_bytes(sheets); zip_data=zip_bytes({name+".csv":csv_bytes(df) for name,df in sheets.items()})
compra_excel_data=excel_bytes({"Compra_MRP":compras_mrp_export})
compra_csv_data=csv_bytes(compras_mrp)
b1,b2,b3,b4=st.columns(4)
with b1: st.download_button("BAIXAR TODOS — EXCEL",excel_data,"MRP_Relatorios_Completos.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
with b2: st.download_button("BAIXAR TODOS — ZIP/CSV",zip_data,"MRP_Relatorios_Completos.zip","application/zip",use_container_width=True)
with b3: st.download_button("BAIXAR MRP GERAL — CSV",csv_bytes(export_macro),"MRP_Geral.csv","text/csv",use_container_width=True)
with b4: st.download_button("BAIXAR COMPRA MRP",compra_excel_data,"Compra_MRP.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
if len(compras_mrp): st.caption(f"Arquivo de compra gerado com {len(compras_mrp)} item(ns) que não normalizam na Demanda por Projeto e exigem nova S.C.")
else: st.caption("Nenhum item da Demanda por Projeto exige nova S.C. no momento.")
st.divider()
if st.session_state.get("auth_role") == "ADMIN":
    render_mrp_history()

# trigger-final-2
