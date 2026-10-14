"""Testes das regras de compra do MRP sem abrir o Streamlit."""
from __future__ import annotations

import ast
import csv
import io
import runpy
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
    "_compra_csv_protheus",
    "_compra_abrir",
    "_compra_fechar",
}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names, "Funções de compra ausentes no código gerado"
# Isola as regras puras de compra sem invocar decorators de Streamlit.
for node in nodes:
    node.decorator_list = []
namespace = {"pd": pd, "date": date, "st": SimpleNamespace(session_state={})}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "mrp_compra_puro.py", "exec"), namespace)
calcular = namespace["_preparar_compra_prioridades"]
gerar_csv = namespace["_compra_csv_protheus"]

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
data = gerar_csv(result).decode("cp1252")
linhas = list(csv.reader(io.StringIO(data)))
assert linhas[0] == ["Produto", "Qtd", "data", "psy", "cc", "op", "obs", "prioridade", "prj", "", ""], linhas[0]
assert all(len(row) == 11 for row in linhas), linhas
assert [row[7] for row in linhas[1:]] == ["2", "1", "1"]
assert linhas[1][0] == "00140027" and linhas[1][8] == ""

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
assert "col_confirmar,col_csv,col_excel,col_finalizar" in source
print("MRP_COMPRA_PRIORIDADE_CSV_OK")
print("MRP_COMPRA_ABRIR_FECHAR_VALIDADO")
