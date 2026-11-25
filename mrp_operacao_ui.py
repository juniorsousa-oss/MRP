"""Apresentação da área de trabalho; sem cálculo ou persistência do MRP."""
from html import escape
import streamlit as st

from mrp_operacao_grade import grade_resultado as operacao_grade

OPERACAO_CSS = """
<style>
body:has(.mrp-operacao) .mrp-workspace-head{
  padding:0 0 3px;border:0;border-radius:0;background:none;margin:0;
}
body:has(.mrp-operacao) .mrp-workspace-head h1{font-size:1.62rem!important}
.mrp-operacao-brandbar{display:flex;align-items:center;gap:10px;
  background:#fff;border:1px solid #dce3ec;border-radius:7px;
  min-height:40px;padding:0 12px;color:#4d6075;font-size:.8rem}
.mrp-operacao-brandbar strong{color:#213e60}
body:has(.mrp-operacao) .mrp-workspace-brand{display:none}
@media(min-width:901px){
  body:has(.mrp-operacao) [data-testid="stSidebar"][aria-expanded="true"]{
    width:210px!important;min-width:210px!important;max-width:210px!important;
  }
  body:has(.mrp-operacao) [data-testid="stSidebarContent"]{
    padding-left:10px!important;padding-right:10px!important;
  }
}
[class*="st-key-mrp_operacao_kpis_"] [data-testid="stButton"] button{
  min-height:44px!important;
}

body:has(.mrp-operacao) [data-testid="stMainBlockContainer"]{
  padding-left:clamp(1rem,2vw,2rem)!important;padding-right:clamp(1rem,2vw,2rem)!important
}
[class*="st-key-mrp_operacao_kpis_"] [data-testid="stHorizontalBlock"]{gap:0!important}
[class*="st-key-mrp_operacao_kpis_"] [data-testid="stButton"] button{
  min-height:52px;border-radius:0;border:1px solid #dce3ec;
  background:#fff;color:#213e60;box-shadow:none;justify-content:flex-start;
  padding:8px 12px;white-space:normal;
}
[class*="st-key-mrp_operacao_kpis_"] [data-testid="stButton"] button p{font-size:.77rem}
[class*="_operacao_kpi_"] button strong{font-size:.97rem;color:#233e5e}
[class*="_operacao_kpi_1"] button strong{color:#246549}
[class*="_operacao_kpi_2"] button strong{color:#86520c}
[class*="_operacao_kpi_3"] button strong{color:#a72e3e}
[class*="st-key-mrp_operacao_kpis_"] button[data-testid="stBaseButton-primary"],
[class*="st-key-mrp_operacao_kpis_"] button:hover{
  background:#e9f0fa;color:#1d3c60;border-bottom:2px solid #315983;
}
[class*="st-key-mrp_operacao_kpis_"] button:focus-visible{outline:2px solid #315983;outline-offset:-2px}
body:has(.mrp-operacao) :is(.st-key-mrp_admin_tabs,.st-key-consulta_tabs_kpi) [role="tablist"],
body:has(.mrp-operacao) [data-testid="stTabs"]:has(.mrp-operacao-tools) [role="tablist"]{
  background:#fff;border-radius:8px 8px 0 0;border:1px solid #dce3ec;
  padding:0 10px;max-width:100%;overflow-x:auto;
}
.mrp-operacao-tools{display:none}
[class*="st-key-mrp_operacao_bar_"]{
  background:#fff;border:1px solid #dce3ec;border-radius:7px;padding:9px 10px;
}
[class*="st-key-mrp_operacao_bar_"] [data-testid="stForm"]{
  padding:0!important;margin:0!important;background:transparent!important;border:0!important;
}
[class*="st-key-mrp_operacao_bar_"] [data-testid="stHorizontalBlock"]{
  column-gap:8px!important;row-gap:8px!important;
}
[class*="st-key-mrp_operacao_bar_"] button{
  min-height:38px!important;height:38px!important;padding:3px 7px!important;
}
[class*="st-key-mrp_operacao_bar_"] button,
[class*="st-key-mrp_operacao_bar_"] button p{
  text-transform:none!important;overflow-wrap:normal!important;word-break:normal!important;
  white-space:nowrap!important;font-size:.8rem!important;line-height:1.2!important;
}
[class*="st-key-mrp_operacao_bar_"] [data-testid="stPopoverButton"] svg{
  flex-shrink:0;width:15px!important;height:15px!important;
}
[class*="st-key-mrp_operacao_bar_"] [data-testid="stHtml"]:has(.mrp-operacao-tools){
  display:none!important;
}
[class*="st-key-mrp_operacao_bar_"] [data-testid="stElementContainer"]:has(.mrp-operacao-tools){
  display:none!important;
}
body:has(.mrp-operacao) [data-testid="stSidebarUserContent"] > :first-child{
  display:flex!important;flex:1 0 auto!important;
}
body:has(.mrp-operacao) [data-testid="stSidebarUserContent"] > :first-child > [data-testid="stVerticalBlock"]{
  flex:1 0 auto!important;
}
body:has(.mrp-operacao) [data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] > :has(.st-key-mrp_sidebar_account){
  margin-top:auto!important;
}
[class*="st-key-mrp_operacao_bar_"] [data-testid="stBaseButton-primary"]{
  background:#213e60!important;color:#fff!important;border-color:#213e60!important
}
.mrp-material-sheet{display:grid;gap:4px;color:#172437}
.mrp-material-sheet small{font-size:.75rem;color:#4d6075}
.mrp-material-sheet strong{font-size:1.08rem;overflow-wrap:anywhere}
.mrp-material-sheet span{font-size:.8rem;color:#4d6075}
[data-testid="stDialog"] [role="dialog"]:has(.mrp-material-sheet){
  position:fixed!important;inset:0 0 0 auto!important;margin:0!important;
  width:min(680px,100vw)!important;max-width:100vw!important;
  min-height:0!important;height:100dvh!important;max-height:100dvh!important;
  overflow:auto!important;border-radius:0!important;background:#fff!important;
}
@media(max-width:900px){
  [class*="st-key-mrp_operacao_kpis_"] [data-testid="stColumn"]{
    flex:1 1 31%!important;width:auto!important;max-width:none!important;
  }
}
@media(max-width:1150px){
  [class*="st-key-mrp_operacao_bar_"] [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}
  [class*="st-key-mrp_operacao_bar_"] [data-testid="stColumn"]{
    flex:1 1 40%!important;width:auto!important;max-width:none!important;
  }
  [class*="st-key-mrp_operacao_bar_"] [data-testid="stColumn"]:has(form){
    flex-basis:100%!important;
  }
  [class*="st-key-mrp_operacao_bar_"] [data-testid="stColumn"]:has([class*="_compra_abrir"]){
    flex-basis:100%!important;
  }
  [class*="st-key-mrp_operacao_bar_"] [data-testid="stColumn"] [data-testid="stColumn"]{
    flex:1 1 40%!important;
  }
}
</style>
"""


def operacao_indicadores(prefixo, quantidades, callback, selecionado):
    labels = (
        ("Todas as demandas", "TODOS", True, "Todas as demandas por projeto."),
        ("No prazo", "🟢 DENTRO DO PRAZO", False, "Atendimento no prazo ou antes."),
        ("Atenção", "🟡 ATENÇÃO AO PRAZO", False, "Até 2 semanas após a necessidade."),
        ("Críticas", "🔴 ATENDIMENTO CRÍTICO", False, "Acima de 2 semanas ou sem previsão."),
        ("Não aptas", "⚪ DEMANDAS NÃO APTAS", True, "Resíduos, suspensas e canceladas."),
    )
    with st.container(key=f"mrp_operacao_kpis_{prefixo}"):
        for i, (col, (label, status, mostrar, dica), valor) in enumerate(zip(st.columns(5, gap=None), labels, quantidades)):
            col.button(f"**{valor}** · {label}", key=f"{prefixo}_operacao_kpi_{i}",
                       type="primary" if status == selecionado else "secondary",
                       help=dica, width="stretch", on_click=callback, args=(status, mostrar))


def operacao_rotulo_grade(total):
    quantidade = f"{total:,}".replace(",", ".")
    return f"{quantidade} {'material' if total == 1 else 'materiais'} · Use Detalhe para abrir o material."


def operacao_busca(frame, termo, codigo_mask):
    q = str(termo or "").strip()
    if not q:
        return frame
    if q.isdecimal():
        return frame[codigo_mask(frame["Código"], q)]
    desc = frame["Descrição"].fillna("").astype(str)
    return frame[desc.str.contains(q, case=False, na=False, regex=False) | codigo_mask(frame["Código"], q)]


def operacao_detalhe(base_key, codigo, descricao, linha, render):
    @st.dialog("Detalhe do material", width="large", on_dismiss="rerun")
    def painel():
        st.html('<div class="mrp-material-sheet">'
                f'<small>Material {escape(str(codigo))}</small>'
                f'<strong>{escape(str(descricao or ""))}</strong>'
                f'<span>{escape(str(linha.get("Tipo", "")))} · {escape(str(linha.get("Status", "")))}</span></div>')
        campos = (("Demanda", "Demanda"), ("Estoque", "Saldo em Estoque"), ("S.C.", "S.C."), ("P.C.", "P.C."))
        cols = st.columns(4)
        for col, (rotulo, chave) in zip(cols, campos):
            valor = linha.get(chave, "")
            col.metric(rotulo, str(valor) if str(valor) not in ("", "nan", "<NA>") else "—")
        render()
        if st.button("Voltar à consulta", key=f"{base_key}_voltar"):
            st.rerun()
    painel()
