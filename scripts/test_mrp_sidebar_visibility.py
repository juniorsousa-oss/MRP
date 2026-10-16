"""Regressão da visibilidade do menu em desktop/mobile e após navegar."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
codigo=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(codigo)
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for name in (
    "_setta_sidebar_mode",
    "_setta_toggle_sidebar_desktop",
    "_setta_toggle_sidebar_mobile",
    "_setta_close_sidebar",
    "_mrp_set_sidebar_page",
):
    assert name in functions,name
# Navegação não deve depender de st.sidebar nem da detecção do navegador.
assert 'if _setta_sidebar_mode_current=="open":' in codigo
assert 'with st.container(key="setta_custom_navigation"):' in codigo
assert 'section[data-testid="stSidebar"]{' in codigo
assert 'display:none!important' in codigo
assert 'section[data-testid="stSidebar"]{display:flex!important;}' not in codigo
assert 'key="setta_drawer_toggle"' in codigo
assert 'key="setta_drawer_toggle_mobile"' in codigo
assert 'on_click=_setta_toggle_sidebar_desktop' in codigo
assert 'on_click=_setta_toggle_sidebar_mobile' in codigo
assert 'st.session_state["_setta_sidebar_mode"]="closed"' in codigo
assert '_setta_close_sidebar()' in ast.get_source_segment(
    codigo,functions["_mrp_set_sidebar_page"]
)
# A sidebar interna foi substituída, com os controles/status preservados.
assert 'with st.container(key="setta_custom_navigation"):' in codigo
assert 'key=f"mrp_nav_btn_{_nav_index}"' in codigo
assert 'RELATÓRIO MRP' in codigo
assert 'SEMANA ATUAL' in codigo
assert "position:fixed!important" in codigo
assert "z-index:500!important" in codigo
assert "z-index:10010!important" in codigo

class St:
    session_state={}
st=St()
ns={"st":st}
code=ast.Module(body=[functions[name] for name in (
    "_setta_sidebar_mode",
    "_setta_toggle_sidebar_desktop",
    "_setta_toggle_sidebar_mobile",
    "_setta_close_sidebar",
)],type_ignores=[])
exec(compile(ast.fix_missing_locations(code),"<sidebar>","exec"),ns)

mode=ns["_setta_sidebar_mode"]
desktop=ns["_setta_toggle_sidebar_desktop"]
mobile=ns["_setta_toggle_sidebar_mobile"]
reset=ns["_setta_close_sidebar"]
assert mode()=="closed" # Primeiro acesso SEMPRE fechado.
desktop()
assert mode()=="open" # O botão abre no computador.
desktop()
assert mode()=="closed" # O botão também fecha.
mobile()
assert mode()=="open" # O botão abre no celular.
reset()
assert mode()=="closed" # A navegação fecha também no celular.
desktop()
assert mode()=="open"
reset()
assert mode()=="closed" # A navegação fecha também no desktop.
mobile()
assert mode()=="open"
mobile()
assert mode()=="closed"
# Sessões antigas em "auto" precisam iniciar recolhidas após o upgrade.
st.session_state["_setta_sidebar_mode"]="auto"
assert mode()=="closed"
assert "position:fixed!important" in codigo
assert "z-index:10010!important" in codigo

print("MRP_SIDEBAR_AUTO_DESKTOP_MOBILE_NAVIGATION_OK")
