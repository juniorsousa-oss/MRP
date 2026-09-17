LOGIN_PATCH = r"""
# =========================================================
# LOGIN — CARD MAIOR, CAMPOS ORGANIZADOS E AUTOCOMPLETE
# =========================================================

_login_replacements = [
    (
        'width:286px !important; height:390px !important; margin:0 !important; padding:0 !important;',
        'width:400px !important; height:520px !important; margin:0 !important; padding:0 !important;'
    ),
    (
        'border-radius:28px !important; box-shadow:0 16px 42px rgba(0,0,0,.16) !important;',
        'border-radius:28px !important; box-shadow:0 18px 48px rgba(0,0,0,.16) !important;'
    ),
    (
        'width:100% !important; height:135px !important; transform:translateY(-30px) !important; overflow:hidden !important; background:transparent !important;',
        'width:100% !important; height:150px !important; transform:none !important; overflow:hidden !important; background:transparent !important;'
    ),
    (
        'padding:20px 18px 8px !important; box-sizing:border-box !important;',
        'padding:26px 24px 10px !important; box-sizing:border-box !important;'
    ),
    (
        'max-width:165px !important; max-height:76px !important;',
        'max-width:230px !important; max-height:104px !important;'
    ),
    (
        '.setta-login-heading { text-align:center !important; padding:0 20px !important; height:58px !important; transform:translateY(-30px) !important; box-sizing:border-box !important; }',
        '.setta-login-heading { text-align:center !important; padding:0 28px !important; height:64px !important; transform:none !important; box-sizing:border-box !important; display:flex !important; align-items:center !important; justify-content:center !important; }'
    ),
    (
        '.setta-login-title { color:#111 !important; font-size:14px !important; line-height:17px !important; font-weight:800 !important; margin:0 !important; }',
        '.setta-login-title { color:#111 !important; font-size:20px !important; line-height:24px !important; font-weight:800 !important; margin:0 !important; }'
    ),
    (
        'position:fixed !important; left:50% !important; top:calc(40% + 15px) !important; transform:translateX(-50%) !important;',
        'position:fixed !important; left:50% !important; top:calc(50% - 35px) !important; transform:translateX(-50%) !important;'
    ),
    (
        'width:286px !important; height:170px !important; margin:0 !important; padding:0 20px 14px !important;',
        'width:352px !important; height:255px !important; margin:0 !important; padding:0 0 18px !important;'
    ),
    (
        'div[data-testid="stForm"] label { color:#202020 !important; font-size:9px !important; line-height:12px !important; font-weight:600 !important; margin-bottom:2px !important; }',
        'div[data-testid="stForm"] label { color:#202020 !important; font-size:13px !important; line-height:18px !important; font-weight:650 !important; margin-bottom:5px !important; }'
    ),
    (
        'div[data-testid="stForm"] [data-testid="stTextInput"] { margin-bottom:8px !important; }',
        'div[data-testid="stForm"] [data-testid="stTextInput"] { margin-bottom:14px !important; }'
    ),
    (
        'div[data-testid="stForm"] [data-testid="stTextInput"] { width:100% !important; margin-bottom:9px !important; }',
        'div[data-testid="stForm"] [data-testid="stTextInput"] { width:100% !important; margin-bottom:14px !important; }'
    ),
    (
        'width:100% !important; height:27px !important; min-height:27px !important; box-sizing:border-box !important;',
        'width:100% !important; height:42px !important; min-height:42px !important; box-sizing:border-box !important;'
    ),
    (
        'padding:0 10px !important; border:0 !important; outline:none !important; box-shadow:none !important;',
        'padding:0 13px !important; border:0 !important; outline:none !important; box-shadow:none !important;'
    ),
    (
        'border-radius:6px !important; background:transparent !important; color:#202020 !important; font-size:8px !important;',
        'border-radius:8px !important; background:transparent !important; color:#202020 !important; font-size:13px !important;'
    ),
    (
        'width:100% !important; height:31px !important; min-height:31px !important; box-sizing:border-box !important;',
        'width:100% !important; height:44px !important; min-height:44px !important; box-sizing:border-box !important;'
    ),
    (
        'border-radius:8px !important; background:#f0f2f6 !important; box-shadow:none !important; overflow:hidden !important;',
        'border-radius:10px !important; background:#f4f5f7 !important; box-shadow:none !important; overflow:hidden !important;'
    ),
    (
        'div[data-testid="stForm"] [data-baseweb="input"] > div { height:27px !important; min-height:27px !important; }',
        'div[data-testid="stForm"] [data-baseweb="input"] > div { height:42px !important; min-height:42px !important; }'
    ),
    (
        'width:34px !important; height:27px !important; min-height:27px !important; margin:0 !important; padding:0 !important;',
        'width:42px !important; height:42px !important; min-height:42px !important; margin:0 !important; padding:0 !important;'
    ),
    (
        'flex:0 0 34px !important; position:static !important; top:auto !important; border:0 !important;',
        'flex:0 0 42px !important; position:static !important; top:auto !important; border:0 !important;'
    ),
    (
        'width:16px !important; height:16px !important; margin:0 !important;',
        'width:18px !important; height:18px !important; margin:0 !important;'
    ),
    (
        'position:static !important; width:100% !important; height:29px !important; min-height:29px !important;',
        'position:static !important; width:100% !important; height:44px !important; min-height:44px !important;'
    ),
    (
        'margin:8px 0 0 !important; padding:0 !important; box-sizing:border-box !important; border-radius:7px !important;',
        'margin:8px 0 0 !important; padding:0 !important; box-sizing:border-box !important; border-radius:10px !important;'
    ),
    (
        'font-size:8px !important; font-weight:700 !important; display:flex !important; align-items:center !important; justify-content:center !important;',
        'font-size:13px !important; font-weight:750 !important; display:flex !important; align-items:center !important; justify-content:center !important;'
    ),
    (
        '.setta-login-wrap, div[data-testid="stForm"] { width:286px !important; }',
        '.setta-login-wrap { width:400px !important; } div[data-testid="stForm"] { width:352px !important; }'
    ),
]

for _old_login, _new_login in _login_replacements:
    if _old_login in _source:
        _source = _source.replace(_old_login, _new_login, 1)

_old_login_fields = '''    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        entrar = st.form_submit_button("ENTRAR", use_container_width=True)'''
_new_login_fields = '''    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input(
            "Usuário",
            placeholder="Digite seu usuário",
            key="login_usuario",
            autocomplete="username",
        )
        password = st.text_input(
            "Senha",
            type="password",
            placeholder="Digite sua senha",
            key="login_senha",
            autocomplete="current-password",
        )
        entrar = st.form_submit_button("ENTRAR", use_container_width=True)'''

if _old_login_fields not in _source:
    raise RuntimeError("Campos do formulário de login não encontrados para adequação.")
_source = _source.replace(_old_login_fields, _new_login_fields, 1)
"""
