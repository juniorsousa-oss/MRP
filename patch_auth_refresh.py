from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')
marker='def _sb_get(params=None):'
if 'def _refresh_supabase_session(' not in s:
    refresh='''def _refresh_supabase_session():\n    refresh_token = st.session_state.get("auth_refresh_token")\n    if not refresh_token:\n        return False\n    try:\n        r = requests.post(\n            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",\n            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},\n            json={"refresh_token": refresh_token},\n            timeout=20,\n        )\n        if r.status_code >= 400:\n            return False\n        auth = r.json()\n        if not auth.get("access_token"):\n            return False\n        st.session_state["auth_access_token"] = auth.get("access_token")\n        if auth.get("refresh_token"):\n            st.session_state["auth_refresh_token"] = auth.get("refresh_token")\n        return True\n    except Exception:\n        return False\n\n'''
    if marker not in s: raise SystemExit('ANCHOR_NOT_FOUND')
    s=s.replace(marker,refresh+marker,1)

old='''def _sb_get(params=None):\n    r=requests.get(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers=_sb_headers(),params=params or {},timeout=20)\n    r.raise_for_status(); return r.json()\n'''
new='''def _sb_get(params=None):\n    r=requests.get(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers=_sb_headers(),params=params or {},timeout=20)\n    if r.status_code == 401 and _refresh_supabase_session():\n        r=requests.get(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers=_sb_headers(),params=params or {},timeout=20)\n    r.raise_for_status(); return r.json()\n'''
if old in s: s=s.replace(old,new,1)
else: print('sb_get pattern not found')

old='''def _sb_post(payload):\n    r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)\n    r.raise_for_status(); return r.json()\n'''
new='''def _sb_post(payload):\n    r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)\n    if r.status_code == 401 and _refresh_supabase_session():\n        r=requests.post(f"{SUPABASE_URL}/rest/v1/mrp_snapshots",headers={**_sb_headers(),"Prefer":"return=representation"},json=payload,timeout=30)\n    r.raise_for_status(); return r.json()\n'''
if old in s: s=s.replace(old,new,1)
else: print('sb_post pattern not found')

# Make visual configuration GET resilient to expired sessions as well.
old='''        r.raise_for_status()\n        rows = r.json()\n'''
new='''        if r.status_code == 401 and _refresh_supabase_session():\n            r = requests.get(\n                f"{SUPABASE_URL}/rest/v1/mrp_app_config",\n                headers=_sb_headers(),\n                params={"select":"*", "id":"eq.1", "limit":"1"},\n                timeout=20,\n            )\n        r.raise_for_status()\n        rows = r.json()\n'''
if old in s: s=s.replace(old,new,1)
else: print('config_get pattern not found')

p.write_text(s,encoding='utf-8')
print('auth refresh patch applied')
