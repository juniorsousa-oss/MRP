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
           "_mrp_dashboard_navigate","_compra_abrir","normalizar_compra_mrp","formatar_data_br",
           "render_validacao_compra_mrp","_compra_menor_preco","_compra_codigo","_compra_botao_finalizar"}
helpers = "\n".join(ast.unparse(n) for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in methods)
APP = f"""
import pandas as pd
import re
import streamlit as st
from mrp_interface_visual import WORKSPACE_CSS
from mrp_abas_visual import ABAS_VISUAL_CSS, limpar_filtros_projeto
from mrp_excedentes import exibir_analise_excedentes
from datetime import date
from mrp_workspace import WORKSPACE_V2_CSS, WorkspaceSection, workspace_sidebar, workspace_pages, workspace_header, workspace_falta
from mrp_operacao_ui import OPERACAO_CSS, operacao_busca, operacao_indicadores, operacao_grade, operacao_detalhe, operacao_tabela_detalhe, operacao_rotulo_grade
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
st.html({shell!r})
st.html({nav_js!r},unsafe_allow_javascript=True)
st.html(WORKSPACE_CSS)
st.html(OPERACAO_CSS)
st.html(WORKSPACE_V2_CSS)
st.html(ABAS_VISUAL_CSS)
def _mrp_set_sidebar_page(page): st.session_state["_mrp_sidebar_page"]=page
st.session_state["auth_role"]="ADMIN"
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
def _compra_exclusoes_ler(): return {{}}
def _mrp_geral_export_sf(x): return x
def excel_bytes(x): return b"teste"
def zip_bytes(x): return b"teste"
def csv_bytes(x): return b"teste"
def formatar_semana(x): return str(x)
UI_CONFIG={{"title_demanda_geral":"DEMANDA GERAL","title_demanda_projeto":"DEMANDA POR PROJETO",
    "subsection_projection_title":"Projeção semanal","subsection_demand_title":"Demanda por projeto",
    "subsection_purchases_title":"Compras"}}
macro=pd.DataFrame({{"Código":[42,43],"Descrição":["Cabo para teste","Motor para teste"],"Tipo":["MP","PI"],
    "Saldo em Estoque":[1.01,4],"Demanda":[4.3,2],"P.C.":[5.4,0],"S.C.":[6.1,0],"Produzindo":[7.2,0],
    "DIV":[-3.25,2],"Status":["CRIAR S.C.","OK"],"Semana de Atendimento":["NN","202648"], "Período de Atendimento":["",""]}})
compras_mrp=pd.DataFrame([{{"produto":42,"qnt":3,"data":"25/11/2026","cc":"600307","op":"26001101001","prioridade":"1","vunit":1.5}}])
cad=macro
rg=macro
def periodo_semana(n): return str(n)
cp=pd.DataFrame({{"Código":[42],"Quantidade S.C.":[1],"Quantidade P.C.":[0],"Nº S.C.":["SC-42"],
    "Nº P.C.":[""],"Semana S.C.":["2026-47"],"Semana P.C.":[""]}})
proj=pd.DataFrame({{"Código":[42],"Descrição":["Cabo"],"Tipo":["MP"],"Semana":[202647],
    "Saldo Inicial":[1],"Demanda":[4],"P.C.":[0],"S.C.":[1],"Produzindo":[1],"Resumo Final":[0]}})
fab_det=pd.DataFrame({{"Código Produto":[42,42],"ORDEM DE PRODUÇÃO":["OP-42"," "],
    "Semana Entrega":["2026-47",None],"Quantidade":[1,None]}})
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
        p.set_default_timeout(8000)
        p.goto(URL,wait_until="domcontentloaded")
        expect(p.get_by_role("heading",name="Demanda Geral",exact=True)).to_be_visible(timeout=30000)
        expect(p.get_by_text("2 materiais ·",exact=False)).to_be_visible()
        assert p.evaluate("document.documentElement.scrollWidth") <= width+2
        expect(p.get_by_role("table")).to_be_visible() if width>700 else expect(p.locator(".op-item").first).to_be_visible()
        order = ["Necessidade", "Estoque", "P.C.", "S.C.", "Produzindo", "Falta"]
        if width>700:
            assert p.get_by_role("columnheader").all_text_contents() == [
                "Código", "Descrição", *order, "Status", "Detalhe"
            ]
            assert p.get_by_role("columnheader").nth(2).evaluate("el => getComputedStyle(el).textAlign") == "center"
            assert p.get_by_role("row").nth(1).get_by_role("cell").nth(2).evaluate(
                "el => getComputedStyle(el).textAlign") == "center"
            expect(p.get_by_role("columnheader").filter(has_text="Produzindo")).to_be_visible()
            first_row=p.get_by_role("row").filter(has_text="Cabo para teste")
            assert first_row.get_by_role("cell").all_text_contents()[2:8] == ["5", "2", "6", "7", "8", "4"]
            p.get_by_role("button",name="Produzindo",exact=True).click()
            expect(p.get_by_role("row").nth(1)).to_contain_text("Motor para teste")
        else:
            first_card=p.locator(".op-item").filter(has_text="Cabo para teste")
            assert first_card.locator(".op-item-value").all_text_contents() == [
                "Necessidade5", "Estoque2", "P.C.6", "S.C.7", "Produzindo8", "Falta4"
            ]
            assert first_card.locator(".op-item-value").first.evaluate(
                "el => getComputedStyle(el).textAlign") == "center"
            second_card=p.locator(".op-item").filter(has_text="Motor para teste")
            expect(second_card.locator(".op-item-value").filter(has_text="Produzindo")).to_have_text("Produzindo0")
        expect(p.get_by_role("heading",name="Revisar materiais")).to_have_count(0)
        expect(p.get_by_role("heading",name="Documentos com excedente")).to_have_count(0)
        if os.environ.get("MRP_LAYOUT_CAPTURES"):
            p.screenshot(path=f"/tmp/MRP-layout-{width}.png")
        controls=p.locator('[class*="st-key-mrp_operacao_bar_"] button')
        if width>1150:
            assert all(b<=45 for b in controls.evaluate_all("(nodes)=>nodes.map(e=>e.getBoundingClientRect().height).filter(Boolean)"))
        busca=p.get_by_placeholder("Buscar por código ou descrição")
        if width<=700:
            assert busca.bounding_box()["width"] >= 200
        p.get_by_role("button",name="Detalhar material 00000043",exact=True).click()
        empty_detail=p.get_by_role("dialog")
        empty_detail.get_by_role("tab",name="Produção",exact=True).click(timeout=8000)
        expect(empty_detail.get_by_text("Nenhuma ordem de produção vinculada.")).to_be_visible()
        empty_detail.get_by_role("button",name="Voltar à consulta").click()
        expect(empty_detail).not_to_be_visible()
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
        for label in ("Projeção", "Necessidades", "Compras", "Produção"):
            dlg.get_by_role("tab",name=label,exact=True).click()
            current=dlg.get_by_role("tabpanel").filter(visible=True)
            grid=current.get_by_test_id("stDataFrame")
            expect(grid).to_be_visible()
            if label=="Produção":
                assert grid.bounding_box()["height"] <= 95, grid.bounding_box()
                if os.environ.get("MRP_LAYOUT_CAPTURES"):
                    p.screenshot(path=f"/tmp/MRP-detail-production-{width}.png")

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
        project=p.locator(".st-key-mrp_visual_projeto")
        expect(project.get_by_text("Status de atendimento",exact=True)).to_be_visible()
        expect(project.get_by_text("Mostrar demandas não aptas",exact=True)).to_be_visible()
        project_button=project.get_by_role("button",name="Buscar",exact=True)
        expect(project_button.locator("p")).to_have_css("font-size","14px")
        assert abs(project_button.bounding_box()["height"] - 40)<2
        project.get_by_placeholder("Parte da descrição").fill("Cabo")
        project_button.click()
        expect(project.get_by_placeholder("Parte da descrição")).to_have_value("Cabo")
        project.get_by_role("button",name="Limpar",exact=True).click()
        expect(project.get_by_placeholder("Parte da descrição")).to_have_value("")
        if width < 700:
            top_fields=project.get_by_test_id("stSelectbox")
            boxes=[top_fields.nth(i).bounding_box() for i in range(top_fields.count())]
            assert abs(boxes[0]["y"]-boxes[1]["y"])<2, boxes
        if os.environ.get("MRP_LAYOUT_CAPTURES"):
            p.screenshot(path=f"/tmp/MRP-projeto-{width}.png")
        def nav(label):
            menu=p.get_by_role("button",name="Abrir menu lateral")
            if menu.is_visible():
                menu.click()
            p.get_by_role("button",name=label,exact=True).click()
        nav("Demanda Geral")
        p.get_by_role("button",name="Exportar",exact=False).click()
        expect(p.get_by_text("BAIXAR MRP GERAL",exact=False)).to_be_visible()
        p.keyboard.press("Escape")
        nav("Análise de Compra")
        buy=p.locator(".st-key-mrp_visual_compra")
        for section in ("Revisar materiais","Exportar prévia por OP","Liberar carga oficial do Protheus"):
            expect(buy.get_by_role("heading",name=section,exact=True)).to_have_css("font-size","18px")
        expect(p.get_by_role("heading",name="Análise de Compra",exact=True)).to_have_count(1)
        expect(buy.get_by_text("Produtos para exportar",exact=True)).to_be_visible()
        expect(buy.get_by_role("button",name="Preparar relatório por OP").locator("p")).to_have_css("font-size","14px")
        expect(buy.get_by_role("button",name="Baixar carga do Protheus")).to_be_disabled()
        buy.get_by_text("Mostrar campos técnicos",exact=True).click()
        expect(buy.get_by_role("checkbox",name="Mostrar campos técnicos")).to_be_checked()
        if os.environ.get("MRP_LAYOUT_CAPTURES"):
            p.locator('[data-testid="stMain"]').evaluate("el => el.scrollTop = 0")
            p.screenshot(path=f"/tmp/MRP-compra-{width}.png")
        nav("Excedentes")
        excess=p.locator(".st-key-mrp_visual_excedentes")
        expect(excess.get_by_role("heading",name="Documentos com excedente")).to_have_css("font-size","18px")
        expect(p.get_by_role("heading",name="Excedentes",exact=True)).to_have_count(1)
        expect(excess.get_by_text("S.C. com excedente",exact=True)).to_be_visible()
        expect(excess.get_by_text("P.C. com excedente",exact=True)).to_be_visible()
        excess.get_by_role("tab",name="Pedidos (P.C.)",exact=True).click()
        expect(excess.get_by_role("tab",name="Pedidos (P.C.)",exact=True)).to_have_attribute("aria-selected","true")
        download=excess.get_by_role("button",name="Baixar excedentes em Excel")
        expect(download.locator("p")).to_have_css("font-size","14px")
        with p.expect_download() as result:
            download.click()
        assert result.value.suggested_filename.endswith(".xlsx")
        if os.environ.get("MRP_LAYOUT_CAPTURES"):
            p.screenshot(path=f"/tmp/MRP-excedentes-{width}.png")
        expect(p.get_by_role("heading",name="Revisar materiais")).to_have_count(0)
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
