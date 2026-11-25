"""Valida menu e rolagem em Streamlit 1.55 com dados fictícios."""
from __future__ import annotations

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
from mrp_interface_visual import WORKSPACE_CSS
from mrp_workspace import WORKSPACE_V2_CSS, workspace_header

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8515"
ARTIFACTS = ROOT / "artifacts" / "sidebar-browser"
SOURCE = montar_fonte_atual()
INITIAL_SIDEBAR = next(
    ast.literal_eval(k.value) for call in ast.walk(ast.parse(SOURCE))
    if isinstance(call, ast.Call) and ast.unparse(call.func) == "st.set_page_config"
    for k in call.keywords if k.arg == "initial_sidebar_state"
)
# Reusar chamadas montadas pelo app, inclusive a escolha st.html vs st.markdown.
BOOTSTRAP = "\n".join(
    ast.get_source_segment(SOURCE, n) for n in ast.parse(SOURCE).body
    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
    and isinstance(n.value.args[0] if n.value.args else None, ast.Constant)
    and any(marker in str(n.value.args[0].value) for marker in (
        "--setta-outer", "__settaMenuCloseOnNavV1"
    ))
)
assert BOOTSTRAP.count("\nst.") == 1, "Esperado CSS e script de navegação do shell."
SIDEBAR = next(
    ast.get_source_segment(SOURCE, n)
    for n in ast.parse(SOURCE).body if isinstance(n, ast.With)
    and any(ast.unparse(i.context_expr) == "st.sidebar" for i in n.items)
)
HEADERS = {
    page: workspace_header(page, "", "ATUALIZADO", "25/11/2026 08:00", semana="2026-47", bases=(5,5), registros="", alertas=[], nome="Almoxarifado", perfil="ADMIN")
    for page in ("MRP ATUAL", "SOLICITAÇÕES AVULSAS", "CONFIGURAÇÕES")
}
APP = f"""
import streamlit as st
from mrp_workspace import workspace_sidebar
st.set_page_config(layout="wide", initial_sidebar_state={INITIAL_SIDEBAR!r})
if not st.session_state.get("logged_in"):
    st.html('<div class="setta-login-wrap"></div>')
    if st.button("Entrar em teste"):
        st.session_state.logged_in=True
        st.session_state.pop("page", None)
        st.rerun()
    st.stop()
{BOOTSTRAP}
st.html({WORKSPACE_CSS!r})
st.html({WORKSPACE_V2_CSS!r})
_mrp_pages=("MRP ATUAL","SOLICITAÇÕES AVULSAS","CONFIGURAÇÕES")
st.session_state.update(auth_nome="Almoxarifado", auth_role="ADMIN", auth_email="conta@example.invalid")
_mrp_page=st.session_state.get("page", _mrp_pages[0])
def _mrp_set_sidebar_page(page): st.session_state.page=page
def _logout():
    st.session_state.logged_in=False
    st.rerun()
st.html({HEADERS!r}[_mrp_page])
{SIDEBAR}
st.write("Página atual: " + _mrp_page)
if _mrp_page == _mrp_pages[0]:
    cards=st.columns(3)
    for col in cards:
        col.markdown('<div class="mrp-source-card" style="min-height:100px">DEMANDAS NO MRP</div>',unsafe_allow_html=True)
    st.html('<div style="height:1100px">Área longa de teste</div>')
st.button("Último controle útil")
"""


def wait_online():
    for _ in range(90):
        try:
            with urllib.request.urlopen(URL, timeout=2) as resp:
                if resp.status == 200:
                    return
        except OSError:
            time.sleep(.5)
    raise AssertionError("Aplicativo Streamlit de teste não iniciou.")


def assert_scroll(page, width, long):
    last = page.get_by_role("button", name="Último controle útil")
    main = page.get_by_test_id("stMain")
    dimensions = main.evaluate("""main => {
      const doc = main.ownerDocument;
      const sidebar = doc.querySelector('[data-testid="stSidebar"]');
      const rect = main.getBoundingClientRect();
      return {h:innerHeight, docH:doc.documentElement.scrollHeight,
        hMain:main.clientHeight, scrollH:main.scrollHeight,
        sidebarH:sidebar.clientHeight, mainX:rect.x, mainW:rect.width,
        docW:doc.documentElement.scrollWidth};
    }""")
    assert dimensions["docH"] <= dimensions["h"]+2, dimensions
    assert dimensions["sidebarH"] <= dimensions["h"]+2, dimensions
    assert dimensions["docW"] <= width+3, dimensions
    if width<=900:
        assert dimensions["mainX"]<24 and dimensions["mainW"]>=width-25, dimensions
    if long:
        assert dimensions["scrollH"]>dimensions["hMain"]+100, dimensions
        main.evaluate("el => el.scrollTop = el.scrollHeight")
        expect(last).to_be_in_viewport()
        distance = last.evaluate("""last =>
          last.closest('[data-testid="stMain"]').getBoundingClientRect().bottom
          - last.getBoundingClientRect().bottom""")
        # Até 32 px de respiro no tema (mais arredondamento do navegador).
        assert -1 <= distance <= 36, distance
        main.evaluate("el => el.scrollTop = 0")
    else:
        assert dimensions["scrollH"]<=dimensions["hMain"]+2, dimensions
        expect(last).to_be_in_viewport()


def assert_header(page):
    top = page.locator(".mrp-v2-top")
    assert abs(top.bounding_box()["y"]) <= 1, "Faixa acima do cabeçalho"
    assert top.evaluate("el => getComputedStyle(el).borderBottomWidth") == "0px"


def assert_menu_button(page, control, *, opening):
    expect(control).to_be_in_viewport(ratio=1)
    rect = control.bounding_box()
    assert 43 <= rect["width"] <= 45 and 43 <= rect["height"] <= 45, rect
    if opening:
        logo = page.locator(".mrp-v2-mark").bounding_box()
        assert rect["x"] + rect["width"] + 6 <= logo["x"], (rect, logo)
        assert abs(rect["y"] + rect["height"]/2 - (logo["y"] + logo["height"]/2)) <= 2


def check(browser,width,height,name,iphone=False):
    opts={"viewport":{"width":width,"height":height}}
    if iphone:
        opts.update(is_mobile=True,has_touch=True,device_scale_factor=3,
                    user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"))
    with browser.new_context(**opts) as context:
        page=context.new_page()
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=30000)
            login=page.get_by_role("button",name="Entrar em teste")
            login.click(timeout=15000)
            expect(page.get_by_role("heading",name="Demanda Geral",exact=True)).to_be_visible(timeout=15000)
            expect(page.locator(".mrp-v2-stamps:visible, .mrp-v2-mobile-date:visible")).to_be_visible()
            expect(page.get_by_text("Bases 5/5")).to_be_visible()
            menu=page.get_by_role("button",name="Abrir menu lateral")
            collapse=page.get_by_role("button",name="Recolher menu lateral")
            settings=page.get_by_role("button",name="Configurações",exact=True)
            sidebar=page.get_by_test_id("stSidebar")
            assert_header(page)
            expect(sidebar).to_have_attribute("aria-expanded", "false")
            for index in range(3):
                expect(sidebar).to_have_attribute("aria-expanded", "false")
                assert_menu_button(page, menu, opening=True)
                if index == 0:
                    menu.press("Enter")
                else:
                    menu.click()
                expect(sidebar).to_have_attribute("aria-expanded", "true")
                assert_menu_button(page, collapse, opening=False)
                assert_header(page)
                if index < 2:
                    collapse.click()
            expect(settings).to_be_in_viewport()
            assert_scroll(page,width,long=True)
            page.screenshot(path=str(ARTIFACTS/f"{name}-aberto.png"))
            settings.click()
            expect(page.get_by_role("heading",name="Configurações",exact=True)).to_be_visible()
            assert_header(page)
            if width<=900:
                expect(sidebar).to_have_attribute("aria-expanded", "false")
                assert_menu_button(page, menu, opening=True)
                menu.click()
            else:
                expect(settings).to_be_in_viewport()
                collapse.click()
                expect(menu).to_be_in_viewport()
                menu.click()
            expect(settings).to_have_attribute("data-testid","stBaseButton-primary")
            assert_scroll(page,width,long=False)
            expect(page.get_by_text("conta@example.invalid")).not_to_be_visible()
            account=page.get_by_role("button",name="Almoxarifado · Admin")
            expect(account).to_be_in_viewport()
            account.click()
            expect(page.get_by_text("conta@example.invalid")).to_be_visible()
            page.get_by_role("button",name="Sair",exact=True).click()
            expect(login).to_be_visible()
            login.click()
            expect(page.get_by_role("heading",name="Demanda Geral",exact=True)).to_be_visible()
            expect(sidebar).to_have_attribute("aria-expanded", "false")
            assert_menu_button(page, menu, opening=True)
            menu.click()
            expect(sidebar).to_have_attribute("aria-expanded", "true")
            print(f"{name}: sidebar, conta, navegação, rolagem e logout OK",flush=True)
        except Exception:
            page.screenshot(path=str(ARTIFACTS/f"{name}-ERRO.png"))
            raise


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    chrome=os.environ.get("MRP_CHROME") or next((p for cmd in ("google-chrome","google-chrome-stable","chromium","chromium-browser")
                 if (p:=shutil.which(cmd))),None)
    assert chrome, "Chrome/Chromium ausente."
    with tempfile.TemporaryDirectory() as folder:
        app=Path(folder)/"sidebar_app.py"
        app.write_text(f"import sys\nsys.path.insert(0, {str(ROOT)!r})\n"+APP,encoding="utf-8")
        server=subprocess.Popen(
            [sys.executable,"-m","streamlit","run",str(app),"--server.headless=true",
             "--server.port=8515","--browser.gatherUsageStats=false"],
            stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        try:
            wait_online()
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(
                    executable_path=chrome,args=["--no-sandbox","--disable-dev-shm-usage"])
                try:
                    check(browser,1440,900,"desktop-1440")
                    check(browser,850,800,"tablet-850")
                    check(browser,390,844,"mobile-390")
                    check(browser,414,896,"mobile-414")
                finally:
                    browser.close()
                if not os.environ.get("MRP_SKIP_WEBKIT"):
                    safari=playwright.webkit.launch()
                    try:
                        check(safari,390,844,"safari-390",iphone=True)
                        check(safari,414,896,"safari-414",iphone=True)
                    finally:
                        safari.close()
        finally:
            server.terminate()
            server.wait(timeout=8)


if __name__=="__main__":
    main()
