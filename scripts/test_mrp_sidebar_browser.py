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
URL = "http://127.0.0.1:8515"
ARTIFACTS = ROOT / "artifacts" / "sidebar-browser"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

APP = (
    'import streamlit as st\n'
    'st.set_page_config(layout="wide", initial_sidebar_state="collapsed")\n'
    'st.markdown('+repr(CSS)+', unsafe_allow_html=True)\n'
    'with st.sidebar:\n'
    '    st.markdown(\'<div class="sidebar-brand"><div class="sidebar-brand-title">MRP</div>'
    '<div class="sidebar-brand-sub">Planejamento de Materiais SETTA</div></div>\', '
    'unsafe_allow_html=True)\n'
    '    st.markdown(\'<div class="sidebar-section-label">NAVEGAÇÃO</div>\', '
    'unsafe_allow_html=True)\n'
    '    st.button("MRP ATUAL", key="mrp_nav_btn_0", type="primary")\n'
    '    st.button("SOLICITAÇÕES AVULSAS", key="mrp_nav_btn_1")\n'
    '    st.markdown(\'<div class="sidebar-divider"></div><div class="sidebar-status-card">'
    'RELATÓRIO MRP</div>\', unsafe_allow_html=True)\n'
    'st.markdown(\'<div class="setta-logo-card">Setta</div>\', unsafe_allow_html=True)\n'
    'st.title("MRP | SETTA — TESTE VISUAL")\n'
    'st.write("Corpo do relatório MRP")\n'
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

def check(browser,width,height,name):
    page=browser.new_page(viewport={"width":width,"height":height},
                          device_scale_factor=1)
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=30000)
        page.get_by_text("MRP | SETTA — TESTE VISUAL").wait_for(timeout=35000)
        page.screenshot(path=str(ARTIFACTS/f"{name}-fechado.png"),full_page=True)
        toggle=button(page)
        rect=toggle.bounding_box()
        assert rect and rect["x"]>=-4 and rect["width"]>=20, rect
        toggle.click(timeout=8000)
        page.get_by_role("button",name="MRP ATUAL").wait_for(state="visible",timeout=10000)
        page.screenshot(path=str(ARTIFACTS/f"{name}-aberto.png"),full_page=True)
        assert page.get_by_role("button",name="SOLICITAÇÕES AVULSAS").is_visible()
        # O painel de controle deve permanecer na viewport, sem cortes laterais.
        sidebar=page.locator('section[data-testid="stSidebar"]')
        bound=sidebar.bounding_box()
        assert bound and bound["width"]>160 and bound["x"]>=-6,bound
        assert bound["x"]+bound["width"]<=width+12,bound
        print(f"{name}: botão visível, clique funcional, opções e layout OK")
    except Exception:
        page.screenshot(path=str(ARTIFACTS/f"{name}-ERRO.png"),full_page=True)
        raise
    finally:
        page.close()

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
                finally:
                    browser.close()
        finally:
            server.terminate()
            try:
                server.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                server.kill()
                server.communicate()

if __name__=="__main__":
    main()
