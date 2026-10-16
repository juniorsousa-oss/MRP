"""Regressão: navegação nativa sem sobrepor os indicadores do MRP."""
import ast
import runpy
from pathlib import Path

root = Path(__file__).resolve().parents[1]
generated = runpy.run_path(str(root / "scripts" / "validate_generated_mrp.py"))["final"]
tree = ast.parse(generated)
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

assert "_mrp_set_sidebar_page" in functions
assert 'with st.sidebar:' in generated
assert 'with st.popover("☰"' not in generated
assert 'st.container(key="setta_custom_navigation")' not in generated
assert 'initial_sidebar_state="auto"' in generated
assert 'key=f"mrp_nav_btn_{_nav_index}"' in generated
assert "RELATÓRIO MRP" in generated
assert "SEMANA ATUAL" in generated
assert 'st.session_state["_mrp_sidebar_page"]=page' in ast.get_source_segment(
    generated, functions["_mrp_set_sidebar_page"]
)

from mrp_setta_ui_v1_patch import SETTA_UI_V1_PATCH
assert '[data-testid="stHeader"],header[data-testid="stHeader"]{' in SETTA_UI_V1_PATCH
assert 'display:flex!important' in SETTA_UI_V1_PATCH
assert '[data-testid="stSidebar"]{' in SETTA_UI_V1_PATCH
assert 'div[data-baseweb="popover"]:has(.sidebar-brand)' not in SETTA_UI_V1_PATCH
assert 'width:260px!important' not in SETTA_UI_V1_PATCH
assert 'flex-basis:260px!important' not in SETTA_UI_V1_PATCH
print("MRP_SIDEBAR_NATIVA_DESKTOP_MOBILE_OK")
