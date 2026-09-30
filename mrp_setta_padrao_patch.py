SETTA_PADRAO_PATCH = r'''
# =========================================================
# PADRÃO VISUAL SETTA — BASE MONITOR DE APIs
# =========================================================

_page_old = 'st.set_page_config(page_title="MRP | SETTA", page_icon="assets/mrp_setta_icon.png", layout="wide")'
_page_new = """def _mrp_browser_icon():
    try:
        from PIL import Image as _MRPImage
        _raw_icon=_central_mrp.favicon_bytes()
        if _raw_icon:
            _img=_MRPImage.open(BytesIO(_raw_icon))
            _img.load()
            return _img
    except Exception:
        pass
    return "📦"

st.set_page_config(
    page_title="MRP | SETTA",
    page_icon=_mrp_browser_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)"""
if _source.count(_page_old) != 1:
    raise RuntimeError("Configuração da página do MRP não encontrada para favicon global.")
_source = _source.replace(_page_old, _page_new, 1)

_login_anchor = 'PUBLIC_LOGIN_CONFIG = _public_login_config()\n'
_login_new = """PUBLIC_LOGIN_CONFIG = _public_login_config()
try:
    _mrp_visual_global=_central_mrp.load_visual_config()
    _mrp_global_logo=_central_mrp.logo_data_uri(_mrp_visual_global)
    if _mrp_global_logo:
        PUBLIC_LOGIN_CONFIG["login_image_data"]=_mrp_global_logo
except Exception:
    pass
PUBLIC_LOGIN_CONFIG.update({
    "app_title":"MRP | SETTA",
    "objective":"Planejamento de necessidades de materiais",
    "color_primary":"#111827",
    "color_title":"#111827",
    "color_header":"#FFFFFF",
    "color_background":"#F4F7FB",
    "color_text":"#111827",
})
"""
if _source.count(_login_anchor) != 1:
    raise RuntimeError("Configuração pública do login não encontrada para padrão SETTA.")
_source = _source.replace(_login_anchor, _login_new, 1)

_ui_settings_call = '_render_visual_settings(UI_CONFIG)\n'
if _ui_settings_call in _source:
    _source = _source.replace(_ui_settings_call, '', 1)

_theme_anchor = '_apply_visual_theme(UI_CONFIG)\n'
_theme_injection = """try:
    _mrp_visual_global=_central_mrp.load_visual_config()
    _mrp_global_logo=_central_mrp.logo_data_uri(_mrp_visual_global)
except Exception:
    _mrp_visual_global={}
    _mrp_global_logo=""
UI_CONFIG.update({
    "logo_data":_mrp_global_logo,
    "logo_width":205,
    "app_title":"MRP | SETTA",
    "objective":"Planejamento de necessidades de materiais",
    "section_main_title":"MRP | SETTA",
    "section_main_description":"Planejamento • Demanda • Compras • Atendimento",
    "main_notice":"",
    "color_primary":"#111827",
    "color_title":"#111827",
    "color_header":"#FFFFFF",
    "color_background":"#F4F7FB",
    "color_text":"#111827",
})
st.session_state["ui_config"] = UI_CONFIG
"""
if _source.count(_theme_anchor) != 1:
    raise RuntimeError("Aplicação do tema do MRP não encontrada para identidade global.")
_source = _source.replace(
    _theme_anchor,
    _theme_injection + _theme_anchor,
    1,
)

_title_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_setta_css = """
<style>
:root{
  --setta-bg:#f4f7fb;
  --setta-card:#ffffff;
  --setta-border:#e5e8ee;
  --setta-text:#111827;
  --setta-muted:#667085;
  --setta-red:#ef4444;
  --setta-green:#22c55e;
}
.stApp{background:var(--setta-bg)!important;color:var(--setta-text)!important}
[data-testid="stHeader"]{background:rgba(255,255,255,.96)!important}

.block-container{
  max-width:1780px!important;
  width:100%!important;
  padding-top:3.2rem!important;
  padding-left:2.7rem!important;
  padding-right:2.7rem!important;
  padding-bottom:3rem!important;
}

section[data-testid="stSidebar"]{
  background:#fff!important;
  border-right:1px solid #e8ebf0!important;
}
section[data-testid="stSidebar"] .block-container{
  padding-top:1.6rem!important;
  padding-left:1rem!important;
  padding-right:1rem!important;
}
.sidebar-brand{
  background:#f8fafc;
  border:1px solid #e5e8ee;
  border-radius:12px;
  padding:.9rem 1rem;
  margin:0 0 1.05rem 0;
}
.sidebar-brand-title{
  font-size:.92rem;
  font-weight:800;
  color:#111827;
  letter-spacing:-.01em;
}
.sidebar-brand-sub{
  margin-top:.18rem;
  font-size:.75rem;
  color:#6b7280;
}
.sidebar-section-label{
  margin:.25rem 0 .45rem;
  color:#374151;
  font-size:.76rem;
  font-weight:800;
  text-transform:uppercase;
  letter-spacing:.055em;
}
.sidebar-info-card{
  background:#f8fafc;
  border:1px solid #e5e8ee;
  border-radius:10px;
  padding:.75rem .85rem;
  color:#6b7280;
  font-size:.76rem;
  line-height:1.55;
}
.sidebar-tools-label{
  margin-top:1.15rem!important;
}
section[data-testid="stSidebar"] details{
  border:1px solid #e5e8ee!important;
  border-radius:10px!important;
  background:#fff!important;
  margin:.35rem 0!important;
  overflow:hidden!important;
}
section[data-testid="stSidebar"] details summary{
  min-height:42px!important;
  display:flex!important;
  align-items:center!important;
  font-size:.78rem!important;
  font-weight:700!important;
  color:#374151!important;
}
section[data-testid="stSidebar"] details summary p{
  text-transform:uppercase!important;
  font-size:.78rem!important;
  font-weight:700!important;
}
section[data-testid="stSidebar"] .stButton>button{
  min-height:42px!important;
}

section[data-testid="stSidebar"] div[role="radiogroup"]{
  display:flex;
  flex-direction:column;
  gap:.34rem;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  position:relative;
  width:100%;
  min-height:42px;
  display:flex!important;
  align-items:center!important;
  padding:.56rem .72rem .56rem .88rem!important;
  margin:0!important;
  border:1px solid transparent!important;
  border-radius:10px!important;
  background:transparent!important;
  cursor:pointer;
  box-sizing:border-box;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label>div:first-child{
  position:absolute!important;
  opacity:0!important;
  width:0!important;
  height:0!important;
  overflow:hidden!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{
  margin:0!important;
  font-size:.83rem!important;
  font-weight:600!important;
  color:#374151!important;
  line-height:1.25!important;
  text-transform:uppercase!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
  background:#f8fafc!important;
  border-color:#e5e7eb!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
  background:#111827!important;
  border-color:#111827!important;
  box-shadow:0 5px 14px rgba(17,24,39,.14)!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked)::before{
  content:"";
  position:absolute;
  left:.42rem;
  top:50%;
  width:4px;
  height:20px;
  border-radius:999px;
  background:#ef4444;
  transform:translateY(-50%);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{
  color:#fff!important;
  font-weight:700!important;
}

[data-testid="stElementContainer"]:has(style):not(:has(.setta-logo-card)){
  display:none!important;
  margin:0!important;
  padding:0!important;
  height:0!important;
  min-height:0!important;
}
.setta-brand{
  width:100%!important;
  min-height:128px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  background:#fff!important;
  border:1px solid #e5e8ee!important;
  border-radius:16px!important;
  box-shadow:0 4px 14px rgba(24,39,75,.08)!important;
  box-sizing:border-box!important;
  margin:0 0 1.85rem!important;
  padding:1.1rem 2rem!important;
}
.setta-brand-logo{
  width:100%!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.setta-brand-logo img{
  display:block!important;
  width:auto!important;
  height:auto!important;
  max-width:205px!important;
  max-height:86px!important;
  object-fit:contain!important;
  margin:0!important;
}
div[data-testid="stElementContainer"]:has(.app-title){
  margin-top:0!important;
  padding-top:0!important;
}
[data-testid="stMarkdownContainer"] h1 a,
[data-testid="stMarkdownContainer"] h2 a,
[data-testid="stMarkdownContainer"] h3 a{
  display:none!important;
}
.app-title{
  margin:0!important;
  padding:0!important;
  font-size:2.55rem!important;
  line-height:1.08!important;
  font-weight:800!important;
  letter-spacing:-.04em!important;
  color:#050505!important;
}
.app-subtitle,.app-sub{
  margin-top:.72rem!important;
  margin-bottom:1.65rem!important;
  color:#4f5661!important;
  font-size:.94rem!important;
  line-height:1.35!important;
  text-transform:uppercase!important;
}

.section-band{
  margin:1.25rem 0 .95rem;
  padding:.82rem 1rem;
  background:#fff;
  border:1px solid #e5e8ee;
  border-left:5px solid #111827;
  border-radius:12px;
  box-shadow:0 3px 12px rgba(15,23,42,.035);
}
.section-band-kicker{
  font-size:.66rem;
  font-weight:900;
  letter-spacing:.085em;
  text-transform:uppercase;
  color:#ef4444;
  margin-bottom:.18rem;
}
.section-band-title{
  font-size:1.08rem;
  font-weight:900;
  color:#111827;
  letter-spacing:-.015em;
  line-height:1.2;
  text-transform:uppercase;
}
.topic-divider{
  height:1px;
  background:#cbd5e1;
  margin:1.55rem 0 1.05rem;
  width:100%;
}

.mrp-source-grid{
  display:grid;
  grid-template-columns:repeat(5,minmax(0,1fr));
  gap:.85rem;
  margin:.3rem 0 1rem;
}
.mrp-source-card{
  position:relative;
  background:#fff;
  border:1px solid #dfe3e8;
  border-radius:12px;
  padding:.88rem .95rem;
  box-shadow:0 3px 12px rgba(15,23,42,.035);
  overflow:hidden;
  min-height:102px;
}
.mrp-source-card::before{
  content:"";
  position:absolute;
  left:0;
  top:0;
  bottom:0;
  width:4px;
  background:#22c55e;
}
.mrp-source-name{
  font-size:.68rem;
  font-weight:900;
  color:#64748b;
  text-transform:uppercase;
  letter-spacing:.025em;
}
.mrp-source-status{
  margin-top:.42rem;
  font-size:.86rem;
  font-weight:900;
  color:#111827;
  text-transform:uppercase;
}
.mrp-source-meta{
  margin-top:.34rem;
  font-size:.65rem;
  color:#94a3b8;
  line-height:1.35;
  text-transform:uppercase;
}

.mrp-output-card{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:1rem;
  margin:.6rem 0 .2rem;
  padding:.82rem 1rem;
  background:#f0fdf4;
  border:1px solid #bbf7d0;
  border-radius:10px;
}
.mrp-output-kicker{
  font-size:.64rem;
  font-weight:900;
  color:#166534;
  text-transform:uppercase;
  letter-spacing:.04em;
}
.mrp-output-status{
  margin-top:.12rem;
  font-size:.88rem;
  font-weight:900;
  color:#166534;
}
.mrp-output-meta{
  font-size:.74rem;
  font-weight:700;
  color:#166534;
  text-align:right;
  text-transform:uppercase;
}

div[data-testid="stMetric"]{
  position:relative!important;
  min-height:110px!important;
  padding:15px 17px!important;
  border:1px solid #dfe3e8!important;
  border-radius:12px!important;
  background:#fff!important;
  box-shadow:0 3px 12px rgba(15,23,42,.04)!important;
  overflow:hidden!important;
}
div[data-testid="stMetric"]::before{
  content:"";
  position:absolute;
  left:0;
  top:0;
  bottom:0;
  width:4px;
  background:#111827;
}
div[data-testid="stMetricLabel"] p{
  color:#64748b!important;
  font-size:.68rem!important;
  font-weight:900!important;
  text-transform:uppercase!important;
}
div[data-testid="stMetricValue"]{
  color:#111827!important;
  font-size:1.55rem!important;
  font-weight:900!important;
  letter-spacing:-.02em!important;
}

[data-testid="stWidgetLabel"] p{
  text-transform:uppercase!important;
  font-weight:700!important;
}
div[data-baseweb="tab-list"]{
  gap:1.05rem!important;
  border-bottom:1px solid #cbd5e1!important;
  overflow-x:auto!important;
  white-space:nowrap!important;
  scrollbar-width:none!important;
}
div[data-baseweb="tab-list"]::-webkit-scrollbar{display:none!important}
div[data-baseweb="tab-list"] button{
  flex:0 0 auto!important;
  padding:.68rem .15rem .62rem!important;
  color:#64748b!important;
  font-size:.76rem!important;
  font-weight:800!important;
  text-transform:uppercase!important;
  letter-spacing:.01em!important;
}
div[data-baseweb="tab-list"] button[aria-selected="true"]{
  color:#111827!important;
  border-bottom-color:#ef4444!important;
}

div.stButton > button,
div.stDownloadButton > button{
  border-radius:9px!important;
  font-weight:800!important;
}
div.stButton > button[kind="primary"],
div.stDownloadButton > button{
  background:#111827!important;
  border-color:#111827!important;
  color:#fff!important;
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button:hover{
  background:#1f2937!important;
  border-color:#1f2937!important;
}

hr{
  border:0!important;
  border-top:1px solid #cbd5e1!important;
  margin:1.55rem 0 1.05rem!important;
}

[data-testid="stDataFrame"]{
  border:1px solid #e5e8ee!important;
  border-radius:12px!important;
  overflow:hidden!important;
  background:#fff!important;
}

@media(max-width:1250px){
  .mrp-source-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media(max-width:900px){
  div[data-testid="stElementContainer"]:has(.app-title){margin-top:0!important}
  .block-container{
    padding-top:2rem!important;
    padding-left:1rem!important;
    padding-right:1rem!important;
    padding-bottom:2rem!important;
  }
  .setta-brand{min-height:105px;margin-bottom:1.8rem!important;padding:.9rem 1rem!important}
  .setta-brand-logo img{max-width:170px!important;max-height:72px!important}
  .app-title{font-size:2rem!important}
  .mrp-source-grid{grid-template-columns:1fr!important}
  .mrp-output-card{align-items:flex-start;flex-direction:column}
  .mrp-output-meta{text-align:left}
}
</style>
"""

if _source.count(_title_anchor) != 1:
    raise RuntimeError("Título principal do MRP não encontrado para CSS padrão SETTA.")
_source = _source.replace(
    _title_anchor,
    'st.markdown(' + repr(_setta_css) + ', unsafe_allow_html=True)\n' + _title_anchor,
    1,
)

_metric_anchor = 'm=st.columns(5);'
_metric_header = """st.markdown(
    '<div class="section-band"><div class="section-band-kicker">01 · VISÃO DE DADOS</div>'
    '<div class="section-band-title">INDICADORES DO MRP</div></div>',
    unsafe_allow_html=True,
)
"""
if _source.count(_metric_anchor) == 1:
    _source = _source.replace(_metric_anchor, _metric_header + _metric_anchor, 1)

_tabs_candidates = [
    'tab1,tab2,tab3,tab4=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS", "COMPARATIVO MRP"])',
    'tab1,tab2,tab3=st.tabs([UI_CONFIG["title_demanda_geral"], UI_CONFIG["title_demanda_projeto"], "TRATATIVA DE PROJETOS"])',
]
for _tabs_anchor in _tabs_candidates:
    if _tabs_anchor in _source:
        _source = _source.replace(
            _tabs_anchor,
            'st.markdown(\'<div class="topic-divider"></div>\', unsafe_allow_html=True)\n'
            'st.markdown(\'<div class="section-band"><div class="section-band-kicker">02 · DEMANDA</div><div class="section-band-title">DEMANDA</div></div>\', unsafe_allow_html=True)\n'
            + _tabs_anchor,
            1,
        )
        break

_export_anchor = 'st.divider(); st.subheader(UI_CONFIG["section_export_title"])'
if _export_anchor in _source:
    _source = _source.replace(
        _export_anchor,
        'st.markdown(\'<div class="topic-divider"></div>\', unsafe_allow_html=True); '
        'st.markdown(\'<div class="section-band"><div class="section-band-kicker">03 · RELATÓRIOS</div><div class="section-band-title">RELATÓRIOS</div></div>\', unsafe_allow_html=True)',
        1,
    )
'''
