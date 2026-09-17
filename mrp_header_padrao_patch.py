HEADER_PADRAO_PATCH = r'''
# =========================================================
# CABEÇALHO PRINCIPAL — PADRÃO GESTÃO DE ENTREGAS
# =========================================================
# Aplicado imediatamente antes do título principal para prevalecer sobre
# todos os estilos visuais carregados anteriormente.

_header_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_header_final_css = '<style>.block-container{max-width:1780px!important;padding-top:3.2rem!important;padding-left:2.7rem!important;padding-right:2.7rem!important;padding-bottom:3rem!important;width:100%!important}.setta-brand{width:100%!important;min-height:128px!important;display:flex!important;align-items:center!important;justify-content:center!important;background:#fff!important;border:1px solid #e5e8ee!important;border-radius:16px!important;box-shadow:0 4px 14px rgba(24,39,75,.08)!important;box-sizing:border-box!important;margin:0 0 1.45rem 0!important;padding:1.1rem 2rem!important}.setta-brand-logo{width:100%!important;display:flex!important;align-items:center!important;justify-content:center!important}.setta-brand-logo img{display:block!important;width:auto!important;height:auto!important;max-width:205px!important;max-height:86px!important;object-fit:contain!important;margin:0!important}div[data-testid="stElementContainer"]:has(.app-title){margin-top:-2rem!important}.app-title{margin:0!important;padding:0!important;font-size:2.55rem!important;line-height:1.08!important;font-weight:800!important;letter-spacing:-.04em!important;color:#050505!important}.app-subtitle,.app-sub{margin-top:.72rem!important;margin-bottom:1.65rem!important;color:#4f5661!important;font-size:.94rem!important;line-height:1.35!important}@media(max-width:900px){.block-container{padding-top:2rem!important;padding-left:1rem!important;padding-right:1rem!important}.setta-brand{min-height:105px!important;margin-bottom:1rem!important}.setta-brand-logo img{max-width:170px!important;max-height:72px!important}div[data-testid="stElementContainer"]:has(.app-title){margin-top:-1.25rem!important}.app-title{font-size:2rem!important}}</style>'
_header_injection = 'st.markdown(' + repr(_header_final_css) + ', unsafe_allow_html=True)\n' + _header_anchor
if _header_anchor not in _source:
    raise RuntimeError("Ponto do título principal não encontrado para padronização final do cabeçalho.")
_source = _source.replace(_header_anchor, _header_injection, 1)
'''
