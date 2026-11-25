"""Visual shell and routes for the existing Streamlit MRP."""
from contextlib import nullcontext
from html import escape
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


def workspace_pages(role):
    # Comparativo e Configurações eram exclusivas do administrador.
    return tuple(p for p in _ROUTES if role == "ADMIN" or p not in {"COMPARATIVO MRP", "CONFIGURAÇÕES"})


class WorkspaceSection(nullcontext):
    def __init__(self, opened):
        super().__init__()
        self.open = opened


def workspace_sidebar(st, pages, active, change):
    keys = {p: i for i, p in enumerate(_ROUTES)}
    for title, group in (("Planejamento", _PLANNING), ("Operações", _OPERATIONS), ("", ("CONFIGURAÇÕES",))):
        if title:
            st.html(f'<div class="sidebar-section-label">{title}</div>')
        for page in group:
            if page not in pages:
                continue
            name, _, icon = _ROUTES[page]
            st.button(name, key=f"mrp_nav_btn_{keys[page]}",
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
        '<header class="mrp-v2-header" aria-label="Página do MRP SETTA">'
        '<div class="mrp-v2-top">'
        f'<span class="mrp-v2-mark">{mark}</span><b class="mrp-v2-brand">MRP</b>'
        '<span class="mrp-v2-name">Planejamento de materiais</span>'
        f'<span class="mrp-v2-stamps">{stamps}</span><span class="mrp-v2-account">{escape(account)}</span>'
        '</div><div class="mrp-v2-intro">'
        f'<div class="mrp-v2-crumb">{section} / {title}</div>'
        f'<h1>{title}</h1><p>{description}</p><span class="mrp-v2-meta">{meta}</span>'
        f'<span class="mrp-v2-mobile-date">{stamps}</span>{alert}</div></header>'
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
body:has(.mrp-v2-header) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(> [data-testid="stHtml"] > style):not(:has(.mrp-v2-header)) {
  display:none!important
}
body:has(.mrp-v2-header) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(> [data-testid="stHtml"]:empty){display:none!important}
body:has(.mrp-v2-header) [data-testid="stMainMenu"]{color:#c1cee0!important}
body:has(.mrp-v2-header) [data-testid="stMain"]{background:#f0f3f8!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"],body:has(.mrp-v2-header) [data-testid="stSidebarContent"]{
  background:#142134!important;color:#f0f5ff!important}
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
body:has(.mrp-v2-header) [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button{
  background:#263d61!important;color:#fff!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding-top:12px!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button::before{display:none!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [class*="st-key-mrp_nav_btn_"] button{padding-left:11px!important}
body:has(.mrp-v2-header) [data-testid="stSidebar"] [data-mrp-toggle]{color:#fff!important;background:#263d61!important;border-color:#4b6385!important}
body:has(.mrp-v2-header) [data-mrp-toggle="Menu"]{min-width:34px!important;width:34px!important;height:34px!important;min-height:34px!important}
body:has(.mrp-v2-header) [data-mrp-toggle="Menu"]::after{display:none}
body:has(.mrp-v2-header):has([data-testid="stSidebar"][aria-expanded="false"]) .mrp-v2-top{padding-left:64px}
@media(min-width:901px){
  body:has(.mrp-v2-header) [data-testid="stSidebar"][aria-expanded="true"]{
    width:220px!important;min-width:220px!important;max-width:220px!important
  }
  body:has(.mrp-v2-header) [data-testid="stSidebarContent"]{padding:0 9px!important}
  body:has(.mrp-v2-header) [class*="st-key-mrp_operacao_kpis_"] [data-testid="stColumn"]{
    flex:1 1 0!important;min-width:0!important;max-width:none!important
  }
}
.mrp-v2-header{color:#172435}
.mrp-v2-top{min-height:58px;background:#142134;color:#fff;margin:0 -28px;
  padding:8px 28px;display:flex;align-items:center;gap:13px;border-bottom:1px solid #35445b}
.mrp-v2-mark{display:grid;place-items:center;box-sizing:border-box;width:88px;height:38px;
  background:white;color:#142134;border-radius:6px;padding:3px 7px;flex:none}
.mrp-v2-mark img{width:100%;height:100%;object-fit:contain}
.mrp-v2-brand{letter-spacing:.08em}
.mrp-v2-name{font-size:.76rem;color:#c1cee0;border-left:1px solid #415067;padding-left:13px}
.mrp-v2-stamps{margin-left:auto;color:#c1cee0;font-size:.75rem}
.mrp-v2-account{color:#fff;font-size:.8rem;font-weight:680;white-space:nowrap}
.mrp-v2-intro{padding-top:17px;position:relative}
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
@media(max-width:700px){
  body:has(.mrp-v2-header) [data-testid="stMainBlockContainer"]{padding:0 12px 18px!important}
  .mrp-v2-top{box-shadow:0 -16px 0 #142134;margin:0 -12px;padding:7px 12px 7px 64px;gap:8px;min-height:56px}
  .mrp-v2-mark{width:66px;height:30px;padding:2px 5px}
  .mrp-v2-account{font-size:.69rem;margin-left:auto;overflow:hidden;text-overflow:ellipsis}
  .mrp-v2-name,.mrp-v2-stamps{display:none}
  .mrp-v2-mobile-date{display:block;margin-top:3px}
  .mrp-v2-intro{padding-top:9px}
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
  body:has(.mrp-v2-header) [data-testid="stHeader"] button[data-mrp-toggle="Menu"]{min-width:34px!important;background:#263d61!important;color:#fff!important;border-color:#4b6385!important}

}
</style>
"""
