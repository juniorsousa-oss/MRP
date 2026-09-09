import streamlit as st
import pandas as pd
import requests
import json
import hashlib
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

SUPABASE_URL="https://cuixazpxkvniqldmmnth.supabase.co"
SUPABASE_KEY="sb_publishable_ZTqIgmA9Ez6AVQsoXa0P8Q_6CYHDFye"

# =========================================================
# AUTENTICAÇÃO E PERFIS — SUPABASE AUTH
# Usuários exibidos no aplicativo: almoxsetta e consulta.
# O Auth continua usando e-mail internamente.
# =========================================================
def _auth_headers(token=None):
    return {"apikey": SUPABASE_KEY,"Authorization": f"Bearer {token or SUPABASE_KEY}","Content-Type": "application/json"}

def _login_supabase(email, password):
    r=requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",headers={"apikey":SUPABASE_KEY,"Content-Type":"application/json"},json={"email":email,"password":password},timeout=20)
    if r.status_code>=400:
        try: msg=r.json().get("error_description") or r.json().get("msg") or "Login inválido"
        except Exception: msg="Login inválido"
        raise ValueError(msg)
    return r.json()

def _load_my_role(access_token,user_id):
    r=requests.get(f"{SUPABASE_URL}/rest/v1/user_roles",headers=_auth_headers(access_token),params={"select":"user_id,nome,role","user_id":f"eq.{user_id}","limit":"1"},timeout=20)
    r.raise_for_status(); rows=r.json(); return rows[0] if rows else None

def _logout():
    for k in ["auth_access_token","auth_refresh_token","auth_user_id","auth_email","auth_nome","auth_role"]: st.session_state.pop(k,None)
    st.rerun()

def _require_login():
    if st.session_state.get("auth_access_token") and st.session_state.get("auth_role") in {"ADMIN","CONSULTA"}: return True
    st.title("MRP — SETTA")
    st.subheader("Acesso ao sistema")
    usuarios={"almoxsetta":"almoxsetta@mrp.setta","consulta":"consulta@mrp.setta"}
    with st.form("login_form",clear_on_submit=False):
        usuario=st.text_input("Usuário",placeholder="almoxsetta ou consulta")
        password=st.text_input("Senha",type="password")
        entrar=st.form_submit_button("ENTRAR",use_container_width=True)
    if entrar:
        usuario_limpo=usuario.strip().lower()
        if usuario_limpo not in usuarios or not password:
            st.error("Informe um usuário válido e a senha.")
        else:
            try:
                auth=_login_supabase(usuarios[usuario_limpo],password); user=auth.get("user") or {}; token=auth.get("access_token")
                role=_load_my_role(token,user.get("id")) if token and user.get("id") else None
                if not role or role.get("role") not in {"ADMIN","CONSULTA"}: st.error("Usuário autenticado, mas sem perfil autorizado no MRP.")
                else:
                    st.session_state["auth_access_token"]=token; st.session_state["auth_refresh_token"]=auth.get("refresh_token"); st.session_state["auth_user_id"]=user.get("id"); st.session_state["auth_email"]=user.get("email",usuarios[usuario_limpo]); st.session_state["auth_nome"]=role.get("nome") or usuario_limpo; st.session_state["auth_role"]=role.get("role"); st.rerun()
            except Exception as e: st.error(f"Não foi possível entrar: {e}")
    return False

if not _require_login(): st.stop()

def _sb_headers():
    token=st.session_state.get("auth_access_token") or SUPABASE_KEY
    return _auth_headers(token)
