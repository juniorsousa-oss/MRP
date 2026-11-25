SETTA_UI_V1_PATCH = r'''
# =========================================================
# SETTA UI — PADRÃO OFICIAL DO CONVERSOR MRP
# Layout Streamlit com sidebar nativa e navegação responsiva
# + Header Superior V1 + Light Lock V1
# =========================================================
# Esta camada é somente estrutural/visual. Não altera cálculos,
# filtros, persistência, banco, integrações ou regras de negócio.

# 1) Sidebar nativa: desktop integrado à largura da página; mobile recolhível.
# O tema SETTA já substitui set_page_config pela versão com favicon
# global. Corrigir o estado diretamente nessa configuração final.
_page_cfg_old = '    initial_sidebar_state="expanded",'
_page_cfg_new = '    initial_sidebar_state="auto",'
if _source.count(_page_cfg_old) != 1:
    raise RuntimeError("Configuração de sidebar da página MRP não localizada.")
_source = _source.replace(_page_cfg_old, _page_cfg_new, 1)

# 2) O menu permanece no próprio st.sidebar. O Streamlit cuida do
# recolhimento no desktop e da abertura responsiva no celular.

# 3) CSS canônico do shell SETTA.
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
/* Não ocultar stToolbar: ele contém o controle nativo que reabre
   o menu lateral na versão 1.55 do Streamlit. */
[data-testid="stToolbar"]{
  display:flex!important;
  visibility:visible!important;
  pointer-events:auto!important;
}
[data-testid="stDecoration"],
[data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"]{
  display:none!important;
}
/* O controle que reabre a sidebar pertence ao cabeçalho nativo.
   Ocultá-lo deixa o usuário sem acesso após recolher o painel. */
[data-testid="stHeader"],header[data-testid="stHeader"]{
  display:flex!important;
  visibility:visible!important;
  height:3rem!important;
  min-height:3rem!important;
  max-height:3rem!important;
  position:fixed!important;
  inset:0 0 auto 0!important;
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
  pointer-events:auto!important;
  z-index:2000!important;
}
[data-testid="stHeader"] button,
[data-testid="stSidebar"] button{
  pointer-events:auto!important;
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

/* Os controles nativos de expansão variam de nome entre as versões
   do Streamlit. Não suprimir o cabeçalho nem o botão ao recolher o menu. */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"]{
  visibility:visible!important;
  opacity:1!important;
  pointer-events:auto!important;
  z-index:3000!important;
}
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"]{
  display:flex!important;
  position:fixed!important;
  top:12px!important;
  left:14px!important;
  width:48px!important;
  min-width:48px!important;
  min-height:42px!important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button,
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button{
  visibility:visible!important;
  opacity:1!important;
  pointer-events:auto!important;
  min-width:42px!important;
  min-height:40px!important;
  background:#fff!important;
  border:1px solid #e5e8ee!important;
  border-radius:10px!important;
  box-shadow:0 2px 9px rgba(15,23,42,.12)!important;
}
@media(max-width:900px){
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="collapsedControl"]{
    top:calc(12px + env(safe-area-inset-top,0px))!important;
    left:12px!important;
  }
}

/* SETTA UI — Sidebar no layout padrão */
section[data-testid="stSidebar"]{
  background:#fff!important;
  background-image:none!important;
  border-right:1px solid #e8ebf0!important;
  border-radius:0!important;
  /* Largura, flex e animação de abrir/fechar pertencem ao Streamlit. */
  overflow-y:auto!important;
  overflow-x:hidden!important;
}
section[data-testid="stSidebar"]>div{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  box-sizing:border-box!important;
}
section[data-testid="stSidebar"] .block-container{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  box-sizing:border-box!important;
  padding-top:54px!important;
  padding-left:16px!important;
  padding-right:16px!important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
  gap:0!important;
  row-gap:0!important;
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
  display:block!important;
  align-self:stretch!important;
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  margin:0 0 2px 0!important;
  padding:0!important;
}
section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has([class*="st-key-mrp_nav_btn_"]){
  display:block!important;
  align-self:stretch!important;
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
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
/* O conteúdo da lateral tem seu próprio scroll quando faltar espaço. */
[data-testid="stSidebarUserContent"]:has(.st-key-mrp_sidebar_account){
  display:flex!important;flex-direction:column!important;flex:1 0 auto!important;
  padding-bottom:16px!important;
}
[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"]{
  flex:1 0 auto!important;
}
[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > :has(.st-key-mrp_sidebar_account),
[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > .st-key-mrp_sidebar_account{
  margin-top:auto!important;padding-top:16px!important;
}
.st-key-mrp_sidebar_account [data-testid="stPopoverButton"]{
  min-height:44px;justify-content:flex-start;border:1px solid #e5e8ee;
  border-radius:9px;background:#f8fafc;color:#1e293b;
}
.st-key-mrp_logout_sidebar button{
  width:100%!important;
  min-height:39px!important;
  background:#fff!important;
  border:1px solid #e5e8ee!important;
  border-radius:9px!important;
  color:#991b1b!important;
  font-size:12px!important;
  font-weight:800!important;
}
.st-key-mrp_logout_sidebar button:hover{
  background:#fff5f5!important;
  border-color:#fecaca!important;
  color:#7f1d1d!important;
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
  /* Preservar o algoritmo responsivo nativo do Streamlit. Nao forcar
     display, flex-basis nem largura de main: no Safari a coluna fantasma
     pode deslocar o conteúdo para fora do viewport. */
  [data-testid="stAppViewContainer"]{
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    margin:0!important;
  }
  [data-testid="stMain"],.stMain,section.main{
    min-width:0!important;
    max-width:100%!important;
    margin:0!important;
    box-sizing:border-box!important;
    overflow-x:hidden!important;
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
  /* A sidebar não pode ocupar uma coluna flex nem reduzir o MRP quando
     aberta. Usar posicionamento fixo, mas deixar a largura/left/transform
     sob controle nativo do Streamlit (especialmente Safari iOS). */
  section[data-testid="stSidebar"]{
    position:fixed!important;
    flex:none!important;
    flex-basis:auto!important;
    max-height:100dvh!important;
    overflow-y:auto!important;
    z-index:1001!important;
  }
  section[data-testid="stSidebar"]>div,
  section[data-testid="stSidebar"] .block-container{
    box-sizing:border-box!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
  }
  section[data-testid="stSidebar"] .block-container{
    padding:60px 14px 28px!important;
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

/* Na área autenticada, voltar ao scroll interno nativo do painel.
   Deixar o shell e o documento crescer com ele esticava a sidebar e
   criava rolagem depois do fim do conteúdo. Não afeta a tela de login. */
html:has(.mrp-workspace-head),body:has(.mrp-workspace-head),
body:has(.mrp-workspace-head) #root{
  height:100%!important;min-height:0!important;overflow:hidden!important;
}
body:has(.mrp-workspace-head) .stApp,
body:has(.mrp-workspace-head) [data-testid="stAppViewContainer"]{
  height:100vh!important;height:100dvh!important;min-height:0!important;
  overflow:hidden!important;
}
body:has(.mrp-workspace-head) [data-testid="stMain"]{
  height:100%!important;min-height:0!important;overflow-y:auto!important;
}
body:has(.mrp-workspace-head) [data-testid="stMainBlockContainer"]{
  min-height:0!important;padding-bottom:24px!important;
}
body:has(.mrp-workspace-head) section[data-testid="stSidebar"]{
  height:100vh!important;height:100dvh!important;min-height:0!important;
}
body:has(.mrp-workspace-head) [data-testid="stHeader"] [data-testid="stExpandSidebarButton"],
body:has(.mrp-workspace-head) [data-testid="stSidebarCollapsedControl"] button,
body:has(.mrp-workspace-head) [data-testid="collapsedControl"] button{
  min-width:74px!important;min-height:38px!important;
  border:1px solid #e5e8ee!important;border-radius:8px!important;background:#fff!important;
}
button[data-mrp-toggle] > *{display:none!important}
button[data-mrp-toggle]::after{content:attr(data-mrp-toggle);font-size:13px;font-weight:650}
button[data-mrp-toggle="Menu"]::before{content:"☰";font-size:14px}
@media(max-width:900px){
  body:has(.mrp-workspace-head) [data-testid="stMainBlockContainer"]{
    padding-bottom:calc(20px + env(safe-area-inset-bottom,0px))!important;
  }
}

</style>"""

# Mantém o bloco de navegação gerado por PADRONIZACAO_NFS_PATCH.
# Não convertê-lo para popover ou elemento flutuante.
if 'with st.sidebar:' not in _source:
    raise RuntimeError("Sidebar nativa do MRP não localizada.")

_shell_anchor = '_mrp_role=st.session_state.get("auth_role")\n'
if _shell_anchor not in _source:
    raise RuntimeError("Ponto de montagem da sidebar não encontrado para SETTA UI.")

# Só fechar ao navegar no mobile. Reutilizar os botões nativos, que
# preservam foco, expansão manual e adaptação do layout Streamlit.
_setta_close_on_navigation = r"""<script>
(() => {
  if (window.__settaMenuCloseOnNavV1) return;
  window.__settaMenuCloseOnNavV1 = true;
  const mobile = window.matchMedia("(max-width: 900px)");
  const sidebar = () => document.querySelector('section[data-testid="stSidebar"]');
  const collapseButton = () => sidebar()?.querySelector(
    'button[data-testid="stSidebarCollapseButton"],' +
    '[data-testid="stSidebarCollapseButton"] button,' +
    '[data-testid="stSidebarHeader"] button'
  );
  const label = (button, text, name) => {
    if (!button || button.dataset.mrpToggle === text) return;
    button.dataset.mrpToggle = text;
    button.setAttribute("aria-label", name);
    button.title = name;
  };
  let initial = true;
  const controls = () => {
    const close = collapseButton();
    label(close, "Recolher", "Recolher menu lateral");
    label(document.querySelector(
      'button[data-testid="stExpandSidebarButton"],' +
      '[data-testid="stExpandSidebarButton"] button,' +
      '[data-testid="stSidebarCollapsedControl"] button,' +
      '[data-testid="collapsedControl"] button'
    ), "Menu", "Abrir menu lateral");
    if (initial && sidebar()?.querySelector('[class*="st-key-mrp_nav_btn_"] button')) {
      initial = false;
      if (mobile.matches && sidebar().getAttribute("aria-expanded") === "true") close?.click();
    }
  };
  let pending = false;
  new MutationObserver(() => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; controls(); });
  }).observe(document.getElementById("root"), {childList: true, subtree: true});
  controls();
  document.addEventListener("click", (event) => {
    const clicked = event.target instanceof Element ? event.target : null;
    if (!mobile.matches || !clicked?.closest('[class*="st-key-mrp_nav_btn_"] button')) return;
    queueMicrotask(() => collapseButton()?.click());
  }, true);
})();
</script>"""

_shell_bootstrap = (
    'st.markdown(' + repr(_setta_css) + ', unsafe_allow_html=True)\n'
    + 'st.html(' + repr(_setta_close_on_navigation)
    + ', unsafe_allow_javascript=True)\n'
)
_source = _source.replace(
    _shell_anchor,
    _shell_bootstrap + _shell_anchor,
    1,
)
'''
