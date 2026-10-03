SETTA_UI_V1_PATCH = r'''
# =========================================================
# SETTA UI — PADRÃO OFICIAL DO CONVERSOR MRP
# App Shell Rounded V1 + Sidebar Operacional V1
# + Header Superior V1 + Light Lock V1
# =========================================================
# Esta camada é somente estrutural/visual. Não altera cálculos,
# filtros, persistência, banco, integrações ou regras de negócio.

# 1) Mantém o DOM da sidebar disponível, como no Conversor MRP.
_page_cfg_old = 'st.set_page_config(page_title="MRP | SETTA", page_icon="assets/mrp_setta_icon.png", layout="wide")'
_page_cfg_new = 'st.set_page_config(page_title="MRP | SETTA", page_icon="assets/mrp_setta_icon.png", layout="wide", initial_sidebar_state="expanded")'
if _page_cfg_old in _source:
    _source = _source.replace(_page_cfg_old, _page_cfg_new, 1)

# 2) Navegação fecha o drawer depois da escolha.
_old_nav_fn = 'def _mrp_set_sidebar_page(page):\n    st.session_state["_mrp_sidebar_page"]=page\n'
_new_nav_fn = 'def _mrp_set_sidebar_page(page):\n    st.session_state["_mrp_sidebar_page"]=page\n    _setta_close_sidebar()\n'
if _old_nav_fn in _source:
    _source = _source.replace(_old_nav_fn, _new_nav_fn, 1)

# 3) Drawer SETTA. A injeção no runtime acontece junto com o CSS,
# antes da sidebar e do cabeçalho, para eliminar layout shift.
_drawer_runtime = """def _setta_sidebar_is_open() -> bool:
    return bool(st.session_state.get("_setta_sidebar_open", False))

def _setta_toggle_sidebar() -> None:
    st.session_state["_setta_sidebar_open"] = not _setta_sidebar_is_open()

def _setta_close_sidebar() -> None:
    st.session_state["_setta_sidebar_open"] = False

_setta_sidebar_open = _setta_sidebar_is_open()
if not _setta_sidebar_open:
    st.markdown(
        '<style>'
        'section[data-testid="stSidebar"]{display:none!important;}'
        '[data-testid="stSidebarCollapseButton"],'
        '[data-testid="stSidebarCollapsedControl"],'
        'button[data-testid="stSidebarCollapseButton"]{display:none!important;}'
        '</style>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<style>'
        '[data-testid="stSidebarCollapseButton"],'
        '[data-testid="stSidebarCollapsedControl"],'
        'button[data-testid="stSidebarCollapseButton"]{display:none!important;}'
        '</style>',
        unsafe_allow_html=True,
    )

with st.container(key="setta_top_controls"):
    st.button(
        "☰",
        key="setta_drawer_toggle",
        help="Abrir/fechar menu",
        use_container_width=True,
        on_click=_setta_toggle_sidebar,
    )

"""

# 4) CSS canônico do shell SETTA.
# Esta é a única camada responsável por moldura, cabeçalho, menu superior e lateral.
_setta_css = """<style>
:root{
  color-scheme:light!important;
  --setta-outer:#EEF3F8;
  --setta-app:#F4F7FB;
  --setta-surface:#FFFFFF;
  --setta-text:#111827;
  --setta-muted:#667085;
  --setta-border:#E5E8EE;
  --setta-red:#EF4444;
}

/* SETTA UI — App Shell Rounded V1 */
html,body,#root{
  height:100%!important;
  min-height:100%!important;
  max-height:100%!important;
  overflow:hidden!important;
}
html,body{
  background:#EEF3F8!important;
  background-image:none!important;
}
body{
  box-sizing:border-box!important;
  padding:18px!important;
  margin:0!important;
  overflow:hidden!important;
}
.stApp,
[data-testid="stApp"]{
  position:relative!important;
  inset:auto!important;
  width:calc(100vw - 36px)!important;
  height:calc(100vh - 36px)!important;
  min-height:0!important;
  max-height:calc(100vh - 36px)!important;
  max-width:1680px!important;
  margin:0 auto!important;
  border:1px solid rgba(202,214,228,.9)!important;
  border-radius:24px!important;
  overflow:hidden!important;
  background:#F8FAFD!important;
  background-image:none!important;
  box-shadow:0 24px 70px rgba(15,27,45,.13)!important;
}
[data-testid="stAppViewContainer"]{
  position:relative!important;
  inset:auto!important;
  width:100%!important;
  height:100%!important;
  min-height:0!important;
  max-height:100%!important;
  border-radius:24px!important;
  overflow:hidden!important;
  background:#F4F7FB!important;
  background-image:none!important;
}
[data-testid="stMain"],
.stMain,
section.main{
  position:relative!important;
  height:100%!important;
  min-height:0!important;
  max-height:100%!important;
  overflow-x:hidden!important;
  overflow-y:auto!important;
  background:#F4F7FB!important;
  background-image:none!important;
  scrollbar-width:thin!important;
  scrollbar-color:#CAD5E3 transparent!important;
}
[data-testid="stMain"]::-webkit-scrollbar,
.stMain::-webkit-scrollbar,
section.main::-webkit-scrollbar{width:9px!important}
[data-testid="stMain"]::-webkit-scrollbar-track,
.stMain::-webkit-scrollbar-track,
section.main::-webkit-scrollbar-track{background:transparent!important}
[data-testid="stMain"]::-webkit-scrollbar-thumb,
.stMain::-webkit-scrollbar-thumb,
section.main::-webkit-scrollbar-thumb{
  background:#CAD5E3!important;
  border-radius:999px!important;
}
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"]{
  height:auto!important;
  min-height:100%!important;
  max-height:none!important;
  overflow:visible!important;
  padding-bottom:48px!important;
}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
header[data-testid="stHeader"]{
  display:none!important;
  visibility:hidden!important;
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
}
.block-container{
  max-width:1780px!important;
  width:100%!important;
  padding-top:18px!important;
  padding-left:2.7rem!important;
  padding-right:2.7rem!important;
  padding-bottom:32px!important;
}

/* SETTA UI — Top Controls V1: medidas idênticas ao Conversor MRP */
.st-key-setta_top_controls{
  position:absolute!important;
  top:18px!important;
  left:44px!important;
  z-index:120!important;
  width:82px!important;
  margin:0!important;
  padding:0!important;
}
.st-key-setta_top_controls [data-testid="stVerticalBlock"]{gap:0!important}
.st-key-setta_drawer_toggle{
  width:82px!important;
  margin:0!important;
  padding:0!important;
}
.st-key-setta_drawer_toggle button{
  position:relative!important;
  width:82px!important;
  min-height:42px!important;
  height:42px!important;
  border-radius:10px!important;
  padding:0!important;
  background:rgba(255,255,255,.96)!important;
  color:#111827!important;
  box-shadow:0 2px 8px rgba(15,23,42,.06)!important;
}
.st-key-setta_drawer_toggle button p{
  font-size:0!important;
  line-height:0!important;
  margin:0!important;
  padding:0!important;
}
.st-key-setta_drawer_toggle button::after{
  content:""!important;
  position:absolute!important;
  left:50%!important;
  top:50%!important;
  width:14px!important;
  height:1.5px!important;
  border-radius:999px!important;
  background:#111827!important;
  box-shadow:0 -5px 0 #111827,0 5px 0 #111827!important;
  transform:translate(-50%,-50%)!important;
}

/* SETTA UI — Integração da Sidebar com o App Shell */
section[data-testid="stSidebar"]{
  align-self:stretch!important;
  height:100%!important;
  min-height:100%!important;
  max-height:100%!important;
  background:#fff!important;
  background-image:none!important;
  border-right:1px solid #e8ebf0!important;
  border-radius:24px 0 0 24px!important;
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  flex:0 0 260px!important;
  flex-basis:260px!important;
  overflow-x:hidden!important;
  overflow-y:auto!important;
  scrollbar-width:thin!important;
  scrollbar-color:#D6DEE8 transparent!important;
}
section[data-testid="stSidebar"]>div{
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  min-height:100%!important;
  height:auto!important;
  box-sizing:border-box!important;
}
section[data-testid="stSidebar"] .block-container{
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  box-sizing:border-box!important;
  padding-top:26px!important;
  padding-left:16px!important;
  padding-right:16px!important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
  gap:0!important;
  row-gap:0!important;
}
.sidebar-brand{
  width:100%!important;
  background:#f8fafc!important;
  border:1px solid #e5e8ee!important;
  border-radius:12px!important;
  padding:14px 16px!important;
  margin:0 0 20px 0!important;
}
.sidebar-brand-title{
  margin:0!important;
  padding:0!important;
  font-size:15px!important;
  font-weight:800!important;
  line-height:18px!important;
  color:#111827!important;
  letter-spacing:-.01em!important;
}
.sidebar-brand-sub{
  margin:3px 0 0 0!important;
  padding:0!important;
  font-size:12px!important;
  font-weight:400!important;
  line-height:16px!important;
  color:#6b7280!important;
}
.sidebar-section-label{
  display:block!important;
  margin:0 0 8px 0!important;
  padding:0!important;
  color:#374151!important;
  font-size:12px!important;
  line-height:15px!important;
  font-weight:800!important;
  text-transform:uppercase!important;
  letter-spacing:.055em!important;
}
section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.sidebar-section-label){
  margin:0!important;
  padding:0!important;
}
section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(div[data-testid="stButton"]){
  margin-bottom:0!important;
  padding:0!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"]{
  margin:0 0 2px 0!important;
  padding:0!important;
}
section[data-testid="stSidebar"] .st-key-mrp_nav_btn_0{
  margin-top:8px!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button{
  position:relative!important;
  width:100%!important;
  min-height:42px!important;
  height:42px!important;
  max-height:42px!important;
  margin:0!important;
  padding:0 12px 0 24px!important;
  border-radius:10px!important;
  justify-content:flex-start!important;
  text-align:left!important;
  box-shadow:none!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button > div{
  width:100%!important;
  justify-content:flex-start!important;
  text-align:left!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button p{
  width:100%!important;
  margin:0!important;
  padding:0!important;
  text-align:left!important;
  font-size:13px!important;
  line-height:16px!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-secondary"]{
  background:transparent!important;
  border:1px solid transparent!important;
  color:#374151!important;
  font-weight:500!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-secondary"]:hover{
  background:#f8fafc!important;
  border-color:#e5e7eb!important;
  color:#111827!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]{
  background:#111827!important;
  border:1px solid #111827!important;
  color:#fff!important;
  font-weight:700!important;
  box-shadow:0 5px 14px rgba(17,24,39,.14)!important;
}
section[data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]::before{
  content:""!important;
  position:absolute!important;
  left:7px!important;
  top:50%!important;
  width:4px!important;
  height:20px!important;
  border-radius:999px!important;
  background:#ef4444!important;
  transform:translateY(-50%)!important;
}
.sidebar-divider{
  display:block!important;
  width:100%!important;
  height:1px!important;
  min-height:1px!important;
  background:#d1d5db!important;
  margin:18px 0 20px 0!important;
  padding:0!important;
}
.sidebar-status-card,
.sidebar-week-card{
  width:100%!important;
  background:#f8fafc!important;
  border:1px solid #e5e8ee!important;
  border-radius:10px!important;
  padding:12px 14px!important;
  margin:0!important;
  color:#6b7280!important;
}
.sidebar-status-name,
.sidebar-week-label{
  margin:0!important;
  padding:0!important;
  font-size:11px!important;
  line-height:14px!important;
  font-weight:800!important;
  color:#64748b!important;
  text-transform:uppercase!important;
  letter-spacing:.025em!important;
}
.sidebar-status-value{
  margin:4px 0 0 0!important;
  padding:0!important;
  font-size:13px!important;
  line-height:16px!important;
  font-weight:900!important;
  text-transform:uppercase!important;
}
.sidebar-status-value.status-ok{color:#16a34a!important}
.sidebar-status-value.status-warning{color:#f59e0b!important}
.sidebar-status-value.status-error{color:#ef4444!important}
.sidebar-status-meta{
  margin:6px 0 0 0!important;
  padding:0!important;
  color:#6b7280!important;
  font-size:11px!important;
  line-height:15px!important;
  text-transform:uppercase!important;
}
.sidebar-subdivider{
  width:100%!important;
  height:1px!important;
  min-height:1px!important;
  background:#d1d5db!important;
  margin:12px 0!important;
}
.sidebar-week-value{
  margin:5px 0 0 0!important;
  padding:0!important;
  color:#111827!important;
  font-size:13px!important;
  line-height:16px!important;
  font-weight:900!important;
  text-transform:uppercase!important;
}
/* SETTA UI — Sidebar Operacional V1 */

/* SETTA UI — Header Superior V1: medidas exatas do Conversor MRP */
.setta-logo-card,
.setta-brand{
  width:100%!important;
  min-height:150px!important;
  height:150px!important;
  max-height:150px!important;
  flex:0 0 150px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  background:#fff!important;
  background-image:none!important;
  border:1px solid #e5e8ee!important;
  border-radius:18px!important;
  box-shadow:0 4px 14px rgba(24,39,75,.08)!important;
  box-sizing:border-box!important;
  margin:0 0 24px 0!important;
  padding:18px 24px!important;
}
.setta-logo-card img,
.setta-brand-logo img{
  display:block!important;
  width:auto!important;
  height:auto!important;
  max-width:220px!important;
  max-height:90px!important;
  object-fit:contain!important;
  margin:0!important;
}
/* Mobile idêntico ao princípio do Conversor: shell ocupa a tela. */
@media(max-width:900px){
  html,body,#root{
    height:auto!important;
    min-height:100%!important;
    max-height:none!important;
    overflow-y:auto!important;
  }
  body{
    padding:0!important;
    background:#F5F8FC!important;
    overflow-y:auto!important;
  }
  .stApp,
  [data-testid="stApp"]{
    width:100vw!important;
    height:auto!important;
    min-height:100vh!important;
    max-height:none!important;
    max-width:none!important;
    border:0!important;
    border-radius:0!important;
    box-shadow:none!important;
  }
  [data-testid="stAppViewContainer"]{
    height:auto!important;
    min-height:100vh!important;
    max-height:none!important;
    border-radius:0!important;
  }
  [data-testid="stMain"],
  .stMain,
  section.main{
    height:auto!important;
    min-height:100vh!important;
    max-height:none!important;
    overflow-y:visible!important;
  }
  .block-container{
    padding-top:18px!important;
    padding-left:1rem!important;
    padding-right:1rem!important;
    padding-bottom:2rem!important;
  }
  section[data-testid="stSidebar"]{border-radius:0!important}
  .st-key-setta_top_controls{
    top:14px!important;
    left:16px!important;
  }
  .setta-logo-card,
  .setta-brand{
    min-height:105px!important;
    height:105px!important;
    max-height:105px!important;
    flex:0 0 105px!important;
    margin-bottom:1.8rem!important;
    padding:.9rem 1rem!important;
  }
  .setta-logo-card img,
  .setta-brand-logo img{
    max-width:170px!important;
    max-height:72px!important;
  }
}
</style>"""

_shell_anchor = '_mrp_role=st.session_state.get("auth_role")\n'
if _shell_anchor not in _source:
    raise RuntimeError("Ponto de montagem da sidebar não encontrado para SETTA UI.")

_shell_bootstrap = (
    'st.markdown(' + repr(_setta_css) + ', unsafe_allow_html=True)\n'
    + _drawer_runtime
)
_source = _source.replace(
    _shell_anchor,
    _shell_bootstrap + _shell_anchor,
    1,
)
'''
