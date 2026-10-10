"""Testa o fluxo de solicitações na aplicação gerada, sem operações no banco."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parent.parent
built=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))
source=built["final"]
tree=ast.parse(source)
methods={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
assert "_mrp_avulsas_view" in methods
assert "_mrp_avulsas_call" in methods
view=ast.get_source_segment(source,methods["_mrp_avulsas_view"])
assert '["MRP ATUAL", "SOLICITAÇÕES AVULSAS"]' in source
assert 'usuario_id=str(dados.get("user_id") or "")' in view
assert 'if str(x.get("criado_por") or "")==usuario_id' in view
assert '"PENDENTES DE SEPARAÇÃO' in view
assert '"MINHAS SOLICITAÇÕES' in view
assert '"CONFIRMAR MATERIAL SEPARADO"' in view
assert '_mrp_avulsas_call("attend",{"id":chaves[alvo],"observacao":obs})' in view
assert 'if str(dados.get("role"))=="ADMIN":' in view
assert 'if tab_pendentes is not None:' in view
assert '"ATUALIZAR STATUS DAS SOLICITAÇÕES"' in view
assert 'st.rerun()' in view
assert "row['saldo']" in view and "row['div']" in view
assert "item['saldo']" in view and "item['div']" in view
assert 'status_exibicao' in view
assert '"ATENDIDO EM"' not in view and '"SEPARADO EM"' in view
assert 'max_value=max(0.001,maximo)' in view
assert 'st.form("mrp_avulsa_criar",clear_on_submit=True,enter_to_submit=False)' in view
assert 'st.form("mrp_avulsa_atender",enter_to_submit=False)' in view
assert '"RECUSAR SOLICITAÇÃO"' in view
assert '_mrp_avulsas_call("reject",{"id":chaves[alvo],"motivo":obs.strip()})' in view
assert 'if recusar and len(obs.strip())<5:' in view
assert '"RECUSADAS (' in view
assert '"OBSERVAÇÃO / MOTIVO DA RECUSA"' in view
assert '"RECUSADO EM"' in view

api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text(encoding="utf-8")
catalog=(root/"supabase/functions/mrp-avulsas-api/catalog.ts").read_text(encoding="utf-8")
assert 'selectMaterial(row)' in api
assert 'item.limite' in api
assert 'availableAfterReservations(item.limite' in api
assert 'x.saldo > 0 && x.div > 0' in api
assert 'role!=="ADMIN"' in api and 'query.eq("criado_por",userId)' in api
assert 'role !== "ADMIN"' in api and 'admin.rpc("mrp_avulsa_atender_seguro"' in api
assert 'displayStatus(r.status)' in api
assert 'for (const r of ledger || [])' in api
assert '"ATENDIDA" && Number(r.snapshot_id)' in api
assert '"Saldo em Estoque"' in catalog
assert '"DIV"' in catalog
assert 'Math.min(saldo, div)' in catalog
# A consulta pode ver o próprio status; não há alteração fiscal nem baixa de estoque.
assert 'atendido_em,observacao_atendimento' in api
assert 'p_div: item.limite' in api
print("MRP_AVULSAS_FLOW_OK")
