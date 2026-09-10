from pathlib import Path
import re

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
old = 'op=mt[(mt["Código Produto"]>0)&mt["Semana Entrega"].between(1,53)].copy(); op=op.drop_duplicates(subset=["ORDEM DE PRODUÇÃO","Código Produto"]); fab_week=op.groupby(["Código Produto","Semana Entrega"]).size().reset_index(name="Produzindo"); fab_week.columns=["Código","Semana","Produzindo"]'
new = '''op=mt[(mt["Código Produto"]>0)&mt["Semana Entrega"].between(1,53)].copy()
# FABRICAÇÃO TC/TP: cada OP conta uma única vez por produto.
# O relatório possui várias linhas de BOM/material por OP; nunca contar essas linhas como peças produzidas.
op["_OP_CHAVE"]=op["ORDEM DE PRODUÇÃO"].astype(str).str.strip()
op["_PROD_CHAVE"]=pd.to_numeric(op["Código Produto"],errors="coerce")
op=op[op["_OP_CHAVE"].ne("")&op["_PROD_CHAVE"].notna()].copy()
op=op.drop_duplicates(subset=["_OP_CHAVE","_PROD_CHAVE","Semana Entrega"])
fab_week=op.groupby(["_PROD_CHAVE","Semana Entrega"],as_index=False)["_OP_CHAVE"].nunique().rename(columns={"_PROD_CHAVE":"Código","Semana Entrega":"Semana","_OP_CHAVE":"Produzindo"})
fab_week["Código"]=pd.to_numeric(fab_week["Código"],errors="coerce")'''
if old not in s:
    raise SystemExit('Trecho de fabricação TC/TP não encontrado; nenhuma alteração realizada.')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('Patch aplicado: fabricação TC/TP passa a contar OPs únicas por produto e semana.')
