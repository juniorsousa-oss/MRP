"""Regressao da apresentacao de S.A. existentes e da numeracao publica."""
from pathlib import Path
import ast,runpy

root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
view=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
src=ast.get_source_segment(source,view)
helpers={n.name:n for n in view.body if isinstance(n,ast.FunctionDef)}
assert "_situacao_pedido" in helpers
assert "_protocolo" in helpers
ns={}
code=ast.Module(body=[helpers["_situacao_pedido"],helpers["_protocolo"]],type_ignores=[])
exec(compile(ast.fix_missing_locations(code),"<mrp-avulsa-helpers>","exec"),ns)
make=ns["_protocolo"]
assert make({"numero":1,"id":"a"})=="SA-000001"
assert make({"numero":3,"id":"a"})=="SA-000003"
assert make({"numero":4,"id":"a"})=="SA-000004"
status=ns["_situacao_pedido"]
p={"estado":"LEGADO"}
assert status(p,[{"status":"ABERTA"}])=="AGUARDANDO SEPARAÇÃO"
assert status(p,[{"status":"ATENDIDA"},{"status":"ATENDIDA"}])=="SEPARADA"
assert status(p,[{"status":"RECUSADA"}])=="RECUSADA"
assert status(p,[{"status":"ATENDIDA"},{"status":"RECUSADA"}])=="TRATATIVA PARCIAL"
assert status({"estado":"ENTREGUE"},[{"status":"ATENDIDA"}])=="ENTREGUE"
assert 'st.columns([5,2.4,2.2],gap="medium")' in src
assert 'st.caption("SOLICITADO EM")' in src
assert 'st.caption("SOLICITANTE")' in src
assert 'st.caption("SITUAÇÃO")' in src
assert 'len(_pendentes)+len(_legados_pendentes)' in src
assert 'len(_separados)+len(_legados_separados)' in src
assert 'valor_ultima_compra_atual' in src
assert 'Não registrado neste pedido' not in src # novas mensagens explicitas
assert '_situacao_pedido(p,_itens_pedido(p))' in src
assert 'REGISTROS ANTERIORES · CONFERÊNCIA POR MATERIAL' in src
sql=(root/"supabase/migrations/20261016_mrp_avulsas_protocolos_000001.sql").read_text("utf-8")
assert 'row_number() over(order by criado_em,id)' in sql
assert "mrp_avulsas_protocolo_migracoes" in sql
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
assert 'carregarCustos(admin)' in api
assert 'valor_ultima_compra_atual' in api
print("MRP_AVULSAS_PROTOCOL_NUMEROS_CUSTOS_LAYOUT_OK")
