# =========================================================
# LOGIN — AJUSTE FINAL E ÚNICO DE POSICIONAMENTO
# =========================================================
# EDITE SOMENTE ESTES VALORES.
# Este CSS é aplicado por último e prevalece sobre os estilos anteriores.

LOGIN_CARD_WIDTH = 400
LOGIN_CARD_HEIGHT = 500

LOGIN_LOGO_AREA_HEIGHT = 140
LOGIN_LOGO_MAX_WIDTH = 220
LOGIN_LOGO_MAX_HEIGHT = 82
LOGIN_LOGO_PADDING_TOP = 18

# AUMENTAR = texto "MRP | SETTA" desce
# DIMINUIR = texto sobe
LOGIN_TITLE_PADDING_TOP = 0
LOGIN_TITLE_AREA_HEIGHT = 66
LOGIN_TITLE_FONT_SIZE = 18

# POSITIVO = formulário desce
# NEGATIVO = formulário sobe
LOGIN_FORM_OFFSET_Y = 60
LOGIN_FORM_WIDTH = 300

# CAMPOS DE USUÁRIO / SENHA
LOGIN_FIELD_HEIGHT = 35
# Espaço vertical entre o campo Usuário e o campo Senha.
# DIMINUIR = aproxima os campos | AUMENTAR = afasta.
LOGIN_FIELD_GAP = 3
# Espaço horizontal do texto dentro do campo.
LOGIN_FIELD_PADDING_X = 12
# Largura reservada ao botão do olho da senha.
LOGIN_EYE_WIDTH = 38

LOGIN_BUTTON_HEIGHT = 50

LOGIN_SPACING_PATCH = r"""
# =========================================================
# LOGIN — CSS FINAL APLICADO POR ÚLTIMO
# =========================================================
_login_final_anchor = '    st.markdown(\'<div class="setta-login-form-note">Entre com seu usuário e senha para acessar o sistema.</div>\', unsafe_allow_html=True)\n'

_login_final_css = '''
<style>
  .setta-login-wrap {
    width:__CARD_WIDTH__px !important;
    height:__CARD_HEIGHT__px !important;
    border-radius:26px !important;
  }

  .setta-login-image {
    width:100% !important;
    height:__LOGO_AREA_HEIGHT__px !important;
    transform:none !important;
    padding:__LOGO_PADDING_TOP__px 28px 4px !important;
    box-sizing:border-box !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
  }

  .setta-login-image img {
    width:auto !important;
    height:auto !important;
    max-width:__LOGO_MAX_WIDTH__px !important;
    max-height:__LOGO_MAX_HEIGHT__px !important;
    object-fit:contain !important;
    display:block !important;
  }

  .setta-login-heading {
    width:100% !important;
    height:__TITLE_AREA_HEIGHT__px !important;
    transform:none !important;
    margin:0 !important;
    padding:__TITLE_PADDING_TOP__px 28px 0 !important;
    box-sizing:border-box !important;
    display:flex !important;
    align-items:flex-start !important;
    justify-content:center !important;
  }

  .setta-login-title {
    margin:0 !important;
    padding:0 !important;
    font-size:__TITLE_FONT_SIZE__px !important;
    line-height:24px !important;
    font-weight:800 !important;
    text-align:center !important;
  }

  div[data-testid="stForm"] {
    position:fixed !important;
    left:50% !important;
    top:calc(50% + __FORM_OFFSET_Y__px) !important;
    transform:translate(-50%, -50%) !important;
    width:__FORM_WIDTH__px !important;
    height:auto !important;
    margin:0 !important;
    padding:0 !important;
    background:transparent !important;
    border:0 !important;
    box-shadow:none !important;
  }

  div[data-testid="stForm"] label {
    font-size:12px !important;
    line-height:17px !important;
    font-weight:650 !important;
    margin-bottom:5px !important;
  }

  /* Espaçamento entre Usuário e Senha */
  div[data-testid="stForm"] [data-testid="stTextInput"] {
    width:100% !important;
    margin-bottom:__FIELD_GAP__px !important;
  }

  /* Contêiner externo do campo */
  div[data-testid="stForm"] [data-baseweb="input"] {
    height:__FIELD_HEIGHT__px !important;
    min-height:__FIELD_HEIGHT__px !important;
    display:flex !important;
    align-items:center !important;
    box-sizing:border-box !important;
  }

  /* Contêiner interno que o Streamlit/BaseWeb cria */
  div[data-testid="stForm"] [data-baseweb="input"] > div {
    height:__FIELD_HEIGHT__px !important;
    min-height:__FIELD_HEIGHT__px !important;
    display:flex !important;
    align-items:center !important;
    box-sizing:border-box !important;
  }

  /* Texto digitado dentro de Usuário e Senha */
  div[data-testid="stForm"] input {
    height:__FIELD_HEIGHT__px !important;
    min-height:__FIELD_HEIGHT__px !important;
    line-height:normal !important;
    padding:0 __FIELD_PADDING_X__px !important;
    margin:0 !important;
    display:flex !important;
    align-items:center !important;
    box-sizing:border-box !important;
    font-size:13px !important;
  }

  /* Botão do olho da senha — mesma altura do campo e centralizado */
  div[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] button {
    width:__EYE_WIDTH__px !important;
    min-width:__EYE_WIDTH__px !important;
    height:__FIELD_HEIGHT__px !important;
    min-height:__FIELD_HEIGHT__px !important;
    flex:0 0 __EYE_WIDTH__px !important;
    margin:0 !important;
    padding:0 !important;
    position:static !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    box-sizing:border-box !important;
  }

  div[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] button svg {
    width:17px !important;
    height:17px !important;
    margin:0 !important;
    display:block !important;
  }

  div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
    height:__BUTTON_HEIGHT__px !important;
    min-height:__BUTTON_HEIGHT__px !important;
    margin-top:10px !important;
  }

  @media (max-width:480px) {
    .setta-login-wrap { width:360px !important; }
    div[data-testid="stForm"] { width:312px !important; }
  }
</style>
'''

_login_final_css = (
    _login_final_css
    .replace('__CARD_WIDTH__', '__CFG_CARD_WIDTH__')
    .replace('__CARD_HEIGHT__', '__CFG_CARD_HEIGHT__')
    .replace('__LOGO_AREA_HEIGHT__', '__CFG_LOGO_AREA_HEIGHT__')
    .replace('__LOGO_MAX_WIDTH__', '__CFG_LOGO_MAX_WIDTH__')
    .replace('__LOGO_MAX_HEIGHT__', '__CFG_LOGO_MAX_HEIGHT__')
    .replace('__LOGO_PADDING_TOP__', '__CFG_LOGO_PADDING_TOP__')
    .replace('__TITLE_PADDING_TOP__', '__CFG_TITLE_PADDING_TOP__')
    .replace('__TITLE_AREA_HEIGHT__', '__CFG_TITLE_AREA_HEIGHT__')
    .replace('__TITLE_FONT_SIZE__', '__CFG_TITLE_FONT_SIZE__')
    .replace('__FORM_OFFSET_Y__', '__CFG_FORM_OFFSET_Y__')
    .replace('__FORM_WIDTH__', '__CFG_FORM_WIDTH__')
    .replace('__FIELD_HEIGHT__', '__CFG_FIELD_HEIGHT__')
    .replace('__FIELD_GAP__', '__CFG_FIELD_GAP__')
    .replace('__FIELD_PADDING_X__', '__CFG_FIELD_PADDING_X__')
    .replace('__EYE_WIDTH__', '__CFG_EYE_WIDTH__')
    .replace('__BUTTON_HEIGHT__', '__CFG_BUTTON_HEIGHT__')
)

if _login_final_anchor not in _source:
    raise RuntimeError('Ponto final do login não encontrado para aplicar CSS definitivo.')

_login_final_injection = '    st.markdown(' + repr(_login_final_css) + ', unsafe_allow_html=True)\n'
_source = _source.replace(_login_final_anchor, _login_final_injection + _login_final_anchor, 1)
"""

LOGIN_SPACING_PATCH = (
    LOGIN_SPACING_PATCH
    .replace('__CFG_CARD_WIDTH__', str(LOGIN_CARD_WIDTH))
    .replace('__CFG_CARD_HEIGHT__', str(LOGIN_CARD_HEIGHT))
    .replace('__CFG_LOGO_AREA_HEIGHT__', str(LOGIN_LOGO_AREA_HEIGHT))
    .replace('__CFG_LOGO_MAX_WIDTH__', str(LOGIN_LOGO_MAX_WIDTH))
    .replace('__CFG_LOGO_MAX_HEIGHT__', str(LOGIN_LOGO_MAX_HEIGHT))
    .replace('__CFG_LOGO_PADDING_TOP__', str(LOGIN_LOGO_PADDING_TOP))
    .replace('__CFG_TITLE_PADDING_TOP__', str(LOGIN_TITLE_PADDING_TOP))
    .replace('__CFG_TITLE_AREA_HEIGHT__', str(LOGIN_TITLE_AREA_HEIGHT))
    .replace('__CFG_TITLE_FONT_SIZE__', str(LOGIN_TITLE_FONT_SIZE))
    .replace('__CFG_FORM_OFFSET_Y__', str(LOGIN_FORM_OFFSET_Y))
    .replace('__CFG_FORM_WIDTH__', str(LOGIN_FORM_WIDTH))
    .replace('__CFG_FIELD_HEIGHT__', str(LOGIN_FIELD_HEIGHT))
    .replace('__CFG_FIELD_GAP__', str(LOGIN_FIELD_GAP))
    .replace('__CFG_FIELD_PADDING_X__', str(LOGIN_FIELD_PADDING_X))
    .replace('__CFG_EYE_WIDTH__', str(LOGIN_EYE_WIDTH))
    .replace('__CFG_BUTTON_HEIGHT__', str(LOGIN_BUTTON_HEIGHT))
)
