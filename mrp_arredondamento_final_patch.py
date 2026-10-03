ARREDONDAMENTO_FINAL_PATCH = r'''
# =========================================================
# ARREDONDAMENTO FINAL — DATAFRAMES
# Executado por último para impedir que camadas/patches posteriores
# deixem cantos retos visíveis atrás das tabelas.
# =========================================================

_round_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_round_css = """<style>
/* Remove qualquer caixa externa quadrada que envolva o dataframe. */
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stDataFrame"]),
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stDataFrame"]) {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Recorte definitivo do componente e de todas as camadas imediatas. */
[data-testid="stDataFrame"] {
    position: relative !important;
    border: 1px solid #e5e8ee !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    clip-path: inset(0 round 16px) !important;
    background: #ffffff !important;
    box-shadow: none !important;
    isolation: isolate !important;
}

[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] > div > div,
[data-testid="stDataFrame"] [role="grid"],
[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
    border-radius: inherit !important;
    overflow: hidden !important;
    background-clip: padding-box !important;
}

/* Evita que canvas/área renderizada ultrapasse a curva dos cantos. */
[data-testid="stDataFrame"] canvas,
[data-testid="stDataFrame"] iframe {
    border-radius: inherit !important;
    clip-path: inset(0 round 16px) !important;
}

/* Mascara qualquer resíduo de fundo quadrado nos quatro cantos. */
[data-testid="stDataFrame"]::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 16px;
    pointer-events: none;
    box-shadow: inset 0 0 0 1px #e5e8ee;
    z-index: 999;
}
</style>"""
_round_code = 'st.markdown(' + repr(_round_css) + ', unsafe_allow_html=True)\n'
if _round_anchor in _source:
    _source = _source.replace(_round_anchor, _round_code + _round_anchor, 1)
else:
    raise RuntimeError("Ponto final do layout não encontrado para arredondamento definitivo.")
'''
