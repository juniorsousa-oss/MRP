"""Testa recusa individual legado e recusa do pedido único; sem writes em produção."""
import ast,runpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
view=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
form_names={}
for n in ast.walk(view):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="form":
        label=n.args[0].value if n.args and isinstance(n.args[0],ast.Constant) else None
        form_names[label]={kw.arg:kw.value for kw in n.keywords}
for form in ("mrp_avulsa_criar","mrp_avulsa_atender","mrp_avulsa_entregar"):
    assert form in form_names,form
    assert form_names[form]["enter_to_submit"].value is False
v=ast.get_source_segment(source,view)
assert 'if recusar and len(obs.strip())<5:' in v
assert '"RECUSAR SOLICITAÇÃO"' in v
assert '"CONFIRMAR MATERIAL SEPARADO"' in v
assert '"CONFIRMAR ENTREGA"' in v
assert '"pedido_tratar"' in v
sql=(root/"supabase/migrations/20261015_mrp_avulsas_fluxo_entrega.sql").read_text("utf-8")
assert "role='OPERADOR'" in sql
assert "'RECUSADA'" in sql and "'ENTREGUE'" in sql
assert "pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'))" in sql
assert "status='RECUSADA'" in sql
assert "status='ATENDIDA'" in sql
assert "VALOR_ULTIMA_COMPRA_AUSENTE" in sql  # regra antiga, substituida pela nova
nova_migracao=(root/"supabase/migrations/20261016_mrp_custo_coluna_m_zero.sql").read_text("utf-8")
assert "valor_unitario_ref=0" in nova_migracao
assert "VALOR_ULTIMA_COMPRA_AUSENTE" not in nova_migracao
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
assert 'if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED",403);' in api
assert 'if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED", 403);' in api
assert '.in("status",["ABERTA","ATENDIDA"])' in api
print("MRP_AVULSAS_RECUSA_E_ENTREGA_OK")
