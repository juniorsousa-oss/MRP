"""Apresentação do MRP; não depende do motor de cálculo nem do Protheus."""
from html import escape
import re


_SECOES = {
    "MRP ATUAL": ("MRP atual", "Planejamento e acompanhamento de materiais"),
    "SOLICITAÇÕES AVULSAS": ("Solicitações avulsas", "Separação, entrega e histórico"),
    "CONFIGURAÇÕES": ("Configurações", "Bases, visual e controles do MRP"),
}
_ESTADOS = {
    "ATUALIZADO": ("ok", "Atualizado"),
    "ATENÇÃO": ("atencao", "Atenção"),
    "ERRO": ("erro", "Falha na atualização"),
}

WORKSPACE_CSS = """
<style>
.mrp-workspace-head{display:flex;align-items:center;gap:18px;flex-wrap:wrap;
  padding:16px 20px;margin:0 0 8px;background:#fff;border:1px solid #dfe5ec;
  border-radius:12px;color:#111827}
.mrp-workspace-brand{display:flex;align-items:center;justify-content:center;
  min-width:76px;padding-right:16px;border-right:1px solid #e5e8ee;font-weight:800}
.mrp-workspace-brand img{display:block;width:76px;max-height:36px;object-fit:contain}
.mrp-workspace-copy{flex:1;min-width:155px}
.mrp-workspace-head h1{font-size:clamp(1.2rem,2vw,1.55rem)!important;
  line-height:1.2!important;letter-spacing:-.025em!important;color:#111827!important;
  padding:0!important;margin:0 0 3px!important;text-transform:none!important}
.mrp-workspace-head p{margin:0;color:#475569;font-size:.82rem;line-height:1.4}
.mrp-workspace-status{font-size:.76rem;color:#475569;text-align:right;line-height:1.45}
.mrp-workspace-status strong{display:block;color:#334155}
.mrp-workspace-status[data-state="ok"] strong{color:#166534}
.mrp-workspace-status[data-state="atencao"] strong{color:#92400e}
.mrp-workspace-status[data-state="erro"] strong{color:#991b1b}
.mrp-buy-step{display:flex;gap:.6rem;align-items:center;margin:10px 0 4px;color:#0f172a}
.mrp-buy-step span{display:grid;place-items:center;width:26px;height:26px;
  flex:none;border-radius:7px;background:#e8eef5;color:#1e3551;font-size:.8rem;font-weight:750}
.mrp-buy-step h3{font-size:1rem!important;line-height:1.3!important;margin:0!important;
  padding:0!important;color:#0f172a!important;text-transform:none!important}
body:has(.mrp-workspace-head) .mrp-ped-hero{background:#fff!important;
  color:#0f172a!important;border:1px solid #dfe5ec;padding:12px 16px!important;
  border-radius:10px;margin:6px 0 12px}
body:has(.mrp-workspace-head) .mrp-ped-hero h2{color:#0f172a!important;
  font-size:1.02rem!important;margin:0 0 3px!important}
body:has(.mrp-workspace-head) .mrp-ped-hero p{color:#475569!important}
body:has(.mrp-workspace-head) .mrp-ped-kicker{display:none}
@media(max-width:600px){
  .mrp-workspace-head{gap:10px;padding:12px}
  .mrp-workspace-brand{min-width:57px;padding-right:10px}
  .mrp-workspace-brand img{width:54px;max-height:28px}
  .mrp-workspace-status{flex-basis:100%;text-align:left;border-top:1px solid #e5e8ee;padding-top:7px}
  .mrp-workspace-status strong{display:inline;margin-right:.45rem}
}
</style>
"""

LOGIN_COMPACTO_CSS = """
<style>
body:has(.setta-login-wrap) .stApp,
body:has(.setta-login-wrap) [data-testid="stAppViewContainer"],
body:has(.setta-login-wrap) [data-testid="stMain"]{
  background:#f1f5f9!important;border:0!important;box-shadow:none!important;border-radius:0!important
}
body:has(.setta-login-wrap) .setta-login-wrap{
  width:min(400px,calc(100vw - 28px))!important;border:1px solid #dbe3eb!important;
  border-radius:16px!important;box-shadow:0 10px 30px rgba(15,23,42,.09)!important
}
body:has(.setta-login-wrap) div[data-testid="stForm"]{
  width:min(300px,calc(100vw - 68px))!important
}
body:has(.setta-login-wrap) div[data-testid="stForm"] [data-baseweb="input"]{
  border:1px solid #94a3b8!important;background:#fff!important
}
body:has(.setta-login-wrap) div[data-testid="stForm"] [data-baseweb="input"]:focus-within{
  outline:2px solid #315983!important;outline-offset:1px
}
</style>
"""


def cabecalho_html(pagina, logo_url, status, quando):
    titulo, descricao = _SECOES.get(pagina, _SECOES["MRP ATUAL"])
    classe, rotulo = _ESTADOS.get(status, ("atencao", "Status indisponível"))
    logo = str(logo_url or "")
    # Apenas imagens raster da configuração de marca, sem conteúdo HTML.
    seguro = re.fullmatch(r"data:image/(?:png|jpeg|jpg|webp|gif);base64,[A-Za-z0-9+/=]+", logo)
    marca = f'<img src="{escape(logo, quote=True)}" alt="SETTA">' if seguro else "SETTA"
    data = str(quando or "").strip()
    data = "Sem horário registrado" if data in ("", "—") else data
    return (
        '<header class="mrp-workspace-head" aria-label="Página do MRP SETTA">'
        + f'<div class="mrp-workspace-brand">{marca}</div>'
        + f'<div class="mrp-workspace-copy"><h1>{titulo}</h1><p>{descricao}</p></div>'
        + f'<div class="mrp-workspace-status" data-state="{classe}">'
        + f'<strong>{rotulo}</strong>{escape(data)}</div></header>'
    )


def etapa_compra_html(numero, titulo):
    return (
        f'<div class="mrp-buy-step"><span aria-hidden="true">{int(numero)}</span>'
        + f'<h3>{escape(titulo)}</h3></div>'
    )
