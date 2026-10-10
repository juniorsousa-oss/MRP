"""Regressão da recusa: formulário explícito, autenticação, auditoria e liberação de reservas.

Não acessa dados de produção e não altera solicitações reais.
"""
import ast
import runpy
from pathlib import Path

root = Path(__file__).resolve().parents[1]
final = runpy.run_path(str(root / "scripts" / "validate_generated_mrp.py"))["final"]
tree = ast.parse(final)
target = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "_mrp_avulsas_view"
)
view = ast.get_source_segment(final, target)
forms = []
for node in ast.walk(target):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "form":
            labels = [arg.value for arg in node.args if isinstance(arg, ast.Constant)]
            kwargs = {k.arg: k.value for k in node.keywords}
            forms.append((labels, kwargs))
form_map = {label: kwargs for labels, kwargs in forms for label in labels}
for key in ("mrp_avulsa_criar", "mrp_avulsa_atender"):
    assert key in form_map, key
    assert isinstance(form_map[key].get("enter_to_submit"), ast.Constant)
    assert form_map[key]["enter_to_submit"].value is False, key
assert view.count("REGISTRAR SOLICITAÇÃO") == 1
assert '"RECUSAR SOLICITAÇÃO"' in view
assert '"CONFIRMAR MATERIAL SEPARADO"' in view
assert 'if concluir or recusar:' in view
assert 'if recusar and len(obs.strip())<5:' in view
assert '_mrp_avulsas_call("reject",{"id":chaves[alvo],"motivo":obs.strip()})' in view
assert '"RECUSADAS (' in view
assert '"RECUSADO EM"' in view

api = (root / "supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
mapping = (root / "supabase/functions/mrp-avulsas-api/catalog.ts").read_text("utf-8")
sql = (root / "supabase/migrations/20261010_mrp_avulsas_recusa.sql").read_text("utf-8")
assert 'if (action === "reject") {' in api
reject = api[api.index('if (action === "reject") {'):api.index('if (action === "attend") {')]
assert 'if (role !== "ADMIN") return fail("ADMIN_REQUIRED", 403)' in reject
assert 'motivo.length < 5 || motivo.length > 1000' in reject
assert 'admin.rpc("mrp_avulsa_recusar_seguro"' in reject
assert 'p_actor: userId' in reject and 'p_motivo: motivo' in reject
assert 'recusado_em' in api
assert 'if (value==="RECUSADA") return "RECUSADA"' in mapping

assert "status in ('ABERTA','ATENDIDA','RECUSADA')" in sql
assert "where id = p_id" in sql and "and status = 'ABERTA'" in sql
assert "length(v_motivo) < 5" in sql
assert "pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'))" in sql
assert "observacao_atendimento = v_motivo" in sql
assert 'from public, anon, authenticated' in sql
assert 'to service_role' in sql
assert "recusado_por" in sql and "recusado_em" in sql
# A API de listagem reserva apenas ABERTA e ATENDIDA; recusas não reduzem disponibilidade.
assert '.in("status",["ABERTA","ATENDIDA"])' in api
assert 'r.status === "ABERTA"' in api
assert 'r.status === "ATENDIDA"' in api
print("MRP_AVULSAS_RECUSA_VALIDADA")
