"""Visual shell and routes for the existing Streamlit MRP."""
from contextlib import nullcontext
from functools import lru_cache
from html import escape
from pathlib import Path
import os
import logging
import re

import pandas as pd
from streamlit.errors import StreamlitAPIException

from mrp_identidade_setta import logo_data_uri

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

@lru_cache(maxsize=1)
def _workspace_transition_script():
    return (Path(__file__).parent / "assets" / "mrp_tab_transition.js").read_text(encoding="utf-8")


def workspace_transition(st):
    """Visual only; missing asset or disabled switch must not stop the MRP."""
    if os.getenv("MRP_DISABLE_TAB_TRANSITION") == "1":
        return
    try:
        script = _workspace_transition_script()
        st.html('<span hidden data-mrp-shell-bootstrap></span><script>' + script + "</script>",
                unsafe_allow_javascript=True)
    except (OSError, UnicodeError, TypeError, StreamlitAPIException):
        logging.getLogger(__name__).warning("Transição visual do MRP desativada nesta sessão.", exc_info=True)


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
    if logo == logo_data_uri() or re.fullmatch(r"data:image/(?:png|jpeg|jpg|webp|gif);base64,[A-Za-z0-9+/=]+", logo):
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
        '<button class="mrp-v2-menu-toggle" type="button" aria-label="Abrir menu lateral" '
        'aria-expanded="false"><span class="mrp-v2-menu-icon" aria-hidden="true"></span></button>'
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
  --v2-bg:#f0f0f0; --v2-navy:#333333; --v2-blue:#ffbb00;
  background:var(--v2-bg)!important;padding:var(--mrp-top-height) 28px 24px!important;
}
/* Troca de aba: o quadro de navegação não esmaece; controles antigos
   ficam fora da tela e do foco até terminar a renderização do destino. */
.mrp-tab-loader{display:none}
html[data-mrp-navigating="true"] .mrp-tab-loader{
  display:flex;align-items:center;min-height:66px;margin:0;
  padding:14px 18px;border:1px solid #e1e1e1;border-radius:12px;
  background:#fff;color:#424242;font-size:.88rem;font-weight:650;
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
/* Sem wrappers de altura limitada. O topo é independente da área rolável. */
body:has(.mrp-v2-header) [data-testid="stElementContainer"]:has(.mrp-v2-header),
body:has(.mrp-v2-header) [data-testid="stHtml"]:has(.mrp-v2-header),
.mrp-v2-header{display:contents!important}
body:has(.mrp-v2-header){--mrp-top-height:58px}
body:has(.mrp-v2-header) [data-testid="stMain"]{
  background:#f0f0f0!important;scroll-padding-top:var(--mrp-top-height)
}
body:has(.mrp-v2-header) [data-testid="stSidebar"],body:has(.mrp-v2-header) [data-testid="stSidebarContent"]{
  background:#333333!important;color:#f0f0f0!important}
body:has(.mrp-v2-header) section[data-testid="stSidebar"]{border-right:0!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] .sidebar-section-label{
  color:#d2d2d2!important;font-size:.67rem!important;letter-spacing:.12em!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button{
  color:#f0f0f0!important;background:transparent!important;border:1px solid transparent!important;box-shadow:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]{
  color:#333333!important;background:#ffbb00!important;border-color:#ffbb00!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button[data-testid="stBaseButton-primary"]::before{
  display:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button:not([data-testid="stBaseButton-primary"]):hover{
  background:#424242!important;color:#fff!important}
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
  flex:0 0 var(--mrp-top-height)!important;height:var(--mrp-top-height)!important;min-height:var(--mrp-top-height)!important;
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
  border-top:1px solid #616161
}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button::before{display:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button{padding-left:11px!important}
/* Ambos os controles nativos têm o mesmo alvo e não avançam sobre a marca. */
body:has(.mrp-v2-header) :is([data-testid="stHeader"], [data-testid="stSidebar"]) button[data-mrp-toggle]{
  display:grid!important;place-items:center;box-sizing:border-box!important;
  width:44px!important;min-width:44px!important;max-width:44px!important;
  height:44px!important;min-height:44px!important;padding:0!important;
  color:#fff!important;background:#424242!important;border:1px solid #767676!important;
  border-radius:8px!important;box-shadow:none!important
}
body:has(.mrp-v2-header) button[data-mrp-toggle]:hover{background:#555555!important}
body:has(.mrp-v2-header) button[data-mrp-toggle]:focus-visible{outline:2px solid #ffbb00!important;outline-offset:2px}
body:has(.mrp-v2-header) [data-testid="stHeader"] button[data-mrp-toggle="Menu"]{
  position:fixed!important;top:7px!important;left:12px!important;pointer-events:auto!important
}
body:has(.mrp-v2-header) [data-testid="stSidebar"] button[data-mrp-toggle="Recolher"]{
  position:absolute!important;top:7px!important;left:12px!important
}
body:has(.mrp-v2-header) button[data-mrp-toggle]::after{content:none}
body:has(.mrp-v2-header) button[data-mrp-toggle="Recolher"]::before{content:"×";font-size:24px;line-height:1}
body:has(.mrp-v2-header) button[data-mrp-toggle="Menu"]::before{font-size:20px;line-height:1}
@media(min-width:901px){
  body:has(.mrp-v2-header) [data-testid="stSidebar"][aria-expanded="true"]{
    width:220px!important;min-width:220px!important;max-width:220px!important
  }
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] [data-testid="stColumn"]{
    flex:1 1 0!important;min-width:0!important;max-width:none!important
  }
}
.mrp-v2-header{color:#333333}
/* Barra em largura de viewport, acima da navegação nativa. Só o conteúdo
   principal acompanha a abertura da sidebar no desktop. */
.mrp-v2-top{position:fixed;inset:0 0 auto;z-index:2002;box-sizing:border-box;
  height:var(--mrp-top-height);background:#333333;color:#fff;
  padding:7px 28px 7px 68px;display:flex;align-items:center;gap:13px;
  pointer-events:none}
.mrp-v2-top button{pointer-events:auto}
.mrp-v2-mark{display:grid;place-items:center;box-sizing:border-box;width:88px;height:38px;
  background:white;color:#333333;border-radius:6px;padding:7px 11px;flex:none}
.mrp-v2-mark img{width:100%;height:24px;object-fit:contain;display:block}
.mrp-v2-brand{letter-spacing:.08em}
.mrp-v2-name{font-size:.76rem;color:#e1e1e1;border-left:1px solid #767676;padding-left:13px}
.mrp-v2-stamps{margin-left:auto;color:#e1e1e1;font-size:.75rem}
.mrp-v2-account{color:#fff;font-size:.8rem;font-weight:680;white-space:nowrap}
.mrp-v2-intro{padding-top:12px;position:relative}
.mrp-v2-crumb,.mrp-v2-meta,.mrp-v2-mobile-date{font-size:.72rem;color:#525252}
.mrp-v2-intro h1{font-size:clamp(1.45rem,3vw,1.95rem)!important;
  font-weight:780!important;color:#333333!important;text-transform:none!important;
  letter-spacing:-.035em!important;padding:0!important;margin:5px 0 3px!important;line-height:1.15!important}
.mrp-v2-intro p{font-size:.82rem;margin:0 0 4px;color:#525252}
.mrp-v2-meta{display:inline-block}
.mrp-v2-mobile-date{display:none}
.mrp-v2-alert{font-size:.78rem;color:#78350f;background:#fffbeb;border-radius:6px;padding:5px 8px;margin-top:6px}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] [data-testid="stHorizontalBlock"]{gap:9px!important}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] button{
  min-height:42px!important;border-radius:8px!important;box-shadow:none!important;border:1px solid #e1e1e1!important}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] button[data-testid="stBaseButton-primary"]{
  background:#fff3cc!important;border-color:#8a6500!important;color:#333333!important}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"]{
  border:1px solid #e1e1e1;border-radius:9px;padding:9px 11px;background:#fff
}
body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_bar_"] button{
  min-height:38px!important;border-radius:6px!important;box-shadow:none!important;text-transform:none!important}
@media(max-width:900px){
  body:has(.mrp-v2-header) section[data-testid="stSidebar"],
  body:has(.mrp-v2-header) section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
    background:transparent!important;pointer-events:none!important
  }
  body:has(.mrp-v2-header) section[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarUserContent"]{
    background:#333333!important;pointer-events:auto!important;box-shadow:8px 10px 24px #33333326
  }
}
@media(max-width:700px){
  body:has(.mrp-v2-header) [data-testid="stMainBlockContainer"]{padding:var(--mrp-top-height) 12px 18px!important}
  .mrp-v2-top{padding-right:12px;gap:8px}
  .mrp-v2-mark{width:66px;height:30px;padding:0}
  .mrp-v2-mark img{width:52px;height:21px}
  .mrp-v2-account{font-size:.69rem;margin-left:auto;overflow:hidden;text-overflow:ellipsis}
  .mrp-v2-name,.mrp-v2-stamps{display:none}
  .mrp-v2-mobile-date{display:block;margin-top:3px}
  .mrp-v2-intro{padding-top:10px}
  body:has(.mrp-v2-header) [data-testid="stMain"] [data-testid="stMainBlockContainer"].block-container{padding:var(--mrp-top-height) 12px 18px!important}

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

/* Sem JS, os acionadores nativos continuam acessíveis atrás da barra. */
.mrp-v2-menu-toggle{display:none}
html[data-mrp-menu-ready] body:has(.mrp-v2-header) .mrp-v2-top{padding-left:12px!important;pointer-events:auto}
html[data-mrp-menu-ready] body:has(.mrp-v2-header) :is([data-testid="stHeader"],[data-testid="stSidebar"]) button[data-mrp-toggle]{
  visibility:hidden!important;pointer-events:none!important
}
html[data-mrp-menu-ready] .mrp-v2-menu-toggle{
  display:grid;place-items:center;box-sizing:border-box;flex:0 0 44px;
  width:44px;height:44px;padding:0;margin:0 -1px 0 0;border:1px solid #767676;border-radius:8px;
  color:#fff;background:#424242;cursor:pointer;font:inherit
}
.mrp-v2-menu-toggle:hover{background:#555555!important}
.mrp-v2-menu-toggle:focus-visible{outline:2px solid #ffbb00;outline-offset:2px}
/* Mesmos glifos e caixa visual do controle nativo no Inventário Setta. */
.mrp-v2-menu-icon{display:flex;align-items:center;justify-content:center;width:16px;height:16px;
  font:400 21px/1 "Material Symbols Rounded";font-feature-settings:"liga";
  font-variation-settings:normal;white-space:nowrap;letter-spacing:normal;user-select:none}
.mrp-v2-menu-icon::before{content:"menu"}
.mrp-v2-menu-toggle[aria-expanded="true"] .mrp-v2-menu-icon::before{content:"close"}
@media(max-width:700px){
  html[data-mrp-menu-ready] .mrp-v2-menu-toggle{margin-right:4px}
}
</style>
"""
