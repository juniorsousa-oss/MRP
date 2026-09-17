LOGIN_SPACING_PATCH = r"""
# =========================================================
# LOGIN — AJUSTE FINO DE ESPAÇAMENTO ENTRE LOGO, TÍTULO E FORMULÁRIO
# =========================================================

_old_login_img = '''      .setta-login-image {{
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
      }}'''
_new_login_img = '''      .setta-login-image {{
        height:140px !important;
        transform:none !important;
        padding:22px 28px 8px !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
      }}
      .setta-login-image img {{
        max-width:220px !important;
        max-height:88px !important;
      }}'''
if _old_login_img in _source:
    _source = _source.replace(_old_login_img, _new_login_img, 1)

_old_login_heading = '''      .setta-login-heading {{
        height:48px !important;
        transform:none !important;
        padding:0 28px !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
      }}'''
_new_login_heading = '''      .setta-login-heading {{
        height:48px !important;
        transform:none !important;
        padding:30px 28px 0 !important;
        display:flex !important;
        align-items:flex-start !important;
        justify-content:center !important;
        box-sizing:border-box !important;
      }}'''
if _old_login_heading in _source:
    _source = _source.replace(_old_login_heading, _new_login_heading, 1)

_old_form_top = '        top:calc(50% - 50px) !important;\n'
_new_form_top = '        top:calc(40% - 20px) !important;\n'
if _old_form_top in _source:
    _source = _source.replace(_old_form_top, _new_form_top, 1)
"""
