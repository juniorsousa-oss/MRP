FILTROS_VISUAL_PATCH = r"""
# =========================================================
# FILTROS OPERACIONAIS — PADRÃO VISUAL GESTÃO DE ENTREGAS
# =========================================================
# Aplica o visual apenas aos formulários operacionais do MRP.
# O formulário de login é excluído pelo seletor :not(:has(input[type="password"])).

_filtros_visual_anchor = '_apply_visual_theme(UI_CONFIG)\n'
_filtros_visual_injection = '''_apply_visual_theme(UI_CONFIG)
st.markdown("""
<style>
/* Bloco dos filtros */
div[data-testid="stForm"]:not(:has(input[type="password"])) {
    background:#f8fafc !important;
    border:1px solid #cbd5e1 !important;
    border-radius:8px !important;
    padding:12px 12px 12px 12px !important;
    box-shadow:none !important;
    margin-bottom:.65rem !important;
}

/* Rótulos */
div[data-testid="stForm"]:not(:has(input[type="password"])) label,
div[data-testid="stForm"]:not(:has(input[type="password"])) [data-testid="stWidgetLabel"] p {
    color:#1f2937 !important;
    font-size:.82rem !important;
    font-weight:500 !important;
}

/* Selectbox e multiselect */
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-baseweb="select"] > div {
    background:#f1f3f6 !important;
    border-color:transparent !important;
    border-radius:6px !important;
    min-height:36px !important;
    box-shadow:none !important;
}

/* Campos de texto */
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-baseweb="input"] {
    background:#f1f3f6 !important;
    border-color:transparent !important;
    border-radius:6px !important;
    min-height:36px !important;
    box-shadow:none !important;
}
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-baseweb="input"] input {
    background:transparent !important;
    color:#20252b !important;
}
div[data-testid="stForm"]:not(:has(input[type="password"])) input::placeholder {
    color:#8a94a3 !important;
    opacity:1 !important;
}

/* Foco discreto */
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-baseweb="select"] > div:focus-within,
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-baseweb="input"]:focus-within {
    border:1px solid #aab2bd !important;
    box-shadow:none !important;
}

/* Botão principal — preto */
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background:#111111 !important;
    border:1px solid #111111 !important;
    color:#ffffff !important;
    border-radius:6px !important;
    min-height:34px !important;
    font-weight:650 !important;
    box-shadow:none !important;
}
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    background:#222222 !important;
    border-color:#222222 !important;
    color:#ffffff !important;
}

/* Botão limpar — claro */
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-testid="stFormSubmitButton"] button[kind="secondary"] {
    background:#ffffff !important;
    border:1px solid #cbd5e1 !important;
    color:#5b6470 !important;
    border-radius:6px !important;
    min-height:34px !important;
    font-weight:500 !important;
    box-shadow:none !important;
}
div[data-testid="stForm"]:not(:has(input[type="password"])) div[data-testid="stFormSubmitButton"] button[kind="secondary"]:hover {
    background:#f5f6f8 !important;
    border-color:#aeb6c2 !important;
    color:#222222 !important;
}

/* Reduz espaços internos para ficar próximo ao modelo */
div[data-testid="stForm"]:not(:has(input[type="password"])) [data-testid="stVerticalBlock"] {
    gap:.65rem !important;
}
</style>
""", unsafe_allow_html=True)
'''

if _filtros_visual_anchor not in _source:
    raise RuntimeError("Ponto do tema não encontrado para aplicar o padrão visual dos filtros.")
_source = _source.replace(_filtros_visual_anchor, _filtros_visual_injection, 1)
"""
