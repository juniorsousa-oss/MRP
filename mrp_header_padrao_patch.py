HEADER_PADRAO_PATCH = r'''
# =========================================================
# CABEÇALHO PRINCIPAL — PADRÃO GESTÃO DE ENTREGAS
# =========================================================
_header_anchor = '_render_brand_header(UI_CONFIG)\n'
_header_final_css = '<style>div[data-testid="stElementContainer"]:has(.setta-brand){margin-bottom:-1.70rem !important}.app-title{margin:0 !important;padding:0 !important;font-size:2.55rem !important;line-height:1.08 !important;font-weight:800 !important;letter-spacing:-0.04em !important;color:#050505 !important}.app-subtitle,.app-sub{margin-top:.72rem !important;margin-bottom:1.65rem !important;color:#4f5661 !important;font-size:.94rem !important;line-height:1.35 !important}@media(max-width:900px){div[data-testid="stElementContainer"]:has(.setta-brand){margin-bottom:-1rem !important}.app-title{font-size:2rem !important}}</style>'
_header_injection = '_render_brand_header(UI_CONFIG)\n' + 'st.markdown(' + repr(_header_final_css) + ', unsafe_allow_html=True)\n'
if _header_anchor not in _source:
    raise RuntimeError("Ponto do cabeçalho principal não encontrado para padronização.")
_source = _source.replace(_header_anchor, _header_injection, 1)
'''
