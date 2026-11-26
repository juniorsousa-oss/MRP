"""Tipografia e dimensões compartilhadas das abas operacionais do MRP."""

ABAS_VISUAL_CSS = """<style>
:where(.st-key-mrp_visual_projeto,.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes){
  --mrp-control-text:.875rem;
  --mrp-control-height:40px;
  --mrp-section-text:1.125rem;
  --mrp-border:#e1e1e1;
  --mrp-surface:#fff;
}
.st-key-mrp_visual_projeto{
  background:var(--mrp-surface);border:1px solid var(--mrp-border);
  border-radius:9px;padding:12px;
}
:is(.st-key-mrp_visual_projeto,.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes)
  [data-testid="stWidgetLabel"] p,
:is(.st-key-mrp_visual_projeto,.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes)
  [data-testid="stCheckbox"] label p{
  font-size:var(--mrp-control-text)!important;font-weight:600!important;text-transform:none!important;
}
:is(.st-key-mrp_visual_projeto,.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes)
  :is([data-baseweb="input"],[data-baseweb="select"] > div:first-child){
  min-height:var(--mrp-control-height);border-radius:6px;
}
:is(.st-key-mrp_visual_projeto,.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes)
  :is([data-testid="stButton"],[data-testid="stFormSubmitButton"],[data-testid="stDownloadButton"]) > button{
  min-height:var(--mrp-control-height)!important;border-radius:6px!important;box-shadow:none!important;
  padding:7px 12px!important;height:auto!important;white-space:normal!important;text-transform:none!important;
}
:is(.st-key-mrp_visual_projeto,.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes)
  :is([data-testid="stButton"],[data-testid="stFormSubmitButton"],[data-testid="stDownloadButton"]) > button p{
  font-size:var(--mrp-control-text)!important;font-weight:600!important;
  line-height:1.3!important;text-transform:none!important;overflow-wrap:anywhere;
}
.st-key-mrp_visual_projeto [data-testid="stFormSubmitButton"] button:is([data-testid^="stBaseButton-primary"],[kind^="primary"]),
.st-key-mrp_visual_compra [data-testid="stButton"] button:is([data-testid^="stBaseButton-primary"],[kind^="primary"]){
  background:#333333!important;border-color:#333333!important;color:#fff!important;
}
.st-key-mrp_visual_projeto [data-testid="stFormSubmitButton"] button:is([data-testid^="stBaseButton-primary"],[kind^="primary"]):hover,
.st-key-mrp_visual_compra [data-testid="stButton"] button:is([data-testid^="stBaseButton-primary"],[kind^="primary"]):hover{
  background:#424242!important;border-color:#424242!important;
}
:is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes) [data-testid="stDownloadButton"]{
  min-height:0!important;padding:0!important;
}
:is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes) [data-testid="stMetric"]{
  background:var(--mrp-surface)!important;border:1px solid var(--mrp-border)!important;
  border-radius:9px!important;box-shadow:none!important;min-height:0!important;padding:10px 12px!important;
}
:is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes) [data-testid="stMetric"]::before{display:none!important}
:is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes) [data-testid="stMetricLabel"] p{
  font-size:var(--mrp-control-text)!important;font-weight:600!important;text-transform:none!important;
  white-space:normal!important;overflow-wrap:anywhere;color:#525252!important;
}
:is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes) [data-testid="stMetricValue"]{
  font-size:1.375rem!important;font-weight:750!important;line-height:1.2!important;
}
:is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes) [data-testid="stDataFrame"]{
  border:1px solid var(--mrp-border)!important;border-radius:9px!important;
}
.st-key-mrp_visual_compra .mrp-buy-step h2,
.st-key-mrp_visual_excedentes :is(h2,h3){
  font-size:var(--mrp-section-text)!important;font-weight:750!important;line-height:1.3!important;
  padding:0!important;margin:0!important;color:#333333!important;text-transform:none!important;
}
.st-key-mrp_visual_compra .mrp-buy-step{margin:9px 0 0}
.st-key-mrp_visual_compra .mrp-buy-step span{border-radius:6px}
.st-key-mrp_visual_excedentes [data-testid="stTabs"] button[role="tab"]{
  min-height:var(--mrp-control-height);text-transform:none!important;
}
.st-key-mrp_visual_excedentes [data-testid="stTabs"] button[role="tab"] p{
  font-size:var(--mrp-control-text)!important;font-weight:600!important;text-transform:none!important;
}
.st-key-mrp_visual_excedentes [data-testid="stTabs"] button[role="tab"][aria-selected="true"]{
  color:#333333!important;
}
.st-key-mrp_visual_excedentes [data-baseweb="tab-highlight"]{background:#ffbb00!important}
@media(max-width:900px){
  .st-key-mrp_visual_projeto [data-testid="stHorizontalBlock"]:has([data-testid="stWidgetLabel"]) > [data-testid="stColumn"],
  .st-key-mrp_visual_projeto [data-testid="stHorizontalBlock"]:has([data-testid="stFormSubmitButton"]) > [data-testid="stColumn"],
  :is(.st-key-mrp_visual_compra,.st-key-mrp_visual_excedentes)
    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"]{
    flex:1 1 calc(50% - 7px)!important;width:auto!important;max-width:none!important;
  }
  .st-key-mrp_visual_projeto [data-testid="stHorizontalBlock"]:has([data-testid="stFormSubmitButton"])
    > [data-testid="stColumn"]:has([data-testid="stCheckbox"]){
    flex-basis:100%!important;margin-block:2px;
  }
  .st-key-mrp_visual_projeto [data-testid="stHorizontalBlock"]{gap:10px!important}
  .st-key-mrp_visual_compra [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
    > [data-testid="stColumn"]{flex-basis:calc(33.333% - 9px)!important}
  .st-key-mrp_visual_compra [data-testid="stMetric"]{padding:8px!important}
}
</style>"""


def limpar_filtros_projeto(valores):
    """Define os padrões explicitamente para que o formulário reflita Limpar."""
    import streamlit as st

    for chave, valor in valores.items():
        st.session_state[chave] = valor
