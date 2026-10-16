"""Menu MRP: abertura/fechamento sem rerun, navegação e estilos originais."""
import ast,runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
generated=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(generated)
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
assert "_setta_close_sidebar" in functions
assert "_mrp_set_sidebar_page" in functions
assert '_setta_close_sidebar()' in ast.get_source_segment(
    generated,functions["_mrp_set_sidebar_page"]
)
# Popover nativo abre e fecha no cliente; sem reexecução ao clicar no ☰.
assert 'with st.popover("☰", width=56,' in generated
assert 'on_change="ignore"' in generated
assert 'key=f"setta_menu_popover_{_setta_menu_revision}"' in generated
assert "with st.container(key=\"setta_custom_navigation\"):" not in generated
assert 'with st.sidebar:' not in ast.get_source_segment(
    generated,functions["_mrp_set_sidebar_page"]
)
assert "key=f\"mrp_nav_btn_{_nav_index}\"" in generated
assert "RELATÓRIO MRP" in generated and "SEMANA ATUAL" in generated

# Alternar a revisão ao mudar página força novo widget/popover recolhido.
class MockST:
    session_state={}
st=MockST()
ns={"st":st}
code=ast.Module(body=[functions["_setta_close_sidebar"]],type_ignores=[])
exec(compile(ast.fix_missing_locations(code),"<menu>","exec"),ns)
close=ns["_setta_close_sidebar"]
close()
assert st.session_state["_setta_menu_revision"]==1
close()
assert st.session_state["_setta_menu_revision"]==2

# Estrutura CSS fixa somente o gatilho (o portal fica sob controle do browser).
from mrp_setta_ui_v1_patch import SETTA_UI_V1_PATCH
assert "position:fixed!important" in SETTA_UI_V1_PATCH
assert '[class*="st-key-setta_menu_popover_"]' in SETTA_UI_V1_PATCH
assert "div[data-baseweb=\"popover\"]:has(.sidebar-brand)" in SETTA_UI_V1_PATCH
assert "width:280px!important" in SETTA_UI_V1_PATCH
assert "min-height:42px!important" in SETTA_UI_V1_PATCH
assert "justify-content:flex-start!important" in SETTA_UI_V1_PATCH
assert "background:#111827!important" in SETTA_UI_V1_PATCH
assert "z-index:10010!important" in SETTA_UI_V1_PATCH
print("MRP_MENU_POPOVER_SEM_RERUN_DESKTOP_MOBILE_OK")
