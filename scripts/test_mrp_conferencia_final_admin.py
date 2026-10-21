"""Validação isolada da Conferência Final ADMIN; não modifica banco ou pedidos."""
import ast
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
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
    'conferencia_final_confirmar',
    'CONFIRMAR ENCERRAMENTO ADMINISTRATIVO',
    'NÚMERO DA NOTA FISCAL',
    'OBSERVAÇÕES (OPCIONAL)',
    '"EMISSAO_NF"',
    'if _finalidade=="TRANSFERENCIA":',
):
    assert item in code, f"Interface final sem componente: {item}"

# Ninguém deve confirmar checkboxes que não existem na interface.
for unwanted in (
    'Conferi materiais, códigos e quantidades da solicitação.',
    'Confirmei que a movimentação foi efetivada no Protheus.',
    'Conferi o documento e sua vinculação à solicitação.',
    'Todos os três itens do checklist são obrigatórios.',
):
    assert unwanted not in code, unwanted

index = (root / "supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
for item in (
    'if (action === "conferencia_final_confirmar")',
    'if (role !== "ADMIN")',
    'mrp_avulsa_conferencia_simples_seguro',
    'conferencias_finais:conferencias',
    'NUMERO_DOCUMENTO_OBRIGATORIO',
):
    assert item in index, f"API final sem validação: {item}"

sql = (root / "supabase/migrations/20261021_mrp_conferencia_simplificada.sql").read_text("utf-8")
for item in (
    'where id=p_pedido_id for update',
    "v_pedido.estado<>'ENTREGUE'",
    'CONFERENCIA_FINAL_JA_CONCLUIDA',
    'GARANTIA_EXIGE_FLUXO_ASTEC',
    'false,false,false',
    'grant execute on function',
    'to service_role',
    'revoke all on function',
):
    assert item in sql, f"Nova RPC sem proteção: {item}"

assert "estado='CONCLUIDO'" not in sql
print("MRP_CONFERENCIA_FINAL_ADMIN_OK")
