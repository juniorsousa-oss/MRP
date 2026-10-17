"""Diagnóstico visual somente leitura da página pública do MRP no WebKit Safari iOS.
Sem interação com sessões, login, formulários ou operações de dados.
"""
from __future__ import annotations
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts"/"live-mobile"
OUT.mkdir(parents=True,exist_ok=True)
URL="https://mrpsetta.streamlit.app/"
JS="""() => {
const selectors={
  root:'#root',app:'.stApp',view:'[data-testid="stAppViewContainer"]',
  main:'[data-testid="stMain"]',block:'[data-testid="stMainBlockContainer"]',
  sidebar:'section[data-testid="stSidebar"]',collapse:'[data-testid="stSidebarCollapsedControl"]',
  logo:'.setta-logo-card',title:'.app-title',band:'.section-band',
  header:'[data-testid="stHeader"]'
};
const records={};
for(const [name,selector] of Object.entries(selectors)){
 const el=document.querySelector(selector);if(!el){records[name]=null;continue}
 const rect=el.getBoundingClientRect(),style=getComputedStyle(el);
 records[name]={x:+rect.x.toFixed(1),y:+rect.y.toFixed(1),w:+rect.width.toFixed(1),
 h:+rect.height.toFixed(1),display:style.display,position:style.position,
 transform:style.transform,marginL:style.marginLeft,paddingL:style.paddingLeft,
 flexBasis:style.flexBasis,overflowX:style.overflowX,
 class:el.className?.toString().slice(0,120)};
}
return {viewport:{innerW:innerWidth,visualW:visualViewport?.width,
 documentW:document.documentElement.scrollWidth,scrollX, dpr:devicePixelRatio},
 location:location.href,title:document.title,records,
 labels:[...document.querySelectorAll('h1,h2')].slice(0,8).map(x=>x.innerText)};
}"""
with sync_playwright() as p:
    browser=p.webkit.launch(headless=True)
    try:
        for width,height,name in [(390,844,"safari-390"),(428,926,"safari-428")]:
            context=browser.new_context(
                viewport={"width":width,"height":height},
                device_scale_factor=3,is_mobile=True,has_touch=True,
                user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 "
                 "Mobile/15E148 Safari/604.1"),
            )
            page=context.new_page()
            try:
                page.goto(URL,wait_until="domcontentloaded",timeout=50000)
                page.wait_for_timeout(10000)
                print("LIVE_DIAGNOSTIC "+name+" "+json.dumps(page.evaluate(JS),ensure_ascii=False),flush=True)
                page.screenshot(path=str(OUT/(name+".png")),full_page=False)
            except Exception as err:
                print("LIVE_ERROR "+name+" "+repr(err),flush=True)
                page.screenshot(path=str(OUT/(name+"-error.png")),full_page=False)
            finally:
                context.close()
    finally:
        browser.close()
