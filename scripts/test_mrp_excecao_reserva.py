"""Verificação estática segura do fluxo: nenhuma solicitação real é gerada."""
import ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]
entry=(root/"app_mrp.py").read_text("utf-8")
marker='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(marker)==1
ctx={"__file__":str(root/"app_mrp.py"),"__name__":"exc_smoke"}
exec(compile(entry.split(marker)[0],"app_mrp.py","exec"),ctx,ctx)
runtime=ctx["_runtime_source"]
stop='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(stop)==1
env={"__file__":str(root/"app_mrp_runtime.py"),"__name__":"exc_smoke"}
exec(compile(runtime.rsplit(stop,1)[0],"app_mrp_runtime.py","exec"),env,env)
tree=ast.parse(env["_source"])
view=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
content=ast.get_source_segment(env["_source"],view).lower()
for token in ("solicitação excepcional","exception_lookup","exception_submit","exception_list",
 "exception_decide","exception_regularize","regularização e criar s.a.",
 "projeto / op com reserva impactada"):
 assert token in content,token
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
for term in ("mrp_excecao_solicitar_seguro","mrp_excecao_decidir_seguro",
 "mrp_excecao_regularizar_e_criar_seguro","input.confirmacao!==true",
 "materialExcecao(admin","role!==\"ADMIN\"","role!==\"CONSULTA\""):
 assert term in api,term
sql=(root/"supabase/migrations/20261023_mrp_excecoes_reserva_controlada.sql").read_text("utf-8")
for term in ("pg_advisory_xact_lock","EXCECAO_NAO_APROVADA",
 "ESTOQUE_COMPROMETIDO_ANTES_DA_REGULARIZACAO",
 "enable row level security","to service_role","excecao_id"):
 assert term in sql,term
print("MRP_EXCECOES_REGRESSAO_OK")
