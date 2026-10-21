"""Smoke de garantia em duas movimentações: sem efeitos no banco de dados."""
import ast
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
entry=(root/"app_mrp.py").read_text("utf-8")
stop='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(stop)==1
scope={"__file__":str(root/"app_mrp.py"),"__name__":"mrp_garantia_smoke"}
exec(compile(entry.split(stop)[0],"app_mrp.py","exec"),scope,scope)
runtime=scope["_runtime_source"]
end='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(end)==1
rscope={"__file__":str(root/"app_mrp_runtime.py"),"__name__":"mrp_garantia_smoke"}
exec(compile(runtime.rsplit(end,1)[0],"app_mrp_runtime.py","exec"),rscope,rscope)
source=rscope["_source"]
view=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
src=ast.get_source_segment(source,view)
for item in (
 "CONFERÊNCIA FINAL · ADMIN",
 "ETAPA 1 · TRANSFERÊNCIA À ASTEC",
 "ETAPA 2 · RESULTADO DA ASTEC",
 "ETAPA 3 · CONFIRMAÇÃO FINAL POR MATERIAL",
 "CONFIRMAR TRANSFERÊNCIA À ASTEC",
 "AGUARDANDO ANÁLISE",
 "DEVOLVIDO SEM USO",
 "CONFIRMAR BAIXA",
 "CONFIRMAR DEVOLUÇÃO AO ESTOQUE",
 "garantia_astec_confirmar",
 "garantia_movimento_final_confirmar",
 "movimento_final_confirmado_em",
 'continue',
 "disabled=(not _astec_liberada or _movimentacao_final)",
 "if perfil==\"ADMIN\" and _mrp_av_admin_area==\"CONFERÊNCIA FINAL\"",
):
 assert item in src,item
assert "ETAPA 4 · VALIDAÇÃO FINAL DO GESTOR" not in src
assert "mrp_doc_astec_" not in src
assert "mrp_doc_movimento_final_" not in src
assert "confirmar_astec" in src
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
for item in ("garantia_astec_confirmar","garantia_movimento_final_confirmar",
             "mrp_avulsa_garantia_ast_ec_seguro","mrp_avulsa_garantia_movimento_final_seguro",
             "garantia_regularizacoes:garantiaRegularizacoes"):
 assert item in api,item
migration=(root/"supabase/migrations/20261021_mrp_avulsas_garantia_duas_movimentacoes.sql").read_text("utf-8")
assert "REGULARIZACAO_GARANTIA" in migration
for item in (
 "garantia_movimento_completo_check",
 "mrp_avulsa_garantia_resultado_seguro",
 "AGUARDANDO_ENDERECAMENTO_ASTEC",
 "MOVIMENTACAO_FINAL_JA_CONFIRMADA",
 "GARANTIA_PENDENTE_ASTEC_DESTINACAO_OU_MOVIMENTACAO_FINAL",
 "RESULTADO_BLOQUEADO_APOS_MOVIMENTACAO_FINAL",
 "revoke all on function",
 "to service_role",
):
 assert item in migration,item
print("MRP_GARANTIA_ASTEC_BAIXA_RETORNO_ADMIN_OK")
