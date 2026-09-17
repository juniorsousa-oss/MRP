LOGIN_PATCH = r"""
# =========================================================
# LOGIN — CARD MAIOR, CAMPOS ORGANIZADOS E AUTOCOMPLETE
# =========================================================

_login_replacements = [
    (
        'width:286px !important; height:390px !important; margin:0 !important; padding:0 !important;',
        'width:400px !important; height:500px !important; margin:0 !important; padding:0 !important;'
    ),
    (
        'border-radius:28px !important; box-shadow:0 16px 42px rgba(0,0,0,.16) !important;',
        'border-radius:26px !important; box-shadow:0 18px 48px rgba(0,0,0,.16) !important;'
    ),
    (
        'width:100% !important; height:135px !important; transform:translateY(-30px) !important; overflow:hidden !important; background:transparent !important;',
        'width:100% !important; height:145px !important; transform:none !important; overflow:hidden !important; background:transparent !important;'
    ),
    (
        'padding:20px 18px 8px !important; box-sizing:border-box !important;',
        'padding:26px 26px 4px !important; box-sizing:border-box !important;'
    ),
    (
        'max-width:165px !important; max-height:76px !important;',
        'max-width:230px !important; max-height:100px !important;'
    ),
    (
        'position:fixed !important; left:50% !important; top:calc(40% + 15px) !important; transform:translateX(-50%) !important;',
        'position:fixed !important; left:50% !important; top:calc(50% - 50px) !important; transform:translateX(-50%) !important;'
    ),
    (
        'width:286px !important; height:170px !important; margin:0 !important; padding:0 20px 14px !important;',
        'width:352px !important; height:245px !important; margin:0 !important; padding:0 !important;'
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
        'margin:10px 0 0 !important; padding:0 !important; box-sizing:border-box !important; border-radius:10px !important;'
    ),
    (
        'font-size:8px !important; font-weight:700 !important; display:flex !important; align-items:center !important; justify-content:center !important;',
        'font-size:13px !important; font-weight:750 !important; display:flex !important; align-items:center !important; justify-content:center !important;'
    ),
    (
        '.setta-login-wrap, div[data-testid="stForm"] {{ width:286px !important; }}',
        '.setta-login-wrap {{ width:400px !important; }} div[data-testid="stForm"] {{ width:352px !important; }}'
    ),
]

for _old_login, _new_login in _login_replacements:
    if _old_login in _source:
        _source = _source.replace(_old_login, _new_login, 1)

# Override final do login. Ele vem depois das regras antigas e garante que
# logo, título e formulário usem a altura do card de forma equilibrada.
_login_media_anchor = '''      @media (max-width:480px) {{
        .setta-login-wrap, div[data-testid="stForm"] {{ width:286px !important; }}
      }}'''
_login_distribution_css = '''      /* DISTRIBUIÇÃO FINAL DO CARD DE LOGIN */
      .setta-login-wrap {{
        width:400px !important;
        height:500px !important;
        border-radius:26px !important;
      }}
      .setta-login-image {{
        height:145px !important;
        transform:none !important;
        padding:24px 28px 4px !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
      }}
      .setta-login-image img {{
        max-width:230px !important;
        max-height:100px !important;
      }}
      .setta-login-heading {{
        height:48px !important;
        transform:none !important;
        padding:0 28px !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
      }}
      .setta-login-title {{
        font-size:18px !important;
        line-height:22px !important;
        font-weight:800 !important;
        margin:0 !important;
        text-align:center !important;
      }}
      div[data-testid="stForm"] {{
        position:fixed !important;
        left:50% !important;
        top:calc(50% - 50px) !important;
        transform:translateX(-50%) !important;
        width:352px !important;
        height:245px !important;
        padding:0 !important;
      }}
      div[data-testid="stForm"] label {{
        font-size:12px !important;
        line-height:17px !important;
        font-weight:650 !important;
        margin-bottom:5px !important;
      }}
      div[data-testid="stForm"] [data-testid="stTextInput"] {{
        width:100% !important;
        margin-bottom:14px !important;
      }}
      div[data-testid="stForm"] input {{
        height:42px !important;
        min-height:42px !important;
        font-size:13px !important;
      }}
      div[data-testid="stForm"] [data-baseweb="input"] {{
        height:44px !important;
        min-height:44px !important;
        border-radius:10px !important;
      }}
      div[data-testid="stForm"] [data-baseweb="input"] > div {{
        height:42px !important;
        min-height:42px !important;
      }}
      div[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] button {{
        width:42px !important;
        height:42px !important;
        min-height:42px !important;
        flex:0 0 42px !important;
      }}
      div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
        height:44px !important;
        min-height:44px !important;
        margin:10px 0 0 !important;
        border-radius:10px !important;
        font-size:13px !important;
        font-weight:750 !important;
      }}
      @media (max-width:480px) {{
        .setta-login-wrap {{ width:360px !important; height:500px !important; }}
        div[data-testid="stForm"] {{ width:312px !important; }}
      }}'''
if _login_media_anchor in _source:
    _source = _source.replace(_login_media_anchor, _login_distribution_css, 1)

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
