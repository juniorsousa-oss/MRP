"""Teste visual da tela ADMIN gerada, com dados sintéticos e sem serviços remotos."""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from mrp_engine_extract import montar_fonte_atual
from mrp_setta_ui_v1_patch import SETTA_UI_V1_PATCH

shell = next(ast.literal_eval(n.value) for n in ast.parse(SETTA_UI_V1_PATCH).body
             if isinstance(n, ast.Assign) and any(t.id == "_setta_css" for t in n.targets if isinstance(t, ast.Name)))
nav_js=next(ast.literal_eval(n.value) for n in ast.parse(SETTA_UI_V1_PATCH).body
            if isinstance(n, ast.Assign) and any(t.id=="_setta_close_on_navigation" for t in n.targets if isinstance(t,ast.Name)))
src = montar_fonte_atual()
lo = src.index('_mrp_manter_filtros_de_abas("admin_operacao_colunas")')
hi = src.index("\nif tab1.open:\n    export_macro=",lo)
limits = (src.index('if _mrp_page in {"MRP ATUAL","DEMANDA POR PROJETO"}:\n    _status_dashboard='), src.index("# Protege a última fotografia"))
methods = {"_setta_dataframe","_setta_table_height","_mrp_codigo_mask","_mrp_manter_filtros_de_abas",
           "_mrp_dashboard_navigate","_compra_abrir"}
helpers = "\n".join(ast.unparse(n) for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in methods)
APP = f"""
import pandas as pd
import re
import streamlit as st
from mrp_interface_visual import WORKSPACE_CSS
from mrp_workspace import WORKSPACE_V2_CSS, WorkspaceSection, workspace_sidebar, workspace_pages, workspace_header, workspace_falta
from mrp_operacao_ui import OPERACAO_CSS, operacao_busca, operacao_indicadores, operacao_grade, operacao_detalhe, operacao_rotulo_grade
st.set_page_config(layout="wide")
st.html({shell!r})
st.html({nav_js!r},unsafe_allow_javascript=True)
st.html(WORKSPACE_CSS)
st.html(OPERACAO_CSS)
st.html(WORKSPACE_V2_CSS)
def _mrp_set_sidebar_page(page): st.session_state["_mrp_sidebar_page"]=page
_mrp_page=st.session_state.get("_mrp_sidebar_page","MRP ATUAL")
st.html(workspace_header(_mrp_page,"","ATUALIZADO","08:10",semana="2026-47",bases=(5,5),registros="",alertas=[],nome="Almoxarifado",perfil="ADMIN"))
with st.sidebar:
    workspace_sidebar(st,workspace_pages("ADMIN"),_mrp_page,_mrp_set_sidebar_page)
{helpers}
def _limpar_filtros_mrp(*keys):
    for k in keys: st.session_state.pop(k,None)
def _mrp_demanda_nao_apta_mask(df): return pd.Series(False,index=df.index)
def _mrp_status_atendimento_series(df): return pd.Series(["🔴"]*len(df),index=df.index)
def _df_exibicao_br(df): return df
def _mrp_numero_br(x): return str(x)
def render_tratativa_projetos(): st.text("Tratativa")
def render_mrp_history(): st.text("Comparativo")
def render_validacao_compra_mrp(*args): st.text("Fluxo de compra de teste")
def exibir_analise_excedentes(*args, **kwargs): st.text("Fluxo de excedentes de teste")
def normalizar_compra_mrp(x): return x
def _mrp_geral_export_sf(x): return x
def excel_bytes(x): return b"teste"
def zip_bytes(x): return b"teste"
def csv_bytes(x): return b"teste"
def formatar_semana(x): return str(x)
UI_CONFIG={{"title_demanda_geral":"DEMANDA GERAL","title_demanda_projeto":"DEMANDA POR PROJETO",
    "subsection_projection_title":"Projeção semanal","subsection_demand_title":"Demanda por projeto",
    "subsection_purchases_title":"Compras"}}
macro=pd.DataFrame({{"Código":[42,43],"Descrição":["Cabo para teste","Motor para teste"],"Tipo":["MP","PI"],
    "Saldo em Estoque":[1,4],"Demanda":[4,2],"P.C.":[0,0],"S.C.":[0,0],"Produzindo":[0,0],
    "DIV":[-3,2],"Status":["CRIAR S.C.","OK"],"Semana de Atendimento":["NN","202648"], "Período de Atendimento":["",""]}})
compras_mrp=macro
cad=macro
rg=macro
cp=pd.DataFrame({{"Código":[42],"Quantidade S.C.":[0],"Quantidade P.C.":[0]}})
proj=pd.DataFrame({{"Código":[]}})
fab_det=pd.DataFrame({{"Código Produto":[]}})
demanda_projeto=pd.DataFrame({{"Produto":[42],"Projeto":["A"],"Semana de Necessidade":[202647],"Descrição":["Cabo"]}})
_status_dashboard=_mrp_status_atendimento_series(demanda_projeto)
{src[limits[0]:limits[1]]}
{src[lo:hi]}
if _mrp_page == "MRP ATUAL":
    with _admin_operacao_acoes:
        with st.popover("Exportar"):
            st.download_button("BAIXAR MRP GERAL — CSV",b"teste")

"""
URL="http://127.0.0.1:8516"

def check(browser, width, height):
    with browser.new_context(viewport={"width":width,"height":height}) as context:
        p=context.new_page()
        p.goto(URL,wait_until="domcontentloaded")
        expect(p.get_by_role("heading",name="Demanda Geral",exact=True)).to_be_visible(timeout=30000)
        expect(p.get_by_text("2 materiais ·",exact=False)).to_be_visible()
        assert p.evaluate("document.documentElement.scrollWidth") <= width+2
        expect(p.get_by_role("table")).to_be_visible() if width>700 else expect(p.locator(".op-item").first).to_be_visible()
        expect(p.get_by_text("Fluxo de compra de teste")).to_have_count(0)
        expect(p.get_by_text("Fluxo de excedentes de teste")).to_have_count(0)
        if os.environ.get("MRP_LAYOUT_CAPTURES"):
            p.screenshot(path=f"/tmp/MRP-layout-{width}.png")
        controls=p.locator('[class*="st-key-mrp_operacao_bar_"] button')
        if width>1150:
            assert all(b<=45 for b in controls.evaluate_all("(nodes)=>nodes.map(e=>e.getBoundingClientRect().height).filter(Boolean)"))
        busca=p.get_by_placeholder("Buscar por código ou descrição")
        if width<=700:
            assert busca.bounding_box()["width"] >= 200
        busca.fill("00000042")
        p.get_by_role("button",name="Buscar",exact=True).click()
        expect(p.get_by_text("1 material ·",exact=False)).to_be_visible()
        detail=p.get_by_role("button",name="Detalhar material 00000042")
        expect(detail).to_be_visible()
        if width<=900:
            assert detail.evaluate("""button => {
                const grid = button.closest('.op-scroll');
                const r=button.getBoundingClientRect(), s=grid.getBoundingClientRect();
                return grid.scrollLeft===0 && r.left>=s.left-1 && r.right<=s.right+1;
            }"""), "Detalhe não aparece antes de rolar a grade"
        detail.click()
        dlg=p.get_by_role("dialog")
        expect(dlg.get_by_text("Cabo para teste")).to_be_visible()
        assert abs(dlg.bounding_box()["x"]+dlg.bounding_box()["width"]-width)<3
        dlg.get_by_role("button",name="Voltar à consulta").click()
        expect(dlg).not_to_be_visible()
        detail.click()
        expect(dlg).to_be_visible()
        p.keyboard.press("Escape")
        expect(dlg).not_to_be_visible()
        p.get_by_role("button",name="Filtros").click()
        p.get_by_role("button",name="Limpar",exact=True).click()
        expect(p.get_by_text("2 materiais ·",exact=False)).to_be_visible()
        p.get_by_role("button",name="Críticas",exact=False).click()
        expect(p.get_by_role("heading",name="Demanda por Projeto",exact=True)).to_be_visible()
        def nav(label):
            if width<=900:
                p.get_by_role("button",name="Abrir menu lateral").click()
            p.get_by_role("button",name=label,exact=True).click()
        nav("Demanda Geral")
        p.get_by_role("button",name="Exportar",exact=False).click()
        expect(p.get_by_text("BAIXAR MRP GERAL",exact=False)).to_be_visible()
        p.keyboard.press("Escape")
        nav("Análise de Compra")
        expect(p.get_by_text("Fluxo de compra de teste")).to_be_visible()
        expect(p.get_by_role("searchbox")).to_have_count(0)
        nav("Excedentes")
        expect(p.get_by_text("Fluxo de excedentes de teste")).to_be_visible()
        expect(p.get_by_text("Fluxo de compra de teste")).to_have_count(0)
        print(f"MRP Operação {width}px: busca, atalhos, grade e ações sem erro.",flush=True)

def main():
    chrome=os.environ.get("MRP_CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    assert chrome
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as work:
        app=Path(work)/"app.py"
        app.write_text(f'import sys\nsys.path.insert(0,{str(root)!r})\n'+APP)
        with tempfile.TemporaryFile() as logs:
            proc=subprocess.Popen([sys.executable,"-m","streamlit","run",str(app),"--server.headless=true",
                                   "--server.port=8516","--browser.gatherUsageStats=false"],stdout=logs,stderr=logs)
            try:
                for _ in range(80):
                    try:
                        urllib.request.urlopen(URL,timeout=2).close()
                        break
                    except OSError:
                        time.sleep(.5)
                with sync_playwright() as p:
                    b=p.chromium.launch(executable_path=chrome,args=["--no-sandbox","--disable-dev-shm-usage"])
                    try:
                        for wh in [(1363,936),(390,844)]:check(b,*wh)
                    finally:
                        b.close()
            except Exception:
                logs.seek(0)
                print(logs.read().decode(),flush=True)
                raise
            finally:
                proc.terminate()
                proc.wait(timeout=8)

if __name__=="__main__": main()
