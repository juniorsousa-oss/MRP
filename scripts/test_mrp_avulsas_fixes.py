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
# Na aba principal existe somente a tabela geral; um unico registro por protocolo.
tabelar=helpers["_tabela_geral_solicitacoes"]
import pandas as pd
ids=[
    {"id":"pedido-3","numero":3,"estado":"LEGADO","solicitante":"consulta@gruposetta.com",
     "criado_em":"2026-10-15T14:00:00+00:00","finalidade":None},
    {"id":"pedido-2","numero":2,"estado":"PENDENTE","solicitante":"consulta@gruposetta.com",
     "criado_em":"2026-10-15T12:00:00+00:00","finalidade":"GARANTIA"},
    {"id":"pedido-1","numero":1,"estado":"SEPARADA","solicitante":"consulta@gruposetta.com",
     "criado_em":"2026-10-15T11:00:00+00:00","finalidade":"TRANSFERENCIA"},
]
filhos_por_id={
    "pedido-3":[{"status":"ABERTA"}],
    "pedido-2":[{"status":"ABERTA"} for _ in range(3)],
    "pedido-1":[{"status":"ATENDIDA"} for _ in range(2)],
}
ns.update({
    "pd":pd,
    "_labels":{"GARANTIA":"GARANTIA","TRANSFERENCIA":"TRANSFERÊNCIA ENTRE FILIAL"},
    "_itens_pedido":lambda pedido:filhos_por_id[pedido["id"]],
    "_situacao_pedido":status,
    "_hora":lambda dt:dt,
})
exec(compile(ast.fix_missing_locations(ast.Module(body=[tabelar],type_ignores=[])),
             "<mrp-tabela-solicitacoes>","exec"),ns)
tabela=ns["_tabela_geral_solicitacoes"](ids)
assert len(tabela)==len(ids) and list(tabela["S.A."])==["SA-000003","SA-000002","SA-000001"]
assert list(tabela["MATERIAIS"])==[1,3,2],tabela
assert list(tabela["SITUAÇÃO"])==["AGUARDANDO SEPARAÇÃO","PENDENTE","SEPARADA"]
assert list(tabela.columns)==["S.A.","SOLICITADO EM","SOLICITANTE","FINALIDADE","MATERIAIS","SITUAÇÃO"]
# A aba principal nunca exibe cartões de S.A. nem comandos de tratativa.
abas=[
    x for x in ast.walk(view)
    if isinstance(x,ast.With) and len(x.items)==1
    and isinstance(x.items[0].context_expr,ast.Subscript)
    and ast.unparse(x.items[0].context_expr).startswith("tabs[")
]
mapa_abas={
    ast.unparse(aba.items[0].context_expr):ast.unparse(aba)
    for aba in abas
}
assert sorted(mapa_abas)==["tabs[0]","tabs[1]","tabs[2]","tabs[3]","tabs[4]"],mapa_abas.keys()
assert "st.dataframe" in mapa_abas["tabs[0]"]
assert "_tabela_geral_solicitacoes" in mapa_abas["tabs[0]"]
assert "_mostrar_pedidos" not in mapa_abas["tabs[0]"]
for i in range(1,5): assert "_mostrar_pedidos" in mapa_abas[f"tabs[{i}]"]
assert "AGUARDANDO SEPARAÇÃO (" in src
assert "SEPARADAS (" in src and "ENTREGUES (" in src and "RECUSADAS (" in src
assert "with tab_pendentes:" in src and "mrp_avulsa_legado_tratar" in src
print("MRP_AVULSAS_ABAS_TABELA_GERAL_E_STATUS_OK")
print("MRP_AVULSAS_PROTOCOL_NUMEROS_CUSTOS_LAYOUT_OK")
