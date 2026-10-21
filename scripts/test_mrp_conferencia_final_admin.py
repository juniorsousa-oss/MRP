"""Validação isolada da Conferência Final ADMIN; não modifica banco ou pedidos."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entry = (root / "app_mrp.py").read_text("utf-8")
marker = 'exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(marker) == 1
env = {"__file__": str(root / "app_mrp.py"), "__name__": "mrp_final_admin_test"}
exec(compile(entry.split(marker)[0], "app_mrp.py", "exec"), env, env)
runtime = env["_runtime_source"]
stop = 'exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(stop) == 1
state = {"__file__": str(root / "app_mrp_runtime.py"), "__name__": "mrp_final_admin_test"}
exec(compile(runtime.rsplit(stop, 1)[0], "app_mrp_runtime.py", "exec"), state, state)
source = state["_source"]
tree = ast.parse(source)
view = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_mrp_avulsas_view")
code = ast.get_source_segment(source, view)
for item in (
    'if perfil=="ADMIN":',
    'CONFERÊNCIA FINAL · ADMIN',
    'PENDENTES DE CONFERÊNCIA (',
    'CONCLUÍDAS (',
    'CONFERÊNCIA FINAL',
    'conferencia_final_confirmar',
    'CONFIRMAR ENCERRAMENTO ADMINISTRATIVO',
    'DOCUMENTO / REFERÊNCIA NO PROTHEUS',
    'Conferi materiais, códigos e quantidades',
    'Confirmei que a movimentação foi efetivada',
    'Conferi o documento',
    'confere_materiais',
    'confere_movimentacao',
    'confere_documento',
):
    assert item in code, f"Interface final sem componente: {item}"

index = (root / "supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
for item in (
    'if (action === "conferencia_final_confirmar")',
    'if (role !== "ADMIN")',
    'mrp_avulsa_conferencia_final_seguro',
    'conferencias_finais:conferencias',
    'CHECKLIST_FINAL_INCOMPLETO',
):
    assert item in index, f"API final sem validação: {item}"

sql = (root / "supabase/migrations/20261021_mrp_avulsas_conferencia_final_admin.sql").read_text("utf-8")
for item in (
    'where id = p_pedido_id for update',
    "v_pedido.estado <> 'ENTREGUE'",
    'CONFERENCIA_FINAL_JA_CONCLUIDA',
    'CHECKLIST_FINAL_INCOMPLETO',
    'grant execute on function',
    'to service_role',
    'revoke all on function',
):
    assert item in sql, f"RPC final sem proteção: {item}"

assert "estado='CONCLUIDO'" not in sql
print("MRP_CONFERENCIA_FINAL_ADMIN_OK")
