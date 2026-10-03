SETTA_UI_V1_PATCH = r'''
# =========================================================
# SETTA UI — PADRÃO OFICIAL DO CONVERSOR MRP
# App Shell Rounded V1 + Sidebar Operacional V1
# + Header Superior V1 + Light Lock V1
# =========================================================

# O Runtime Load Once V1 já é proprietário do bundle da Central no patch
# funcional anterior. Esta camada não altera carga, cálculos ou persistência.

_sidebar_role_anchor = '_mrp_role=st.session_state.get("auth_role")\n'
_sidebar_helpers = """def _setta_sidebar_is_open():
    return bool(st.session_state.get("_setta_sidebar_open", False))

def _setta_toggle_sidebar():
    st.session_state["_setta_sidebar_open"] = not _setta_sidebar_is_open()

def _setta_close_sidebar():
    st.session_state["_setta_sidebar_open"] = False

"""
if _sidebar_helpers not in _source:
    if _sidebar_role_anchor not in _source:
        raise RuntimeError("Ponto da Sidebar Operacional não encontrado.")
    _source = _source.replace(
        _sidebar_role_anchor,
        _sidebar_helpers + _sidebar_role_anchor,
        1,
    )

_old_nav_fn = '''def _mrp_set_sidebar_page(page):
    st.session_state["_mrp_sidebar_page"]=page
'''
_new_nav_fn = '''def _mrp_set_sidebar_page(page):
    st.session_state["_mrp_sidebar_page"]=page
    _setta_close_sidebar()
'''
if _old_nav_fn in _source:
    _source = _source.replace(_old_nav_fn, _new_nav_fn, 1)

_title_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
if _title_anchor not in _source:
    raise RuntimeError("Título principal não encontrado para SETTA UI V1.")

_setta_shell_css = """<style>
/* ======================================================
   SETTA UI — App Shell Rounded V1
   Referência oficial: MRP-CONVERSOR
   ====================================================== */
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
html,body,#root{
  height:100%!important;
  min-height:100%!important;
  max-height:100%!important;
  overflow:hidden!important;
  background:#EEF3F8!important;
  color-scheme:light!important;
}
body{
  box-sizing:border-box!important;
  padding:18px!important;
  margin:0!important;
  overflow:hidden!important;
  background:#EEF3F8!important;
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
  background:transparent!important;
}

/* ======================================================
   SETTA UI — Sidebar Operacional V1
   ====================================================== */
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
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"]{
  display:none!important;
}

/* Controle superior proprietário SETTA */
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
  width:82px!important;
  min-height:42px!important;
  height:42px!important;
  border-radius:10px!important;
  padding:0!important;
  background:rgba(255,255,255,.96)!important;
  border:1px solid #E5E8EE!important;
  color:#111827!important;
  box-shadow:0 2px 8px rgba(15,23,42,.06)!important;
  font-weight:800!important;
  font-size:12px!important;
}

/* ======================================================
   SETTA UI — Header Superior V1
   ====================================================== */
.setta-logo-card,
.setta-brand{
  width:100%!important;
  min-height:150px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  background:#FFFFFF!important;
  background-image:none!important;
  border:1px solid #E5E8EE!important;
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

/* ======================================================
   SETTA UI — Light Lock V1
   ====================================================== */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.stMain,
.block-container{
  color:#111827!important;
}
input,textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div,
[data-baseweb="base-input"],
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input{
  background:#FFFFFF!important;
  color:#111827!important;
  -webkit-text-fill-color:#111827!important;
}
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"]{
  background:#FFFFFF!important;
  color:#111827!important;
}
[data-testid="stDataFrame"]{
  background:#FFFFFF!important;
  border:1px solid #E5E8EE!important;
  border-radius:12px!important;
  overflow:hidden!important;
}
[data-testid="stMetric"],
[data-testid="stAlert"],
[data-testid="stFileUploader"] section{
  color:#111827!important;
}

/* Mobile: shell ocupa a tela inteira, como no Conversor MRP. */
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
  section[data-testid="stSidebar"]{
    border-radius:0!important;
  }
  .st-key-setta_top_controls{
    top:14px!important;
    left:16px!important;
  }
  .setta-logo-card,
  .setta-brand{
    min-height:105px!important;
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

_setta_runtime_ui = '''_setta_sidebar_open = _setta_sidebar_is_open()
if not _setta_sidebar_open:
    st.markdown(
        """<style>
        section[data-testid="stSidebar"]{display:none!important}
        </style>""",
        unsafe_allow_html=True,
    )

with st.container(key="setta_top_controls"):
    st.button(
        "☰ MENU",
        key="setta_drawer_toggle",
        use_container_width=True,
        on_click=_setta_toggle_sidebar,
    )

st.markdown(_setta_shell_css, unsafe_allow_html=True)
'''

_source = _source.replace(
    _title_anchor,
    _setta_runtime_ui + _title_anchor,
    1,
)
'''
