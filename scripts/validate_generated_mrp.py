"""Monta todas as camadas do MRP sem abrir o Streamlit nem ler dados externos."""
from pathlib import Path
import ast
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
source=(ROOT/"app_mrp.py").read_text(encoding="utf-8")
last='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert source.count(last)==1, "Execução principal do MRP alterada"
ns={"__file__":str(ROOT/"app_mrp.py"),"__name__":"mrp_code_validation"}
exec(compile(source.split(last)[0],str(ROOT/"app_mrp.py"),"exec"),ns)
runtime=ns["_runtime_source"]
inner='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.endswith(inner+"\n") or runtime.rstrip().endswith(inner), "Runtime do MRP alterado"
script=runtime.rsplit(inner,1)[0]
rs={"__file__":str(ROOT/"app_mrp_runtime.py"),"__name__":"mrp_code_validation"}
exec(compile(script,"app_mrp_runtime.py","exec"),rs)
final=rs["_source"]
compile(final,"mrp_generated.py","exec")
ast.parse(final)
for token in [
    'SOLICITAÇÕES AVULSAS',
    'mrp-avulsas-api',
    'def _mrp_avulsas_view():',
    'consulta_projeto_busca',
    'admin_projeto_busca',
    'consulta_produto_busca',
    'admin_produto_busca',
    'codigo_consulta != "TODOS"',
    'projeto_consulta != "TODOS"',
    'produto_consulta != "TODOS"',
    'codigo_admin != "TODOS"',
    'projeto_admin != "TODOS"',
    'produto_admin != "TODOS"',
    'QUANTIDADE SOLICITADA',
    'SOLICITAÇÕES ATENDIDAS',
]:
    assert token in final, f"Ausente no código final: {token}"
assert 'st.session_state.pop(_key,None)' not in final, "Filtros do projeto ainda são zerados automaticamente."
print("MRP_GENERATED_VALIDATED",len(final))
