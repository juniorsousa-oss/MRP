"""Smoke de estrutura isolada: ADMIN usa três áreas, perfis operacionais intactos."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
entry=(root/"app_mrp.py").read_text(encoding="utf-8")
stop='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(stop)==1
scope={"__file__":str(root/"app_mrp.py"),"__name__":"mrp_admin_areas"}
exec(compile(entry.split(stop)[0],"app_mrp.py","exec"),scope,scope)
runtime=scope["_runtime_source"]
inner='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(inner)==1
state={"__file__":str(root/"app_mrp_runtime.py"),"__name__":"mrp_admin_areas"}
exec(compile(runtime.rsplit(inner,1)[0],"app_mrp_runtime.py","exec"),state,state)
code=state["_source"]
view=next(n for n in ast.parse(code).body
          if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
src=ast.get_source_segment(code,view)
for token in (
    'options=("SOLICITAÇÕES","CONFERÊNCIA FINAL","ADMINISTRAÇÃO")',
    'key="mrp_avulsas_admin_area"',
    'if _mrp_av_admin_area=="SOLICITAÇÕES":',
    'if perfil=="ADMIN" and _mrp_av_admin_area=="CONFERÊNCIA FINAL":',
    'if perfil=="ADMIN" and _mrp_av_admin_area=="ADMINISTRAÇÃO":',
    'CONFIRMAR ENCERRAMENTO ADMINISTRATIVO',
    'PENDENTES DE CONFERÊNCIA',
    'CONCLUÍDAS (',
    'ADMINISTRAÇÃO · NOTIFICAÇÕES POR E-MAIL',
    'ADMINISTRAÇÃO · TESTAR CONEXÃO COM O TEAMS',
    'if perfil=="OPERADOR":',
    'if perfil=="CONSULTA":',
    'CONFIRMAR MATERIAL SEPARADO',
    'CONFIRMAR ENTREGA',
):
    assert token in src,token
assert src.count('key="mrp_avulsas_admin_area"')==1
assert "st.markdown(\"### CONFERÊNCIA FINAL · ADMIN\")" in src
print("MRP_AVULSAS_ADMIN_AREAS_OK",len(code))
