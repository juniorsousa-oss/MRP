"""Exercita a view real dos 3 perfis com respostas sintéticas e sem escrita nem rede externa."""
import ast
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

from mrp_engine_extract import montar_fonte_atual

SOURCE = montar_fonte_atual()
VIEW = ast.get_source_segment(SOURCE, next(n for n in ast.parse(SOURCE).body
    if isinstance(n,ast.FunctionDef) and n.name == "_mrp_avulsas_view"))
APP = """
import pandas as pd
import streamlit as st
from mrp_avulsas_validacao import identificacao_valida
st.set_page_config(layout="wide")
perfil_fixture=st.query_params.get("perfil","ADMIN")
def _mrp_avulsas_call(action,payload=None):
    assert action=="list", "A fixture nunca permite escrita"
    states=("PENDENTE","SEPARADA","ENTREGUE","ENTREGUE","RECUSADA")
    requests=[{"id":str(i),"numero":40+i,"estado":state,"finalidade":"TRANSFERENCIA",
              "criado_em":"2026-11-25T15:00:00Z","entregue_em":"2026-11-25T16:00:00Z",
              "solicitante":"Pessoa Exemplo","destino":"ASTEC"}
              for i,state in enumerate(states,1)]
    if perfil_fixture=="CONSULTA":
        requests=requests[:1]
    rows=[{"id":int(p["id"]),"pedido_id":p["id"],"status":"ABERTA",
            "codigo":"00000042","descricao":"Cabo de teste","quantidade":1}
            for p in requests]
    return {"role":perfil_fixture,"pedidos":requests,"rows":rows,"snapshot_id":"42",
            "conferencias_finais":[{"pedido_id":"4","procedimento":"TRANSFERENCIA",
                                   "documento_referencia":"DOC-FICTICIO"}]}
def excel_bytes(_):return b"fake"
"""+VIEW+"\n_mrp_avulsas_view()\n"


def check(browser, url, width, role):
    with browser.new_context(viewport={"width":width,"height":850}) as context:
        p=context.new_page()
        p.goto(url+f"/?perfil={role}",wait_until="domcontentloaded")
        expect(p.get_by_text(f"Almoxarifado · Perfil {role}")).to_be_visible()
        expect(p.get_by_role("button",name="Detalhar SA-000041")).to_be_visible()
        assert p.evaluate("document.documentElement.scrollWidth") <= width+2
        if role=="CONSULTA":
            expect(p.get_by_role("button",name="Detalhar SA-000042")).to_have_count(0)
            p.get_by_text("NOVA SOLICITAÇÃO",exact=True).click()
            expect(p.get_by_text("Selecionar materiais",exact=True)).to_be_visible()
            p.get_by_text("MINHAS SOLICITAÇÕES",exact=True).click()
        busca=p.get_by_role("textbox",name="Buscar por número da S.A.",exact=True)
        busca.fill("000041")
        busca.press("Enter")
        expect(p.get_by_text("1 solicitação · Página 1 de 1")).to_be_visible()
        p.get_by_role("button",name="Detalhar SA-000041").click()
        expect(p.get_by_role("heading",name="SA-000041",exact=True)).to_be_visible()
        sep=p.get_by_role("button",name="CONFIRMAR MATERIAL SEPARADO")
        if role=="OPERADOR":
            expect(sep).to_be_visible()
            expect(p.get_by_role("button",name="RECUSAR SOLICITAÇÃO")).to_be_visible()
        else:
            expect(sep).to_have_count(0)
        p.get_by_role("button",name="Voltar à fila").click()
        expect(busca).to_have_value("000041")
        if role=="ADMIN":
            p.get_by_text("CONFERÊNCIA FINAL",exact=True).click()
            p.get_by_role("button",name="Detalhar SA-000043").click()
            expect(p.get_by_role("button",name="CONFIRMAR ENCERRAMENTO ADMINISTRATIVO")).to_be_visible()
            p.get_by_role("tab",name="CONCLUÍDAS (1)",exact=True).click()
            p.get_by_role("button",name="Detalhar SA-000044").click()
            expect(p.get_by_text("DOC-FICTICIO",exact=True)).to_be_visible()
        print(f"{role} {width}px: fila, detalhe e permissões OK",flush=True)


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port=sock.getsockname()[1]
    url=f"http://127.0.0.1:{port}"
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as work, tempfile.TemporaryFile() as logs:
        app=Path(work)/"app.py"
        app.write_text(f'import sys\nsys.path.insert(0,{str(root)!r})\n'+APP)
        server=subprocess.Popen([sys.executable,"-m","streamlit","run",str(app),"--server.headless=true",
                                 "--server.address=127.0.0.1",f"--server.port={port}","--browser.gatherUsageStats=false"],
                                stdout=logs,stderr=logs)
        try:
            for _ in range(80):
                try:
                    with urlopen(url,timeout=2):break
                except OSError:time.sleep(.25)
            else:raise RuntimeError("App de teste não iniciou.")
            with sync_playwright() as pw:
                chrome=os.environ.get("MRP_CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
                b=pw.chromium.launch(executable_path=chrome,args=["--no-sandbox","--disable-dev-shm-usage"])
                try:
                    for w in (1363,390):
                        for role in ("ADMIN","OPERADOR","CONSULTA"):
                            check(b,url,w,role)
                finally:b.close()
        except Exception:
            logs.seek(0)
            print(logs.read().decode(),flush=True)
            raise
        finally:
            server.terminate()
            server.wait(timeout=10)

if __name__=="__main__":
    main()
