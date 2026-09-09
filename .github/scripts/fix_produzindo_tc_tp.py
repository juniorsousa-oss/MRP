from pathlib import Path

path = Path("app_mrp.py")
text = path.read_text(encoding="utf-8")
old = '''op=mt[(mt["Código Produto"]>0)&mt["Semana Entrega"].between(1,53)].copy(); fab_week=op.groupby(["Código Produto","Semana Entrega"]).size().reset_index(name="Produzindo"); fab_week.columns=["Código","Semana","Produzindo"]'''
new = '''op=mt[(mt["Código Produto"]>0)&mt["Semana Entrega"].between(1,53)].copy(); op=op.drop_duplicates(subset=["ORDEM DE PRODUÇÃO","Código Produto"]); fab_week=op.groupby(["Código Produto","Semana Entrega"]).size().reset_index(name="Produzindo"); fab_week.columns=["Código","Semana","Produzindo"]'''
if old not in text:
    raise SystemExit("Trecho de cálculo de Produzindo não encontrado; nenhuma alteração foi feita.")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Correção aplicada: Produzindo agora considera apenas 1 ocorrência por ORDEM DE PRODUÇÃO + CÓDIGO PRODUTO.")
