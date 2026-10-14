"""Testes das regras de compra do MRP sem abrir o Streamlit."""
from __future__ import annotations

import ast
import csv
import io
import runpy
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
}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names, "Funções de compra ausentes no código gerado"
# Isola as regras puras de compra sem invocar decorators de Streamlit.
for node in nodes:
    node.decorator_list = []
namespace = {"pd": pd, "date": date}
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
print("MRP_COMPRA_PRIORIDADE_CSV_OK")
