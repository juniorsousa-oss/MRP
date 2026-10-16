SETTA_UI_V1_PATCH = r'''
# =========================================================
# SETTA UI — PADRÃO OFICIAL DO CONVERSOR MRP
# Layout padrão Streamlit + Sidebar Operacional V1
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
_drawer_runtime = """# Menu SETTA independente do painel interno do Streamlit:
# apenas a navegação própria (st.container) é exibida quando o usuário abre.
def _setta_sidebar_mode() -> str:
    return "open" if st.session_state.get("_setta_sidebar_mode")=="open" else "closed"

def _setta_toggle_sidebar_desktop() -> None:
    st.session_state["_setta_sidebar_mode"]=(
        "closed" if _setta_sidebar_mode()=="open" else "open"
    )

def _setta_toggle_sidebar_mobile() -> None:
    st.session_state["_setta_sidebar_mode"]=(
        "closed" if _setta_sidebar_mode()=="open" else "open"
    )

def _setta_close_sidebar() -> None:
    st.session_state["_setta_sidebar_mode"]="closed"

_setta_sidebar_mode_current=_setta_sidebar_mode()

# O botão é renderizado sempre, inclusive com a navegação fechada.
# Os links, status e semana são renderizados posteriormente em painel próprio.
with st.container(key="setta_top_controls"):
    st.button(
        "☰",
        key="setta_drawer_toggle",
        help="Abrir ou fechar menu (computador)",
        use_container_width=True,
        on_click=_setta_toggle_sidebar_desktop,
    )
    st.button(
        "☰",
        key="setta_drawer_toggle_mobile",
        help="Abrir ou fechar menu (celular)",
        use_container_width=True,
        on_click=_setta_toggle_sidebar_mobile,
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

/* SETTA UI — Layout padrão Streamlit */
html,body,#root{
  min-height:100%!important;
  height:auto!important;
  max-height:none!important;
  overflow-y:auto!important;
  overflow-x:hidden!important;
}
html,body{
  background:#F4F7FB!important;
  background-image:none!important;
}
body{
  box-sizing:border-box!important;
  padding:0!important;
  margin:0!important;
  overflow-y:auto!important;
}
.stApp,
[data-testid="stApp"]{
  position:relative!important;
  inset:auto!important;
  width:100%!important;
  height:auto!important;
  min-height:100vh!important;
  max-height:none!important;
  max-width:none!important;
  margin:0!important;
  border:0!important;
  border-radius:0!important;
  overflow:visible!important;
  background:#F8FAFD!important;
  background-image:none!important;
  box-shadow:none!important;
}
[data-testid="stAppViewContainer"]{
  position:relative!important;
  inset:auto!important;
  width:100%!important;
  height:auto!important;
  min-height:100vh!important;
  max-height:none!important;
  border-radius:0!important;
  overflow:visible!important;
  background:#F4F7FB!important;
  background-image:none!important;
}
[data-testid="stMain"],
.stMain,
section.main{
  position:relative!important;
  height:auto!important;
  min-height:100vh!important;
  max-height:none!important;
  overflow-x:hidden!important;
  overflow-y:visible!important;
  background:#F4F7FB!important;
  background-image:none!important;
}
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"]{
  width:100%!important;
  max-width:none!important;
  height:auto!important;
  min-height:100vh!important;
  max-height:none!important;
  margin:0!important;
  overflow:visible!important;
  padding-top:3.2rem!important;
  padding-left:2.7rem!important;
  padding-right:2.7rem!important;
  padding-bottom:3rem!important;
  box-sizing:border-box!important;
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
  max-width:none!important;
  width:100%!important;
  margin:0!important;
  padding-top:3.2rem!important;
  padding-left:2.7rem!important;
  padding-right:2.7rem!important;
  padding-bottom:3rem!important;
  box-sizing:border-box!important;
}

/* SETTA UI — Top Controls V1: medidas idênticas ao Conversor MRP */
.st-key-setta_top_controls{
  position:fixed!important;
  top:calc(12px + env(safe-area-inset-top,0px))!important;
  left:14px!important;
  z-index:10010!important;
  width:58px!important;
  max-width:58px!important;
  margin:0!important;
  padding:0!important;
}
.st-key-setta_drawer_toggle_mobile{
  display:none!important;
}
@media(max-width:900px){
  .st-key-setta_drawer_toggle{display:none!important;}
  .st-key-setta_drawer_toggle_mobile{display:block!important;}
}
.st-key-setta_top_controls [data-testid="stVerticalBlock"]{gap:0!important}
.st-key-setta_drawer_toggle,
.st-key-setta_drawer_toggle_mobile{
  width:58px!important;
  max-width:58px!important;
  margin:0!important;
  padding:0!important;
}
.st-key-setta_drawer_toggle button,
.st-key-setta_drawer_toggle_mobile button{
  width:58px!important;
  min-width:58px!important;
  min-height:44px!important;
  height:44px!important;
  border-radius:10px!important;
  padding:0!important;
  background:rgba(255,255,255,.98)!important;
  box-shadow:0 2px 10px rgba(15,23,42,.14)!important;
}

/* Menu SETTA independente: nunca depender do DOM da sidebar do Streamlit. */
section[data-testid="stSidebar"]{
  display:none!important;
  visibility:hidden!important;
}
.st-key-setta_custom_navigation{
  position:fixed!important;
  top:0!important;
  left:0!important;
  right:auto!important;
  box-sizing:border-box!important;
  width:min(86vw,280px)!important;
  min-width:0!important;
  max-width:280px!important;
  height:100dvh!important;
  min-height:0!important;
  max-height:100dvh!important;
  overflow-y:auto!important;
  overscroll-behavior:contain!important;
  padding:88px 16px 30px!important;
  margin:0!important;
  z-index:500!important;
  border-right:1px solid #e8ebf0!important;
  background:#fff!important;
  box-shadow:5px 0 30px rgba(15,23,42,.15)!important;
}
.st-key-setta_custom_navigation [data-testid="stVerticalBlock"]{
  gap:0!important;
  row-gap:0!important;
  min-width:0!important;
}
.st-key-setta_custom_navigation [class*="st-key-mrp_nav_btn_"]{
  margin:0 0 2px!important;
  padding:0!important;
  width:100%!important;
}
.st-key-setta_custom_navigation [class*="st-key-mrp_nav_btn_"] button{
  display:flex!important;
  position:relative!important;
  justify-content:flex-start!important;
  width:100%!important;
  min-height:42px!important;
  padding:0 12px 0 24px!important;
  border-radius:10px!important;
  text-align:left!important;
}
.st-key-setta_custom_navigation [class*="st-key-mrp_nav_btn_"] button p{
  width:100%!important;
  font-size:13px!important;
  text-align:left!important;
}
.st-key-setta_custom_navigation [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-secondary"]{
  background:transparent!important;
  border:1px solid transparent!important;
  color:#374151!important;
}
.st-key-setta_custom_navigation [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]{
  background:#111827!important;
  border:1px solid #111827!important;
  color:#fff!important;
}
.st-key-setta_custom_navigation [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]::before{
  content:""!important;
  position:absolute!important;
  top:50%!important;
  left:7px!important;
  width:4px!important;
  height:20px!important;
  background:#ef4444!important;
  border-radius:999px!important;
  transform:translateY(-50%)!important;
}

/* SETTA UI — Sidebar no layout padrão */
section[data-testid="stSidebar"]{
  background:#fff!important;
  background-image:none!important;
  border-right:1px solid #e8ebf0!important;
  border-radius:0!important;
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  flex:0 0 260px!important;
  flex-basis:260px!important;
  overflow:hidden!important;
}
section[data-testid="stSidebar"]>div{
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
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
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  background:#fff!important;
  background-image:none!important;
  border:1px solid #e5e8ee!important;
  border-radius:18px!important;
  box-shadow:0 4px 14px rgba(24,39,75,.08)!important;
  box-sizing:border-box!important;
  margin:61px 0 24px 0!important;
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
/* Mobile: página normal e responsiva. */
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
    width:100%!important;
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
    margin-top:0!important;
    margin-bottom:1.8rem!important;
    padding:.9rem 1rem!important;
  }
  .setta-logo-card img,
  .setta-brand-logo img{
    max-width:170px!important;
    max-height:72px!important;
  }
}

/* SETTA MRP — RESPONSIVIDADE MOBILE (somente viewport <= 900px).
   O menu é sobreposto, nunca reserva 260px no fluxo da página. */
@media (max-width:900px){
  html,body,#root{
    width:100%!important;
    min-width:0!important;
    max-width:100vw!important;
    margin:0!important;
    overflow-x:clip!important;
  }
  .stApp,[data-testid="stApp"]{
    width:100%!important;
    min-width:0!important;
    max-width:100vw!important;
    margin:0!important;
    overflow-x:clip!important;
  }
  [data-testid="stAppViewContainer"]{
    position:relative!important;
    display:block!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    margin:0!important;
    overflow-x:clip!important;
  }
  [data-testid="stMain"],.stMain,section.main{
    position:relative!important;
    left:auto!important;
    right:auto!important;
    transform:none!important;
    flex:1 1 auto!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    margin:0!important;
    padding:0!important;
    box-sizing:border-box!important;
    overflow-x:clip!important;
  }
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewBlockContainer"],
  .block-container:not(section[data-testid="stSidebar"] .block-container){
    box-sizing:border-box!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    margin:0!important;
    padding:76px 14px 28px!important;
    overflow:visible!important;
  }
  section[data-testid="stSidebar"]{
    position:fixed!important;
    inset:0 auto 0 0!important;
    display:flex;
    flex:none!important;
    flex-basis:auto!important;
    width:min(86vw,300px)!important;
    min-width:0!important;
    max-width:min(86vw,300px)!important;
    height:100dvh!important;
    max-height:100dvh!important;
    overflow-y:auto!important;
    overscroll-behavior:contain;
    z-index:225!important;
    box-shadow:7px 0 32px rgba(12,32,50,.15)!important;
  }
  section[data-testid="stSidebar"]>div,
  section[data-testid="stSidebar"] .block-container{
    box-sizing:border-box!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
  }
  section[data-testid="stSidebar"] .block-container{
    padding:76px 14px 28px!important;
  }
  .st-key-setta_top_controls{
    position:fixed!important;
    top:calc(12px + env(safe-area-inset-top,0px))!important;
    left:14px!important;
    right:auto!important;
    z-index:10010!important;
    width:58px!important;
    max-width:58px!important;
    margin:0!important;
  }
  .st-key-setta_drawer_toggle{
    width:58px!important;
    max-width:58px!important;
  }
  .st-key-setta_drawer_toggle_mobile,
  .st-key-setta_drawer_toggle_mobile button{
    width:58px!important;
    min-width:58px!important;
    max-width:58px!important;
    height:44px!important;
    min-height:44px!important;
    border-radius:12px!important;
  }
  .st-key-setta_drawer_toggle button{
    width:58px!important;
    min-width:58px!important;
    height:44px!important;
    min-height:44px!important;
    max-height:44px!important;
    border-radius:12px!important;
  }
  .setta-logo-card,.setta-brand{
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    min-height:96px!important;
    height:auto!important;
    margin:0 0 18px!important;
    padding:15px 12px!important;
    border-radius:16px!important;
  }
  .setta-logo-card img,.setta-brand-logo img{
    max-width:min(65vw,175px)!important;
    max-height:64px!important;
    object-fit:contain!important;
  }
  .app-title{
    margin:0!important;
    font-size:clamp(1.75rem,7vw,2.1rem)!important;
    line-height:1.12!important;
    overflow-wrap:normal!important;
  }
  .app-subtitle,.app-sub{
    font-size:.81rem!important;
    line-height:1.55!important;
    margin-bottom:1.15rem!important;
    overflow-wrap:anywhere!important;
  }
  .section-band{
    padding:12px 14px!important;
    border-radius:13px!important;
  }
  .section-band-title{
    font-size:1rem!important;
    line-height:1.28!important;
    overflow-wrap:anywhere!important;
  }
  div[data-testid="stHorizontalBlock"]{
    box-sizing:border-box!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    flex-wrap:wrap!important;
    gap:.8rem!important;
  }
  div[data-testid="stColumn"]{
    box-sizing:border-box!important;
    flex:1 1 100%!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
  }
  div[data-testid="stMetric"]{
    box-sizing:border-box!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    padding:14px 16px!important;
  }
  .mrp-source-grid{
    width:100%!important;
    min-width:0!important;
    grid-template-columns:minmax(0,1fr)!important;
  }
  .mrp-source-card,.mrp-output-card,.mrp-ped-hero,.mrp-av-hero{
    box-sizing:border-box!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
  }
  [data-testid="stTabs"]{
    max-width:100%!important;
    min-width:0!important;
  }
  [data-testid="stTabs"] [data-baseweb="tab-list"]{
    overflow-x:auto!important;
    max-width:100%!important;
    scrollbar-width:thin;
  }
  [data-testid="stDataFrame"]{
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    overflow-x:auto!important;
  }
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewBlockContainer"],
  .block-container:not(section[data-testid="stSidebar"] .block-container){
    padding-bottom:calc(32px + env(safe-area-inset-bottom,0px))!important;
  }
}
/* Tabletes: dois indicadores por linha. Celulares: um por linha. */
@media (min-width:601px) and (max-width:900px){
  div[data-testid="stColumn"]{
    flex:1 1 calc(50% - .4rem)!important;
    width:calc(50% - .4rem)!important;
    max-width:calc(50% - .4rem)!important;
  }
  .mrp-source-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
}

</style>"""

# O menu montado pelo st.sidebar pode ser desmontado pelo Streamlit,
# dependendo da largura, zoom, estado nativo ou versão do navegador.
# Montamos os MESMOS controles e cards em st.container, diretamente no
# conteúdo principal. O painel é aberto/recolhido apenas pela sessão.
_menu_original_anchor = (
    'with st.sidebar:\n'
    '    st.markdown(\n'
    '        \'<div class="sidebar-brand">\''
)
_menu_block_start = _source.find(_menu_original_anchor)
_menu_block_end = _source.find('\ndef _mrp_source_card_html(', _menu_block_start)
if _menu_block_start < 0 or _menu_block_end < 0:
    raise RuntimeError("Navegação SETTA não localizada para painel independente.")
_menu_original = _source[_menu_block_start:_menu_block_end]
_menu_personalizado = _menu_original.replace(
    'with st.sidebar:',
    'with st.container(key="setta_custom_navigation"):',
    1,
)
_menu_personalizado = (
    'if _setta_sidebar_mode_current=="open":\n'
    + ''.join('    '+_line if _line.strip() else _line
              for _line in _menu_personalizado.splitlines(keepends=True))
)
_source = (
    _source[:_menu_block_start]
    + _menu_personalizado
    + _source[_menu_block_end:]
)

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
