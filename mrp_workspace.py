"""Visual shell and routes for the existing Streamlit MRP."""
from contextlib import nullcontext
from html import escape
from pathlib import Path
import re

import pandas as pd

_ROUTES = {
    "MRP ATUAL": ("Demanda Geral", "Consulte necessidades, saldos e falta por material.", "grid_view"),
    "DEMANDA POR PROJETO": ("Demanda por Projeto", "Acompanhe o atendimento por projeto e material.", "layers"),
    "TRATATIVA DE PROJETOS": ("Tratativa de Projetos", "Consulte as tratativas registradas por projeto.", "fact_check"),
    "COMPARATIVO MRP": ("Comparativo MRP", "Compare versões do planejamento de materiais.", "monitoring"),
    "ANÁLISE DE COMPRA": ("Análise de Compra", "Revise os materiais e gere os relatórios de compra.", "shopping_cart"),
    "EXCEDENTES": ("Excedentes", "Consulte quantidades canceláveis em solicitações e pedidos de compra.", "inventory_2"),
    "SOLICITAÇÕES AVULSAS": ("Solicitações Avulsas", "Separação, entrega e histórico.", "assignment"),
    "CONFIGURAÇÕES": ("Configurações", "Bases, visual e operação do MRP.", "settings"),
}
_PLANNING = tuple(_ROUTES)[:4]
_OPERATIONS = tuple(_ROUTES)[4:7]
_ROUTE_IDS = {page: i for i, page in enumerate(_ROUTES)}

WORKSPACE_TRANSITION_JS = (
    '<span hidden data-mrp-shell-bootstrap></span><script>'
    + (Path(__file__).parent / "assets" / "mrp_tab_transition.js").read_text(encoding="utf-8")
    + "</script>"
)


def workspace_pages(role):
    # Comparativo e Configurações eram exclusivas do administrador.
    return tuple(p for p in _ROUTES if role == "ADMIN" or p not in {"COMPARATIVO MRP", "CONFIGURAÇÕES"})


class WorkspaceSection(nullcontext):
    def __init__(self, opened):
        super().__init__()
        self.open = opened


def workspace_sidebar(st, pages, active, change):
    for title, group in (("Planejamento", _PLANNING), ("Operações", _OPERATIONS), ("", ("CONFIGURAÇÕES",))):
        if title:
            st.html(f'<div class="sidebar-section-label">{title}</div>')
        for page in group:
            if page not in pages:
                continue
            name, _, icon = _ROUTES[page]
            st.button(name, key=f"mrp_nav_btn_{_ROUTE_IDS[page]}",
                      icon=f":material/{icon}:", type="primary" if active == page else "secondary",
                      width="stretch", on_click=change, args=(page,))


def workspace_header(page, logo, status, when, *, semana, bases, registros, alertas, nome, perfil):
    title, description, _ = _ROUTES[page]
    logo = str(logo or "")
    if re.fullmatch(r"data:image/(?:png|jpeg|jpg|webp|gif);base64,[A-Za-z0-9+/=]+", logo):
        mark = f'<img src="{escape(logo,quote=True)}" alt="SETTA">'
    else:
        mark = '<b>SETTA</b>'
    account = " · ".join(filter(None, (str(nome or ""), str(perfil or "").title())))
    section = "Planejamento" if page in _PLANNING else "Operações" if page in _OPERATIONS else "Administração"
    date = str(when or "—")
    stamps = escape(f"{str(status or 'Atualização').capitalize()} {date} · Semana {semana or '—'}")
    meta = escape(" · ".join(filter(None, (f"Bases {bases[0]}/{bases[1]}", str(registros or "").lower()))))
    alert = f'<div class="mrp-v2-alert" role="status">{escape(" · ".join(alertas))}</div>' if alertas else ""
    return (
        f'<header class="mrp-v2-header" data-mrp-route="{_ROUTE_IDS[page]}" aria-label="Página do MRP SETTA">'
        '<div class="mrp-v2-top">'
        f'<span class="mrp-v2-mark">{mark}</span><b class="mrp-v2-brand">MRP</b>'
        '<span class="mrp-v2-name">Planejamento de materiais</span>'
        f'<span class="mrp-v2-stamps">{stamps}</span><span class="mrp-v2-account">{escape(account)}</span>'
        '</div><div class="mrp-v2-intro">'
        f'<div class="mrp-v2-crumb">{section} / {title}</div>'
        f'<h1>{title}</h1><p>{description}</p><span class="mrp-v2-meta">{meta}</span>'
        f'<span class="mrp-v2-mobile-date">{stamps}</span>{alert}</div>'
        '<div class="mrp-tab-loader" role="status" aria-live="polite">Carregando aba…</div></header>'
    )


def workspace_falta(frame):
    """Read the existing final balance; do not recalculate planning or exports."""
    result = frame.copy()
    if "DIV" in result:
        result["Falta"] = (-pd.to_numeric(result["DIV"], errors="coerce")).clip(lower=0)
    else:
        result["Falta"] = float("nan")
    return result


WORKSPACE_V2_CSS = """
<style>
body:has(.mrp-v2-header) [data-testid="stMain"] [data-testid="stMainBlockContainer"].block-container {
  --v2-bg:#f0f3f8; --v2-navy:#142134; --v2-blue:#2158b3;
  background:var(--v2-bg)!important;padding:0 28px 24px!important;
}
/* Troca de aba: o quadro de navegação não esmaece; controles antigos
   ficam fora da tela e do foco até terminar a renderização do destino. */
.mrp-tab-loader{display:none}
html[data-mrp-navigating="true"] .mrp-tab-loader{
  display:flex;align-items:center;min-height:66px;margin:0;
  padding:14px 18px;border:1px solid #dbe4f0;border-radius:12px;
  background:#fff;color:#345071;font-size:.88rem;font-weight:650;
}
html[data-mrp-navigating="true"] [data-testid="stMainBlockContainer"] [data-mrp-tab-boundary] ~ *{
  display:none!important;
}
html[data-mrp-navigating="true"] [data-testid="stSidebar"] [data-stale="true"],
html[data-mrp-navigating="true"] [data-testid="stMainBlockContainer"] [data-stale="true"]:has(.mrp-v2-header){
  opacity:1!important;transition:none!important;
}
/* O bootstrap executa JS, mas não é um bloco visual nem deve criar o gap da pilha. */
body:has(.mrp-v2-header) [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has([data-mrp-shell-bootstrap]){
  display:none!important
}
body:has(.mrp-v2-header) [data-testid="stMainMenu"]{display:none!important}
body:has(.mrp-v2-header) [data-testid="stToolbar"]{pointer-events:none!important}
/* Sem wrappers de altura limitada: só a barra fica no topo da área rolável. */
body:has(.mrp-v2-header) [data-testid="stElementContainer"]:has(.mrp-v2-header),
body:has(.mrp-v2-header) [data-testid="stHtml"]:has(.mrp-v2-header),
.mrp-v2-header{display:contents!important}
body:has(.mrp-v2-header) [data-testid="stMain"]{background:#f0f3f8!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"],body:has(.mrp-v2-header) [data-testid="stSidebarContent"]{
  background:#142134!important;color:#f0f5ff!important}
body:has(.mrp-v2-header) section[data-testid="stSidebar"]{border-right:0!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] .sidebar-section-label{
  color:#a9bcd7!important;font-size:.67rem!important;letter-spacing:.12em!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button{
  color:#cfdaeb!important;background:transparent!important;border:1px solid transparent!important;box-shadow:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]{
  color:#fff!important;background:#263d61!important;border-color:#3f5e8d!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button:hover{
  background:#263d61!important;color:#fff!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button p{color:inherit!important;text-transform:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] [data-testid="stIconMaterial"]{
  font-size:18px!important;color:inherit!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"],
body:has(.mrp-v2-header) [data-testid="stSidebarContent"]{
  overflow:hidden!important
}
body:has(.mrp-v2-header) [data-testid="stSidebarContent"]{
  position:static!important;height:100%!important;padding:0!important;gap:0!important
}
body:has(.mrp-v2-header) [data-testid="stSidebarHeader"]{
  flex:0 0 58px!important;height:58px!important;min-height:58px!important;
  margin:0!important;padding:0!important;position:static!important
}
body:has(.mrp-v2-header) [data-testid="stSidebarUserContent"]{
  display:flex!important;flex-direction:column!important;flex:1 1 0!important;min-height:0!important;
  gap:0!important;margin:0!important;width:100%!important;box-sizing:border-box!important;
  padding:8px 12px max(12px,env(safe-area-inset-bottom))!important
}
body:has(.mrp-v2-header) [data-testid="stSidebarUserContent"] > :first-child,
body:has(.mrp-v2-header) [data-testid="stSidebarUserContent"] > :first-child > [data-testid="stVerticalBlock"]{
  display:flex!important;flex-direction:column!important;flex:1 1 0!important;min-height:0!important
}
body:has(.mrp-v2-header) [data-testid="stSidebarUserContent"] [data-testid="stLayoutWrapper"]:has(> .st-key-mrp_sidebar_nav){
  flex:1 1 auto!important;min-height:0!important;overflow:auto!important;overscroll-behavior:contain
}
body:has(.mrp-v2-header) [data-testid="stSidebarUserContent"] [data-testid="stLayoutWrapper"]:has(> .st-key-mrp_sidebar_account){
  flex:0 0 auto!important;margin-top:auto!important;padding-top:10px!important;
  border-top:1px solid #354a65
}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button::before{display:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button{padding-left:11px!important}
/* Ambos os controles nativos têm o mesmo alvo e não avançam sobre a marca. */
body:has(.mrp-v2-header) :is([data-testid="stHeader"], [data-testid="stSidebar"]) button[data-mrp-toggle]{
  display:grid!important;place-items:center;box-sizing:border-box!important;
  width:44px!important;min-width:44px!important;max-width:44px!important;
  height:44px!important;min-height:44px!important;padding:0!important;
  color:#fff!important;background:#263d61!important;border:1px solid #4b6385!important;
  border-radius:8px!important;box-shadow:none!important
}
body:has(.mrp-v2-header) button[data-mrp-toggle]:hover{background:#334e78!important}
body:has(.mrp-v2-header) button[data-mrp-toggle]:focus-visible{outline:2px solid #dceaff!important;outline-offset:2px}
body:has(.mrp-v2-header) [data-testid="stHeader"] button[data-mrp-toggle="Menu"]{
  position:fixed!important;top:7px!important;left:12px!important;pointer-events:auto!important
}
body:has(.mrp-v2-header) [data-testid="stSidebar"] button[data-mrp-toggle="Recolher"]{
  position:absolute!important;top:7px!important;left:12px!important
}
body:has(.mrp-v2-header) button[data-mrp-toggle]::after{content:none}
body:has(.mrp-v2-header) button[data-mrp-toggle="Recolher"]::before{content:"×";font-size:24px;line-height:1}
body:has(.mrp-v2-header) button[data-mrp-toggle="Menu"]::before{font-size:20px;line-height:1}
body:has(.mrp-v2-header):has([data-testid="stSidebar"][aria-expanded="false"]) .mrp-v2-top{padding-left:68px}
@media(min-width:901px){
  body:has(.mrp-v2-header) [data-testid="stSidebar"][aria-expanded="true"]{
    width:220px!important;min-width:220px!important;max-width:220px!important
  }
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] [data-testid="stColumn"]{
    flex:1 1 0!important;min-width:0!important;max-width:none!important
  }
}
.mrp-v2-header{color:#172435}
.mrp-v2-top{position:sticky;top:0;z-index:4;min-height:58px;background:#142134;color:#fff;margin:0 -28px;
  padding:8px 28px;display:flex;align-items:center;gap:13px}
.mrp-v2-mark{display:grid;place-items:center;box-sizing:border-box;width:88px;height:38px;
  background:white;color:#142134;border-radius:6px;padding:3px 7px;flex:none}
.mrp-v2-mark img{width:100%;height:100%;object-fit:contain}
.mrp-v2-brand{letter-spacing:.08em}
.mrp-v2-name{font-size:.76rem;color:#c1cee0;border-left:1px solid #415067;padding-left:13px}
.mrp-v2-stamps{margin-left:auto;color:#c1cee0;font-size:.75rem}
.mrp-v2-account{color:#fff;font-size:.8rem;font-weight:680;white-space:nowrap}
.mrp-v2-intro{padding-top:1px;position:relative}
.mrp-v2-crumb,.mrp-v2-meta,.mrp-v2-mobile-date{font-size:.72rem;color:#4d6077}
.mrp-v2-intro h1{font-size:clamp(1.45rem,3vw,1.95rem)!important;
  font-weight:780!important;color:#172435!important;text-transform:none!important;
  letter-spacing:-.035em!important;padding:0!important;margin:5px 0 3px!important;line-height:1.15!important}
.mrp-v2-intro p{font-size:.82rem;margin:0 0 4px;color:#4d6077}
.mrp-v2-meta{display:inline-block}
.mrp-v2-mobile-date{display:none}
.mrp-v2-alert{font-size:.78rem;color:#78350f;background:#fffbeb;border-radius:6px;padding:5px 8px;margin-top:6px}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] [data-testid="stHorizontalBlock"]{gap:9px!important}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] button{
  min-height:42px!important;border-radius:8px!important;box-shadow:none!important;border:1px solid #dce3ed!important}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] button[data-testid="stBaseButton-primary"]{
  background:#edf4ff!important;border-color:#7195d0!important;color:#1d4e9d!important}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"]{
  border:1px solid #dce3ed;border-radius:9px;padding:9px 11px;background:#fff
}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] button{
  min-height:38px!important;border-radius:6px!important;box-shadow:none!important;text-transform:none!important}
@media(max-width:900px){
  .mrp-v2-top{padding-left:68px}
  body:has(.mrp-v2-header) section[data-testid="stSidebar"],
  body:has(.mrp-v2-header) section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
    background:transparent!important;pointer-events:none!important
  }
  body:has(.mrp-v2-header) section[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarUserContent"]{
    background:#142134!important;pointer-events:auto!important;box-shadow:8px 10px 24px #14213426
  }
}
@media(max-width:700px){
  body:has(.mrp-v2-header) [data-testid="stMainBlockContainer"]{padding:0 12px 18px!important}
  .mrp-v2-top{margin:0 -12px;padding:7px 12px 7px 68px;gap:8px;min-height:58px}
  .mrp-v2-mark{width:66px;height:30px;padding:2px 5px}
  .mrp-v2-account{font-size:.69rem;margin-left:auto;overflow:hidden;text-overflow:ellipsis}
  .mrp-v2-name,.mrp-v2-stamps{display:none}
  .mrp-v2-mobile-date{display:block;margin-top:3px}
  .mrp-v2-intro{margin-top:-7px}
  body:has(.mrp-v2-header) [data-testid="stMain"] [data-testid="stMainBlockContainer"].block-container{padding:0 12px 18px!important}

  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] [data-testid="stColumn"]{
    flex:1 1 42%!important;min-width:0!important}
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] button{min-height:34px!important}
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 22%!important;min-width:0!important
  }
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] :is([data-testid="stVerticalBlock"],[data-testid="stLayoutWrapper"]) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{flex:1 1 24%!important;min-width:0!important}
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has([data-testid="stForm"] input[placeholder="Buscar por código ou descrição"]){flex:1 1 100%!important}
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] [data-testid="stForm"] [data-testid="stHorizontalBlock"]:has(input[placeholder="Buscar por código ou descrição"]){
    display:grid!important;grid-template-columns:minmax(0,1fr) 76px;gap:8px!important;align-items:end!important
  }
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] [data-testid="stPopoverButton"]{width:100%!important}

}
</style>
"""
