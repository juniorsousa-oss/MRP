"""Regressão do layout mobile do shell SETTA sem executar a aplicação."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
generated=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
ast.parse(generated)

from mrp_setta_ui_v1_patch import SETTA_UI_V1_PATCH
prefix='_setta_css = """<style>'
assert SETTA_UI_V1_PATCH.count(prefix)==1
shell=SETTA_UI_V1_PATCH.split(prefix,1)[1].split('</style>"""',1)[0]
assert shell.count("{")==shell.count("}"),"CSS com chaves divergentes"
assert shell.count("@media (max-width:900px)")>=1
mobile=shell[shell.index("/* SETTA MRP — RESPONSIVIDADE MOBILE"):]

# A sidebar nativa e o painel principal não recebem dimensões impostas.
# Isso evita a coluna invisível que empurra os cartões no Safari iOS.
assert "flex-direction:row!important;" not in mobile
assert "flex-basis:100%!important;" not in mobile
assert "max-width:min(86vw,300px)!important" not in mobile
assert "position:fixed!important" not in mobile.split(
    'section[data-testid="stSidebar"]>div,',1)[0]
assert "display:block!important;" not in mobile.split(
    'section[data-testid="stSidebar"]>div,',1)[0]

# A página e os blocos devem ocupar 100% do viewport.
for selector in (
    '[data-testid="stAppViewContainer"]',
    '[data-testid="stMain"]',
    '[data-testid="stMainBlockContainer"]',
    '[data-testid="stAppViewBlockContainer"]',
):
    assert selector in mobile,selector
assert "max-width:100vw!important" in mobile
assert "max-width:100%!important" in mobile
assert "min-width:0!important" in mobile
assert "padding:76px 14px 28px!important" in mobile

# A barra nativa não flutua sobre os indicadores nem suprime o controle do header.
assert '[data-testid="stHeader"],header[data-testid="stHeader"]{' in shell
assert 'div[data-baseweb="popover"]:has(.sidebar-brand)' not in shell
assert 'with st.sidebar:' in generated
assert ".setta-logo-card,.setta-brand{" in mobile
assert "min-height:96px!important" in mobile

# Indicadores, cartões, abas e planilhas.
for marker in (
    'div[data-testid="stHorizontalBlock"]',
    'div[data-testid="stColumn"]',
    'div[data-testid="stMetric"]',
    '.mrp-source-grid',
    '.mrp-source-card,.mrp-output-card,.mrp-ped-hero,.mrp-av-hero',
    '[data-testid="stTabs"] [data-baseweb="tab-list"]',
    '[data-testid="stDataFrame"]',
    '@media (min-width:601px) and (max-width:900px)',
):
    assert marker in mobile,marker
assert "flex:1 1 100%!important" in mobile
assert "padding-bottom:calc(32px + env(safe-area-inset-bottom,0px))!important" in mobile

# A montagem global injeta este shell no runtime produzido.
assert "SETTA_UI_V1_PATCH" in (root/"app_mrp.py").read_text("utf-8")
assert "st-key-setta_menu_popover_" not in generated
assert "/* SETTA MRP — RESPONSIVIDADE MOBILE" in generated
print("MRP_MOBILE_SIDEBAR_VIEWPORT_CARDS_OK")
