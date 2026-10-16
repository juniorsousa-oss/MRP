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
assert '_situacao_pedido(_pedido,_filhos)' in src
assert 'REGISTROS ANTERIORES · CONFERÊNCIA POR MATERIAL' in src
sql=(root/"supabase/migrations/20261016_mrp_avulsas_protocolos_000001.sql").read_text("utf-8")
assert 'row_number() over(order by criado_em,id)' in sql
assert "mrp_avulsas_protocolo_migracoes" in sql
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
assert 'carregarCustos(admin)' in api
assert 'valor_ultima_compra_atual' in api
# Na aba principal cada MATERIAL aparece em uma linha, repetindo seu protocolo.
tabelar=helpers["_tabela_geral_solicitacoes"]
metadata=helpers["_dados_complementares"]
condicao_relatorio=helpers["_condicao_garantia_relatorio"]
import pandas as pd
ids=[
    {"id":"pedido-3","numero":3,"estado":"LEGADO","solicitante":"consulta@gruposetta.com",
     "criado_em":"2026-10-15T14:00:00+00:00","finalidade":"GARANTIA"},
    {"id":"pedido-2","numero":2,"estado":"PENDENTE","solicitante":"consulta@gruposetta.com",
     "criado_em":"2026-10-15T12:00:00+00:00","finalidade":"GARANTIA"},
    {"id":"pedido-1","numero":1,"estado":"SEPARADA","solicitante":"consulta@gruposetta.com",
     "criado_em":"2026-10-15T11:00:00+00:00","finalidade":"ACERTO_GERENCIAL"},
]
filhos_por_id={
    "pedido-3":[{"id":10,"pedido_id":"pedido-3","codigo":"00000001","descricao":"ITEM A",
                  "quantidade":1,"status":"ABERTA"}],
    "pedido-2":[{"id":11+i,"pedido_id":"pedido-2","codigo":str(i+2).zfill(8),
                  "descricao":"ITEM "+str(i+2),"quantidade":i+1,"status":"ABERTA"}
                  for i in range(3)],
    "pedido-1":[{"id":20+i,"pedido_id":"pedido-1","codigo":str(i+5).zfill(8),
                  "descricao":"ITEM "+str(i+5),"quantidade":i+4,"status":"ATENDIDA"}
                  for i in range(2)],
}
todos_itens=[item for rows in filhos_por_id.values() for item in rows]
ns.update({
    "pd":pd,
    "_labels":{"GARANTIA":"GARANTIA","ACERTO_GERENCIAL":"ACERTO GERENCIAL"},
    "_dados_complementares":None,
    "_itens_pedido":lambda pedido:filhos_por_id[pedido["id"]],
    "_situacao_pedido":status,
    "_condicao_garantia":lambda pedido,item: (
        "AGUARDANDO RETORNO" if pedido.get("finalidade")=="GARANTIA"
        and pedido.get("estado")=="ENTREGUE" else ""
    ),
    "_hora":lambda dt:dt,
    "itens":todos_itens,
})
exec(compile(ast.fix_missing_locations(ast.Module(body=[metadata,condicao_relatorio,tabelar],type_ignores=[])),
             "<mrp-tabela-solicitacoes>","exec"),ns)
tabela=ns["_tabela_geral_solicitacoes"](ids)
assert len(tabela)==6,tabela
assert list(tabela["S.A."])==[
    "SA-000003","SA-000002","SA-000002","SA-000002","SA-000001","SA-000001"
],tabela
assert list(tabela["CÓDIGO"])==[
    "00000001","00000002","00000003","00000004","00000005","00000006"
],tabela
assert list(tabela["QUANTIDADE"])==[1.,1.,2.,3.,4.,5.],tabela
assert tabela.iloc[0]["OP(s)"]=="A PREENCHER NA ENTREGA" # Campo obrigatorio faltante.
assert tabela.iloc[0]["CR"]=="NA"
assert tabela.iloc[0]["APROVADOR"]=="NA"
assert tabela.iloc[0]["FILIAL"]=="NA"
assert tabela.iloc[0]["CONDIÇÃO GARANTIA"]=="AGUARDANDO ENTREGA"
assert tabela.iloc[-1]["OP(s)"]=="NA"
assert tabela.iloc[-1]["CR"]=="A PREENCHER NA ENTREGA"
assert tabela.iloc[-1]["APROVADOR"]=="A PREENCHER NA ENTREGA"
assert tabela.iloc[-1]["FILIAL"]=="NA"
assert tabela.iloc[-1]["CONDIÇÃO GARANTIA"]=="NA"
assert not tabela[["OP(s)","CR","APROVADOR","FILIAL","CONDIÇÃO GARANTIA"]].isin([""]).any().any()
assert '_exportar=_tabela_geral_solicitacoes(pedidos)' in src

assert set(["OP(s)","CR","APROVADOR","FILIAL"]).issubset(tabela.columns)
assert ns["_dados_complementares"]({
    "finalidade":"GARANTIA","psys":"25078201001",
})=={"OP(s)":"25078201001","CR":"NA","APROVADOR":"NA","FILIAL":"NA"}
assert ns["_dados_complementares"]({
    "finalidade":"ACERTO_GERENCIAL","cr":"600307","aprovador":"Gestão",
})=={"OP(s)":"NA","CR":"600307","APROVADOR":"Gestão","FILIAL":"NA"}
assert ns["_dados_complementares"]({
    "finalidade":"TRANSFERENCIA","destino":"ASTEC",
})=={"OP(s)":"NA","CR":"NA","APROVADOR":"NA","FILIAL":"ASTEC"}
assert ns["_dados_complementares"]({
    "finalidade":"TRANSFERENCIA","destino":None,
})["FILIAL"]=="ASTEC"

assert list(tabela["SITUAÇÃO"])==[
    "AGUARDANDO SEPARAÇÃO","AGUARDANDO SEPARAÇÃO",
    "AGUARDANDO SEPARAÇÃO","AGUARDANDO SEPARAÇÃO","SEPARADA","SEPARADA",
],tabela
assert list(tabela["FINALIDADE"])==[
    "GARANTIA","GARANTIA","GARANTIA","GARANTIA","ACERTO GERENCIAL","ACERTO GERENCIAL"
],tabela
assert list(tabela.columns)==[
    "S.A.","SOLICITADO EM","SOLICITANTE","FINALIDADE",
    "CÓDIGO","DESCRIÇÃO","QUANTIDADE","SITUAÇÃO","CONDIÇÃO GARANTIA",
    "OP(s)","CR","APROVADOR","FILIAL",
]
# Historico sem pedido_id continua aparecendo, sem desaparecer.
ns["itens"]=todos_itens+[{
    "id":44,"pedido_id":None,"codigo":"00000044","descricao":"ITEM ANTIGO",
    "quantidade":2,"status":"RECUSADA","solicitante":"consulta@gruposetta.com",
}]
tabela_legado=ns["_tabela_geral_solicitacoes"](ids)
assert len(tabela_legado)==7
assert tabela_legado.iloc[-1]["S.A."]=="REGISTRO #44"
assert tabela_legado.iloc[-1]["SITUAÇÃO"]=="RECUSADA"
for c in ("OP(s)","CR","APROVADOR","FILIAL","CONDIÇÃO GARANTIA"):
    assert tabela_legado.iloc[-1][c]=="NA",c
assert ns["_dados_complementares"]({
    "finalidade":"TRANSFERENCIA","destino":"  ",
})["FILIAL"]=="ASTEC"
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
for i in (1,2,4): assert "_mostrar_pedidos" in mapa_abas[f"tabs[{i}]"]
assert "_exibir_entregas" in mapa_abas["tabs[3]"]
assert 'metric("SEPARADAS · NÃO ENTREGUES",len(_separados)+len(_legados_separados))' in src
assert "Separadas: materiais com separação confirmada" in src
assert "AGUARDANDO SEPARAÇÃO (" in src
assert "SEPARADAS (" in src and "ENTREGUES (" in src and "RECUSADAS (" in src
assert "with tab_pendentes:" in src and "mrp_avulsa_legado_tratar" in src
print("MRP_AVULSAS_ABAS_TABELA_GERAL_E_STATUS_OK")
print("MRP_AVULSAS_PROTOCOL_NUMEROS_CUSTOS_LAYOUT_OK")
