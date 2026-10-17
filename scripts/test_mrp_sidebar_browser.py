"""Teste REAL do botão de abertura da sidebar no Chromium e no viewport mobile.
Executado apenas em ambiente de CI; não acessa Supabase nem dados internos.
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

from mrp_setta_ui_v1_patch import SETTA_UI_V1_PATCH

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse(SETTA_UI_V1_PATCH)
css_node = next(
    n.value for n in tree.body if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "_setta_css" for t in n.targets)
)
CSS = ast.literal_eval(css_node)
js_node=next(n.value for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=="_setta_close_on_navigation" for t in n.targets))
NAV_JS=ast.literal_eval(js_node)
URL = "http://127.0.0.1:8515"
ARTIFACTS = ROOT / "artifacts" / "sidebar-browser"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

APP = (
    'import streamlit as st\n'
    'st.set_page_config(layout="wide", initial_sidebar_state="collapsed")\n'
    'st.markdown('+repr(CSS)+', unsafe_allow_html=True)\n'
    'st.html('+repr(NAV_JS)+', unsafe_allow_javascript=True)\n'
    'def navegar(page): st.session_state["pagina_atual"]=page\n'
    'with st.sidebar:\n'
    '    st.markdown(\'<div class="sidebar-brand"><div class="sidebar-brand-title">MRP</div>'
    '<div class="sidebar-brand-sub">Planejamento de Materiais SETTA</div></div>\', '
    'unsafe_allow_html=True)\n'
    '    st.markdown(\'<div class="sidebar-section-label">NAVEGAÇÃO</div>\', '
    'unsafe_allow_html=True)\n'
    '    st.button("MRP ATUAL", key="mrp_nav_btn_0", type="primary", use_container_width=True, on_click=navegar, args=("MRP ATUAL",))\n'
    '    st.button("SOLICITAÇÕES AVULSAS", key="mrp_nav_btn_1", use_container_width=True, on_click=navegar, args=("SOLICITAÇÕES AVULSAS",))\n'
    '    st.button("CONFIGURAÇÕES", key="mrp_nav_btn_2", use_container_width=True, on_click=navegar, args=("CONFIGURAÇÕES",))\n'
    '    st.markdown(\'<div class="sidebar-divider"></div><div class="sidebar-status-card">'
    'RELATÓRIO MRP</div>\', unsafe_allow_html=True)\n'
    'st.markdown(\'<div class="setta-logo-card">Setta</div>\', unsafe_allow_html=True)\n'
    'st.title("MRP | SETTA — TESTE VISUAL")\n'
    'st.markdown(\'<div class="section-band"><div class="section-band-title">INDICADORES DO MRP</div></div>\',unsafe_allow_html=True)\n'
    'cards=st.columns(3)\n'
    'for pos,col in enumerate(cards):\n'
    '    with col:\n'
    '        st.markdown(\'<div class="mrp-source-card" style="min-height:100px">DEMANDAS NO MRP</div>\',unsafe_allow_html=True)\n'
    'st.write("Corpo do relatório MRP")\n'
    'st.write("Página atual: "+st.session_state.get("pagina_atual","MRP ATUAL"))\n'
)

SELECTORS = (
    '[data-testid="stSidebarCollapsedControl"]',
    '[data-testid="collapsedControl"]',
    '[data-testid="stExpandSidebarButton"]',
)

def wait_online():
    for _ in range(90):
        try:
            with urllib.request.urlopen(URL, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(.7)
    raise AssertionError("Aplicativo Streamlit de teste não iniciou.")

def button(page):
    for sel in SELECTORS:
        node=page.locator(sel)
        if node.count()==0:
            continue
        locator=node.first.locator("button")
        target=locator.first if locator.count() else node.first
        if target.is_visible():
            return target
    ids=page.locator("[data-testid]").evaluate_all(
        "(nodes)=>[...new Set(nodes.map(n=>n.dataset.testid))].slice(0,120)"
    )
    raise AssertionError("Controle nativo de expandir sidebar não visível: "+str(ids))

def check(browser,width,height,name,mobile_iphone=False):
    # WebKit desktop reduzido não equivale ao Safari do iPhone:
    # viewport móvel, toque, DPR e User-Agent mudam o layout do Streamlit.
    opts={"viewport":{"width":width,"height":height},
          "device_scale_factor":3 if mobile_iphone else 1}
    if mobile_iphone:
        opts.update({
            "is_mobile":True,
            "has_touch":True,
            "user_agent":(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        })
    context=browser.new_context(**opts)
    page=context.new_page()
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=30000)
        page.get_by_text("MRP | SETTA — TESTE VISUAL").wait_for(timeout=35000)
        page.wait_for_timeout(500)
        diagnostics=page.evaluate("""() => {
          const logo=document.querySelector('.setta-logo-card');
          const rect=logo?.getBoundingClientRect();
          const frames=[...document.querySelectorAll('iframe')].map(el=>({
            h:Math.round(el.getBoundingClientRect().height),
            y:Math.round(el.getBoundingClientRect().top),
            outer:el.outerHTML.slice(0,300)
          }));
          const block=[...document.querySelectorAll('[data-testid="stElementContainer"]')]
            .slice(0,7).map(el=>({
              h:Math.round(el.getBoundingClientRect().height),
              y:Math.round(el.getBoundingClientRect().top),
              text:(el.innerText||"").slice(0,45),
              html:el.outerHTML.slice(0,140)
            }));
          const main=document.querySelector('[data-testid="stMain"]');
          const mr=main?.getBoundingClientRect();
          const band=document.querySelector('.section-band')?.getBoundingClientRect();
          const cardRects=[...document.querySelectorAll('.mrp-source-card')].map(x=>{
            const r=x.getBoundingClientRect();return {x:Math.round(r.x),w:Math.round(r.width),
              right:Math.round(r.right)};
          });
          return {
            bandX:Math.round(band?.x||0),bandW:Math.round(band?.width||0),
            cardRects,
            logoY:Math.round(rect?.y||0),
            logoX:Math.round(rect?.x||0),
            logoW:Math.round(rect?.width||0),
            mainX:Math.round(mr?.x||0),
            mainW:Math.round(mr?.width||0),
            scrollW:document.documentElement.scrollWidth,
            frames,block,innerWidth:window.innerWidth
          };
        }""")
        print(f"LAYOUT_DIAGNOSTICO {name}: {diagnostics}",flush=True)
        if width<=430:
            assert diagnostics["logoY"]<205, (
                "O cabeçalho SETTA ficou afastado do topo no celular",diagnostics)
            assert diagnostics["mainX"]<24, (
                "Sidebar colapsada deslocou o MRP para a direita",diagnostics)
            assert diagnostics["logoX"]<35, (
                "Logo fora da area util do celular",diagnostics)
            assert diagnostics["logoW"]>=width-55, (
                "MRP perdeu largura para a sidebar colapsada",diagnostics)
            assert diagnostics["bandX"]>=8 and diagnostics["bandX"]<36, (
                "Seção visual cortada na esquerda",diagnostics)
            assert diagnostics["bandW"]>=width-58, (
                "Seção visual comprimida",diagnostics)
            assert len(diagnostics["cardRects"])==3
            for rect in diagnostics["cardRects"]:
                assert 8<=rect["x"]<=36 and rect["w"]>=width-60, (
                    "Cartão deslocado ou cortado no mobile",rect,diagnostics)
                assert rect["right"]<=width+4,rect
            assert diagnostics["mainW"]>=width-25, (
                "Conteudo principal comprimido no Safari",diagnostics)
            assert diagnostics["scrollW"]<=width+6, (
                "Rolagem horizontal indevida no celular",diagnostics)
        page.screenshot(path=str(ARTIFACTS/f"{name}-fechado.png"),full_page=True)
        toggle=button(page)
        rect=toggle.bounding_box()
        assert rect and rect["x"]>=-4 and rect["width"]>=20, rect
        toggle.click(timeout=8000)
        page.get_by_role("button",name="MRP ATUAL").wait_for(state="visible",timeout=10000)
        # O Streamlit anima a sidebar com translateX: aguardar o fim
        # da transição, e não registrar o frame intermediário como defeito.
        page.wait_for_timeout(700)
        page.screenshot(path=str(ARTIFACTS/f"{name}-aberto.png"),full_page=True)
        assert page.get_by_role("button",name="SOLICITAÇÕES AVULSAS").is_visible()
        if width<=430:
            open_main=page.locator('[data-testid="stMain"]').bounding_box()
            assert open_main and open_main["x"]<24 and open_main["width"]>=width-25, (
                "Abrir menu deslocou ou comprimiu o MRP",open_main
            )
        nav_box=page.get_by_role("button",name="MRP ATUAL").bounding_box()
        assert nav_box and nav_box["width"]>=190,nav_box
        # O painel de controle deve permanecer na viewport, sem cortes laterais.
        sidebar=page.locator('section[data-testid="stSidebar"]')
        bound=sidebar.bounding_box()
        assert bound and bound["width"]>160 and bound["x"]>=-6,bound
        assert bound["x"]+bound["width"]<=width+12,bound
        # Navegação pelo botão próprio deve fechar o menu nativo automaticamente,
        # sem escondê-lo via CSS e sem perder o botão de reabrir.
        page.get_by_role("button",name="CONFIGURAÇÕES").click(timeout=8000)
        page.get_by_text("Página atual: CONFIGURAÇÕES").wait_for(state="visible",timeout=12000)
        page.wait_for_timeout(700)
        close_state=page.locator('section[data-testid="stSidebar"]').bounding_box()
        collapsed_button=button(page)
        collapsed_rect=collapsed_button.bounding_box()
        assert collapsed_rect and collapsed_rect["width"]>=20,collapsed_rect
        assert close_state is None or close_state["x"]+close_state["width"]<40,(
            "Sidebar ainda aberta após selecionar aba",close_state,
            page.locator('section[data-testid="stSidebar"] button').evaluate_all(
                "(nodes)=>nodes.map(b=>({aria:b.ariaLabel,html:b.outerHTML.slice(0,400)}))"
            ),
        )
        page.screenshot(path=str(ARTIFACTS/f"{name}-navegacao-fechou.png"),full_page=True)
        collapsed_button.click(timeout=8000)
        page.get_by_role("button",name="SOLICITAÇÕES AVULSAS").wait_for(state="visible",timeout=10000)
        page.wait_for_timeout(700)
        page.screenshot(path=str(ARTIFACTS/f"{name}-reaberto.png"),full_page=True)
        print(f"{name}: botão, layout, navegação, fechamento e reabertura OK")
    except Exception:
        page.screenshot(path=str(ARTIFACTS/f"{name}-ERRO.png"),full_page=True)
        raise
    finally:
        context.close()

def main():
    executable=next((p for cmd in ["google-chrome","google-chrome-stable","chromium","chromium-browser"]
                    if (p:=shutil.which(cmd))),None)
    if not executable:
        raise RuntimeError("Chrome/Chromium ausente no runner visual.")
    with tempfile.TemporaryDirectory() as folder:
        app=Path(folder)/"sidebar_app.py"
        app.write_text(APP,encoding="utf-8")
        server=subprocess.Popen(
            ["streamlit","run",str(app),"--server.headless=true",
             "--server.port=8515","--browser.gatherUsageStats=false"],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        )
        try:
            wait_online()
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(
                    executable_path=executable,headless=True,
                    args=["--no-sandbox","--disable-dev-shm-usage"],
                )
                try:
                    check(browser,1440,900,"desktop-1440")
                    check(browser,390,844,"mobile-390")
                    check(browser,414,896,"iphone-414")
                finally:
                    browser.close()
                # WebKit e o motor do Safari: o bug de espaco em branco
                # nao apareceu no Chromium, portanto validar tambem nele.
                safari=playwright.webkit.launch(headless=True)
                try:
                    check(safari,390,844,"safari-390",mobile_iphone=True)
                    check(safari,414,896,"safari-414",mobile_iphone=True)
                finally:
                    safari.close()
        finally:
            server.terminate()
            try:
                server.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                server.kill()
                server.communicate()

if __name__=="__main__":
    main()
