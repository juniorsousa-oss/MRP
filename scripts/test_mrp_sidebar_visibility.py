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
assert 'initial_sidebar_state="collapsed"' in generated
assert 'key=f"mrp_nav_btn_{_nav_index}"' in generated
assert "RELATÓRIO MRP" in generated
assert "SEMANA ATUAL" in generated
assert 'st.session_state["_mrp_sidebar_page"]=page' in ast.get_source_segment(
    generated, functions["_mrp_set_sidebar_page"]
)

from mrp_setta_ui_v1_patch import SETTA_UI_V1_PATCH
assert '[data-testid="stHeader"],header[data-testid="stHeader"]{' in SETTA_UI_V1_PATCH
assert "pointer-events:auto!important" in SETTA_UI_V1_PATCH
assert '[data-testid="stSidebarCollapsedControl"]' in SETTA_UI_V1_PATCH
assert '[data-testid="collapsedControl"]' in SETTA_UI_V1_PATCH
assert 'display:flex!important' in SETTA_UI_V1_PATCH
assert '[data-testid="stSidebar"]{' in SETTA_UI_V1_PATCH
assert 'div[data-baseweb="popover"]:has(.sidebar-brand)' not in SETTA_UI_V1_PATCH
assert 'width:260px!important' not in SETTA_UI_V1_PATCH
assert 'flex-basis:260px!important' not in SETTA_UI_V1_PATCH
# Conta acessível no menu nativo, sem limitar a ADMIN/CONSULTA/OPERADOR.
assert generated.count('key="mrp_logout_sidebar"') == 1
assert '<div class="sidebar-section-label">MINHA CONTA</div>' in generated
assert "USUÁRIO CONECTADO" in generated
assert 'st.session_state.get("auth_nome")' in generated
assert 'st.session_state.get("auth_role")' in generated
assert 'st.session_state.get("auth_email")' in generated
assert "_mrp_escape_html(_mrp_account_name)" in generated
assert "_mrp_escape_html(_mrp_account_email)" in generated
assert "sidebar-account-card" in SETTA_UI_V1_PATCH
assert ".st-key-mrp_logout_sidebar button" in SETTA_UI_V1_PATCH
logout_buttons = [n for n in ast.walk(tree) if isinstance(n, ast.If)
    and isinstance(n.test, ast.Call)
    and isinstance(n.test.func, ast.Attribute)
    and n.test.func.attr == "button"
    and any(kw.arg == "key" and isinstance(kw.value, ast.Constant)
        and kw.value.value == "mrp_logout_sidebar" for kw in n.test.keywords)]
assert len(logout_buttons) == 1
assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    and n.func.id == "_logout" for n in ast.walk(logout_buttons[0]))
assert "_logout" in functions

# Logout deve apagar dados de autenticação e forçar retorno ao login.
class FakeStreamlit:
    def __init__(self):
        self.session_state = {key:"teste" for key in
            ("auth_access_token","auth_refresh_token","auth_user_id",
             "auth_email","auth_nome","auth_role")}
        self.session_state["outro_estado"] = "preservado"
        self.rerun_called = False
    def rerun(self):
        self.rerun_called = True

st = FakeStreamlit()
logout_module = ast.Module(body=[functions["_logout"]], type_ignores=[])
scope = {"st": st}
exec(compile(ast.fix_missing_locations(logout_module), "<logout>", "exec"), scope)
scope["_logout"]()
assert st.rerun_called
assert st.session_state == {"outro_estado":"preservado"}
print("MRP_SIDEBAR_NATIVA_CONTA_E_LOGOUT_OK")
