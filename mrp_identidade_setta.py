"""Assets e tipografia da Setta v4.0, locais e sem requisições externas."""
from base64 import b64encode
from functools import lru_cache
from io import BytesIO
from pathlib import Path


ASSETS = Path(__file__).resolve().parent / "assets"
GRAFITE = "333333"
CINZA_ESCURO = "424242"
CINZA_CLARO = "E1E1E1"
CINZA_FUNDO = "F0F0F0"
AMARELO = "FFBB00"
EXCEL_LAYOUT_VERSION = "setta-v4.0"


@lru_cache(maxsize=4)
def _encoded_asset(filename):
    return b64encode((ASSETS / filename).read_bytes()).decode("ascii")


def logo_data_uri():
    return "data:image/svg+xml;base64," + _encoded_asset("setta-logo-oficial.svg")


@lru_cache(maxsize=1)
def favicon_png():
    from PIL import Image, ImageDraw

    # Ícone de app: arte oficial sem distorção, fundo grafite, aro branco e
    # cantos transparentes. Supersampling mantém o contorno limpo na aba.
    size, scale = 256, 4
    edge = size * scale
    tile = Image.new("RGBA", (edge, edge))
    shape = ImageDraw.Draw(tile)
    shape.rounded_rectangle((4*scale, 4*scale, edge-4*scale-1, edge-4*scale-1),
                            radius=58*scale, fill="#FFFFFF")
    shape.rounded_rectangle((13*scale, 13*scale, edge-13*scale-1, edge-13*scale-1),
                            radius=49*scale, fill="#" + GRAFITE)
    tile = tile.resize((size, size), Image.Resampling.LANCZOS)
    with Image.open(ASSETS / "setta-simbolo-oficial.png") as source:
        art = source.convert("RGBA")
        art = art.resize((202, 202), Image.Resampling.LANCZOS)
    tile.alpha_composite(art, ((size - art.width)//2, (size - art.height)//2))
    content = BytesIO()
    tile.save(content, format="PNG", optimize=True)
    return content.getvalue()


@lru_cache(maxsize=1)
def identidade_css():
    return """<style>
@font-face {
  font-family: Outfit;
  src: url(data:font/woff2;base64,__OUTFIT__) format("woff2");
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
}
body:has(.setta-login-wrap) .stApp,
body:has(.mrp-v2-header) .stApp,
body:has(.setta-login-wrap) :is(.setta-login-title,h1,h2,h3,p,label,input,button),
body:has(.mrp-v2-header) :is(.mrp-v2-top,.mrp-v2-intro) :is(b,span,div),
body:has(.mrp-v2-header) .sidebar-section-label,
body:has(.mrp-v2-header) :is(h1,h2,h3,h4,p,label,input,textarea,button,[role="tab"],[data-baseweb="select"],[data-testid="stMetricValue"]) {
  font-family: Outfit, "Source Sans Pro", system-ui, sans-serif !important;
}
body:has(.setta-login-wrap) :is(.stApp,[data-testid="stMain"],[data-testid="stMainBlockContainer"]) {
  background:#F0F0F0!important;
}
body:has(.setta-login-wrap) .setta-login-wrap { border-color:#E1E1E1!important; }
body:has(.setta-login-wrap) [data-testid="stForm"] [data-baseweb="input"] {
  background:#F0F0F0!important; border:1px solid #767676!important;
}
body:has(.setta-login-wrap) [data-testid="stForm"] input::placeholder { color:#656565!important; }
body:has(.setta-login-wrap) [data-testid="stForm"] [data-baseweb="input"]:focus-within {
  outline:2px solid #333333; outline-offset:2px;
}
body:has(.setta-login-wrap) [data-testid="stFormSubmitButton"] button {
  background:#FFBB00!important; border-color:#FFBB00!important; color:#333333!important;
}
body:has(.setta-login-wrap) [data-testid="stFormSubmitButton"] button p { color:inherit!important; }
body:has(.setta-login-wrap) [data-testid="stFormSubmitButton"] button:hover {
  background:#F0AF00!important; border-color:#F0AF00!important;
}
body:has(.setta-login-wrap) [data-testid="stFormSubmitButton"] button:focus-visible {
  outline:2px solid #333333; outline-offset:2px;
}
body:has(.mrp-v2-header) [data-baseweb="tab-highlight"] {
  background:#FFBB00!important;
}
body:has(.mrp-v2-header) [data-baseweb="tab-list"] [aria-selected="true"] {
  color:#333333!important;
}
@media(max-width:480px) {
  body:has(.setta-login-wrap) .setta-login-wrap { width:min(360px,calc(100vw - 20px))!important; }
  body:has(.setta-login-wrap) [data-testid="stForm"] { width:min(312px,calc(100vw - 56px))!important; }
}
</style>""".replace("__OUTFIT__", _encoded_asset("outfit-latin.woff2"))
