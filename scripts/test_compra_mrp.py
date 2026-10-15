"""Testes das regras de compra do MRP sem abrir o Streamlit."""
from __future__ import annotations

import ast
import io
import runpy
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from types import SimpleNamespace
from datetime import date, timedelta

import pandas as pd

# Reconstrói a fonte final com os patches e extrai somente funções puras.
source = runpy.run_path("scripts/validate_generated_mrp.py")["final"]
tree = ast.parse(source)
names = {
    "normalizar_compra_mrp",
    "formatar_data_br",
    "_compra_codigo",
    "_preparar_compra_prioridades",
    "_compra_excel_protheus",
    "excel_bytes",
    "_compra_abrir",
    "_compra_fechar",
}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names, "Funções de compra ausentes no código gerado"
# Isola as regras puras de compra sem invocar decorators de Streamlit.
for node in nodes:
    node.decorator_list = []
namespace = {"pd": pd, "date": date, "st": SimpleNamespace(session_state={}), "BytesIO":io.BytesIO}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "mrp_compra_puro.py", "exec"), namespace)
calcular = namespace["_preparar_compra_prioridades"]

hoje = date.today()
base = pd.DataFrame([
    {"produto": 140027, "qnt": 2, "data": (hoje + timedelta(days=10)).strftime("%d/%m/%Y"), "psy": "", "cc": "600307", "op": "", "obs": "MRP", "prioridade": ""},
    {"produto": "00041212", "qnt": 3, "data": (hoje + timedelta(days=10)).strftime("%d/%m/%Y"), "psy": "", "cc": "600307", "op": "", "obs": "MRP", "prioridade": ""},
    {"produto": "00800081", "qnt": 1, "data": (hoje + timedelta(days=20)).strftime("%d/%m/%Y"), "psy": "", "cc": "600307", "op": "", "obs": "MRP", "prioridade": ""},
])
cad = pd.DataFrame([
    {"Código": 140027, "Lead Time (dias)": 20},
    {"Código": 41212, "Lead Time (dias)": 0},
    {"Código": 800081, "Lead Time (dias)": 20},
])
result = calcular(base, cad)
assert result["prioridade"].tolist() == ["2", "1", "1"], result["prioridade"].tolist()
assert set(result["prj"]) == {""}
assert result["produto"].tolist() == ["00140027", "00041212", "00800081"]

# A tela de validacao e carregada somente com o quarto botao e fica fechada
# por padrao, tanto no painel administrativo como na consulta.
for perfil in ("admin", "consulta"):
    state = namespace["st"].session_state
    assert state.get(f"{perfil}_compra_aberta", False) is False
    namespace["_compra_abrir"](perfil)
    assert state[f"{perfil}_compra_aberta"] is True
    state[f"{perfil}_compra_confirmada"] = "aprovacao-anterior"
    namespace["_compra_fechar"](perfil)
    assert state[f"{perfil}_compra_aberta"] is False
    assert f"{perfil}_compra_confirmada" not in state
    namespace["_compra_abrir"](perfil)
    assert state[f"{perfil}_compra_aberta"] is True
    assert f"{perfil}_compra_confirmada" not in state

def possui_validacao_condicional(perfil):
    chave = f"{perfil}_compra_aberta"
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or chave not in ast.unparse(node.test):
            continue
        if any(
            isinstance(chamado, ast.Call)
            and isinstance(chamado.func, ast.Name)
            and chamado.func.id == "render_validacao_compra_mrp"
            for comando in node.body
            for chamado in ast.walk(comando)
        ):
            return True
    return False

assert possui_validacao_condicional("admin")
assert possui_validacao_condicional("consulta")
assert source.count('ANÁLISE DE COMPRA') >= 2
assert "FINALIZAR ANÁLISE DE COMPRA" in source
assert "col_confirmar,col_excel,col_finalizar" in source
assert 'st.download_button(\n                "BAIXAR COMPRA MRP — EXCEL"' in source
assert 'key=f"{prefixo}_compra_csv"' not in source

# Regra STSUP25: A:K; prioridade em J e C preenchida como TEXTO.
# Regressao da conversao 04/12/2026 -> 12/4/2026 observada no Protheus.
amostra=result.copy()
amostra.at[0,"data"]="04/12/2026"
amostra.at[1,"data"]="25/11/2026"
excel_binario=namespace["_compra_excel_protheus"](amostra)
with ZipFile(io.BytesIO(excel_binario)) as zip_excel:
    ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    folha=ET.fromstring(zip_excel.read("xl/worksheets/sheet1.xml"))
    estilos=ET.fromstring(zip_excel.read("xl/styles.xml"))
    dimensao=folha.find("m:dimension",ns)
    assert dimensao is not None and dimensao.get("ref")==f"A1:K{len(amostra)+1}"
    linhas=folha.findall("./m:sheetData/m:row",ns)
    assert len(linhas)==len(amostra)+1

    for linha in linhas:
        referencias=[c.attrib.get("r") for c in linha.findall("m:c",ns)]
        assert referencias==[f"{col}{linha.attrib['r']}" for col in "ABCDEFGHIJK"], referencias

    # Openpyxl pode gravar inlineStr sem arquivo sharedStrings.
    strings=[]
    if "xl/sharedStrings.xml" in zip_excel.namelist():
        shared=ET.fromstring(zip_excel.read("xl/sharedStrings.xml"))
        strings=["".join(t.itertext()) for t in shared.findall("m:si",ns)]
    def conteudo(celula):
        if celula.get("t")=="s":
            return strings[int(celula.find("m:v",ns).text)]
        if celula.get("t")=="inlineStr":
            return "".join(celula.find("m:is",ns).itertext())
        v=celula.find("m:v",ns)
        return "" if v is None else v.text

    header={c.get("r"):conteudo(c) for c in linhas[0].findall("m:c",ns)}
    assert [header[f"{col}1"] for col in "ABCDEFGHIJK"] == [
        "produto","qnt","data","psy","cc","op","obs","","vunit","prioridade","justificativa"
    ], header

    cell_xfs=estilos.find("m:cellXfs",ns)
    assert cell_xfs is not None
    for idx,esperado in ((2,"04/12/2026"),(3,"25/11/2026")):
        celulas={c.attrib["r"]:c for c in linhas[idx-1].findall("m:c",ns)}
        c=celulas[f"C{idx}"]
        assert c.get("t")=="inlineStr",c.attrib
        assert conteudo(c)==esperado,(conteudo(c),esperado)
        assert cell_xfs[int(c.get("s"))].attrib["numFmtId"]=="49",c.attrib
        assert conteudo(celulas[f"J{idx}"]) in {"1","2"}
        assert conteudo(celulas[f"I{idx}"])==""
        assert conteudo(celulas[f"K{idx}"])==""
    # Formato da data sera replicado literalmente na conversao da tabela
    # para CSV, nao havendo valor serial (46360) nem 12/4/2026.

# TC/TP: compras da mesma data e mesmo material viram uma unica SC.
# Mantem OPs na observacao e campo OP vazio para o STSUP25.
tc_def=next(
    (node for node in ast.walk(tree)
     if isinstance(node,ast.FunctionDef) and node.name=="_consolidar_compras_tctp"),
    None,
)
assert tc_def is not None, "Consolidacao de TC/TP nao inserida no MRP"
tc_def.decorator_list=[]
exec(compile(ast.Module(body=[tc_def],type_ignores=[]),"mrp_compra_tctp.py","exec"),namespace)
agrupar_tc=namespace["_consolidar_compras_tctp"]
assert "_consolidar_compras_tctp(_tc_compras)" in source
tc_exemplos=[
    {"produto":80098,"qnt":2,"data":"06/11/2026","psy":"","cc":"600307","op":"26031401001","obs":"MRP","prioridade":""},
    {"produto":80098,"qnt":3,"data":"06/11/2026","psy":"","cc":"600307","op":"26031401002","obs":"MRP","prioridade":""},
    {"produto":80098,"qnt":1,"data":"06/11/2026","psy":"","cc":"600307","op":"26031401001","obs":"MRP","prioridade":""},
    {"produto":80098,"qnt":4,"data":"13/11/2026","psy":"","cc":"600307","op":"26031401003","obs":"MRP","prioridade":""},
    {"produto":90017,"qnt":5,"data":"06/11/2026","psy":"","cc":"600307","op":"26031401004","obs":"MRP","prioridade":""},
]
tc_agrupado=agrupar_tc(tc_exemplos)
assert len(tc_agrupado)==3, tc_agrupado.to_dict("records")
assert tc_agrupado["qnt"].sum()==15
assert tc_agrupado["op"].eq("").all()
primeira=tc_agrupado.iloc[0]
assert primeira["produto"]==80098 and primeira["qnt"]==6
assert primeira["data"]=="06/11/2026"
assert primeira["obs"]=="MRP TC/TP - OPs: 26031401001, 26031401002",primeira["obs"]
assert tc_agrupado.iloc[1]["qnt"]==4 and tc_agrupado.iloc[1]["data"]=="13/11/2026"
assert tc_agrupado.iloc[2]["produto"]==90017 and tc_agrupado.iloc[2]["qnt"]==5

cad_tc=pd.DataFrame([
    {"Código":80098,"Lead Time (dias)":0},
    {"Código":90017,"Lead Time (dias)":0},
])
tc_com_prioridades=calcular(tc_agrupado,cad_tc)
assert tc_com_prioridades["prioridade"].isin(["1","2"]).all()
excel_tc=namespace["_compra_excel_protheus"](tc_com_prioridades)
with ZipFile(io.BytesIO(excel_tc)) as zip_excel:
    ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    xml=ET.fromstring(zip_excel.read("xl/worksheets/sheet1.xml"))
    linhas=xml.findall("./m:sheetData/m:row",ns)
    assert len(linhas)==4
    data_c=next(c for c in linhas[1].findall("m:c",ns) if c.get("r")=="C2")
    campo_op=next(c for c in linhas[1].findall("m:c",ns) if c.get("r")=="F2")
    campo_obs=next(c for c in linhas[1].findall("m:c",ns) if c.get("r")=="G2")
    campo_prio=next(c for c in linhas[1].findall("m:c",ns) if c.get("r")=="J2")
    assert "".join(data_c.find("m:is",ns).itertext())=="06/11/2026"
    assert "".join(campo_op.find("m:is",ns).itertext())==""
    assert "26031401001" in "".join(campo_obs.find("m:is",ns).itertext())
    assert "26031401002" in "".join(campo_obs.find("m:is",ns).itertext())
    assert "".join(campo_prio.find("m:is",ns).itertext()) in ("1","2")
print("MRP_COMPRA_TCTP_OP_VAZIA_E_AGRUPAMENTO_OK")

print("MRP_COMPRA_EXCEL_DATA_TEXTO_DD_MM_AAAA_OK")
print("MRP_COMPRA_LAYOUT_STSUP25_PRIORIDADE_J_OK")
print("MRP_COMPRA_ABRIR_FECHAR_VALIDADO")
