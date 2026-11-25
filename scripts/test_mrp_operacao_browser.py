"""Teste visual da tela ADMIN gerada, com dados sintéticos e sem serviços remotos."""
import ast
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
src = montar_fonte_atual()
limits = (src.index("operacao_indicadores('admin'"), src.index("# Protege a última fotografia"))
lo = src.index('_mrp_manter_filtros_de_abas("admin_operacao_colunas")')
hi = src.index("compras_mrp_export=", lo)
lo2 = src.index("with _admin_operacao_acoes:", hi)
hi2 = src.index("exibir_analise_excedentes(macro,cp,proj", lo2)
methods = {"_setta_dataframe","_setta_table_height","_mrp_codigo_mask","_mrp_manter_filtros_de_abas",
           "_mrp_dashboard_navigate","_compra_abrir"}
helpers = "\n".join(ast.unparse(n) for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in methods)
APP = f"""
import pandas as pd
import re
import streamlit as st
from mrp_interface_visual import WORKSPACE_CSS, cabecalho_html
from mrp_operacao_ui import OPERACAO_CSS, operacao_busca, operacao_indicadores, operacao_grade, operacao_detalhe
st.set_page_config(layout="wide")
st.html({shell!r})
st.html(WORKSPACE_CSS)
st.html(OPERACAO_CSS)
st.html('<span class="mrp-operacao" hidden></span>')
st.html(cabecalho_html("MRP ATUAL", "", "ATUALIZADO","08:10",semana="2026-47",bases=(5,5)))
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
    "DIV":[0,0],"Status":["CRIAR S.C.","OK"],"Semana de Atendimento":["NN","202648"], "Período de Atendimento":["",""]}})
cad=macro
rg=macro
cp=pd.DataFrame({{"Código":[42],"Quantidade S.C.":[0],"Quantidade P.C.":[0]}})
proj=pd.DataFrame({{"Código":[]}})
fab_det=pd.DataFrame({{"Código Produto":[]}})
demanda_projeto=pd.DataFrame({{"Produto":[42],"Projeto":["A"],"Semana de Necessidade":[202647],"Descrição":["Cabo"]}})
_status_dashboard=_mrp_status_atendimento_series(demanda_projeto)
{src[limits[0]:limits[1]]}
{src[lo:hi]}
compras_mrp_export=macro
export_macro=macro
sheets={{"MRP":macro}}
{src[lo2:hi2]}
"""
URL="http://127.0.0.1:8516"

def check(browser, width, height):
    with browser.new_context(viewport={"width":width,"height":height}) as context:
        p=context.new_page()
        p.goto(URL,wait_until="domcontentloaded")
        expect(p.get_by_role("heading",name="MRP atual")).to_be_visible(timeout=30000)
        expect(p.get_by_text("2 materiais",exact=False)).to_be_visible()
        assert p.evaluate("document.documentElement.scrollWidth") <= width+2
        busca=p.get_by_placeholder("Buscar por código ou descrição")
        busca.fill("00000042")
        p.get_by_role("button",name="Buscar",exact=True).click()
        expect(p.get_by_text("1 materiais",exact=False)).to_be_visible()
        if width>900:
            grid=p.get_by_test_id("stDataFrame").first
            canvas=grid.locator("canvas").first
            expect(canvas).to_be_visible()
            canvas.click(position={"x":15,"y":46})
            dlg=p.get_by_role("dialog")
            expect(dlg.get_by_text("Cabo para teste")).to_be_visible()
            assert abs(dlg.bounding_box()["x"]+dlg.bounding_box()["width"]-width)<3
            dlg.get_by_role("button",name="Voltar à consulta").click()
            expect(dlg).not_to_be_visible()
            canvas.click(position={"x":15,"y":46})
            expect(dlg).to_be_visible()
            p.keyboard.press("Escape")
            expect(dlg).not_to_be_visible()
        p.get_by_role("button",name="Filtros").click()
        p.get_by_role("button",name="Limpar",exact=True).click()
        expect(p.get_by_text("2 materiais",exact=False)).to_be_visible()
        p.get_by_role("button",name="Críticas",exact=False).click()
        expect(p.get_by_role("tab",name="DEMANDA POR PROJETO")).to_have_attribute("aria-selected","true")
        p.get_by_role("button",name="Exportar",exact=False).click()
        expect(p.get_by_text("BAIXAR MRP GERAL",exact=False)).to_be_visible()
        p.keyboard.press("Escape")
        p.get_by_role("button",name="ANÁLISE DE COMPRA",exact=True).click()
        expect(p.get_by_text("Fluxo de compra de teste")).to_be_visible()
        print(f"MRP Operação {width}px: busca, atalhos, grade e ações sem erro.",flush=True)

def main():
    chrome=shutil.which("google-chrome") or shutil.which("chromium")
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
                        for wh in [(1440,900),(390,844)]:check(b,*wh)
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
