ARREDONDAMENTO_FINAL_PATCH = r'''
# =========================================================
# ARREDONDAMENTO FINAL — DATAFRAMES
# Executado por último para impedir que camadas/patches posteriores
# deixem cantos retos visíveis atrás das tabelas.
# =========================================================

_round_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_round_css = """<style>
/* Uniformiza o fundo final para que nenhum canto de wrapper fique aparente. */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"],
.stMain,
.block-container {
    background: #F4F7FB !important;
    background-image: none !important;
}

/* Remove fundo/borda de TODOS os wrappers de layout que contenham dataframe. */
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stDataFrame"]),
div[data-testid="stVerticalBlock"]:has([data-testid="stDataFrame"]),
div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"]),
div[data-testid="column"]:has([data-testid="stDataFrame"]),
div.stColumn:has([data-testid="stDataFrame"]) {
    background: transparent !important;
    background-image: none !important;
    border: 0 !important;
    box-shadow: none !important;
    outline: 0 !important;
}

/* Qualquer pseudo-elemento de wrapper também deve desaparecer. */
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"])::after,
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stDataFrame"])::before,
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stDataFrame"])::after {
    display: none !important;
    content: none !important;
}

/* Remove qualquer caixa externa quadrada que envolva o dataframe. */
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stDataFrame"]),
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stDataFrame"]) {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* O Streamlit/Glide mantém uma camada retangular atrás do grid.
   A máscara no element-container elimina especificamente esse resíduo. */
div[data-testid="stElementContainer"]:has(> div [data-testid="stDataFrame"]) {
    position: relative !important;
    overflow: visible !important;
}

/* Faz o fundo imediatamente atrás do grid ser exatamente o fundo da página. */
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]) > div,
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]) > div > div {
    background: transparent !important;
    background-image: none !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Máscara física nos cantos esquerdos: cobre qualquer pixel quadrado
   renderizado pelo viewport/canvas que escape do border-radius. */
[data-testid="stDataFrame"] {
    -webkit-mask-image:
      radial-gradient(circle at 16px 16px, #000 15.5px, transparent 16px),
      linear-gradient(#000 0 0);
    -webkit-mask-composite: source-over;
    mask-image: none;
}

/* Sobreposição final, da cor do fundo, somente fora da curva. */
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"])::before {
    content:"" !important;
    display:block !important;
    position:absolute !important;
    left:0 !important;
    bottom:0 !important;
    width:18px !important;
    height:18px !important;
    pointer-events:none !important;
    z-index:10000 !important;
    background:
      radial-gradient(circle at 18px 0, transparent 17px, #F4F7FB 17.5px) !important;
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
