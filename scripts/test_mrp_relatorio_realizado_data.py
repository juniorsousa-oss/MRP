"""Teste funcional dos campos de execução/data do relatório de S.A., sem banco."""
import ast
import sys
import textwrap
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
entry=(root/"app_mrp.py").read_text("utf-8")
stop='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(stop)==1
scope={"__file__":str(root/"app_mrp.py"),"__name__":"test_mrp_report"}
exec(compile(entry.split(stop)[0],"app_mrp.py","exec"),scope,scope)
runtime=scope["_runtime_source"]
end='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(end)==1
rscope={"__file__":str(root/"app_mrp_runtime.py"),"__name__":"test_mrp_report"}
exec(compile(runtime.rsplit(end,1)[0],"app_mrp_runtime.py","exec"),rscope,rscope)
generated=rscope["_source"]
view=next(n for n in ast.parse(generated).body
          if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
fn=next(n for n in view.body
        if isinstance(n,ast.FunctionDef) and n.name=="_tabela_geral_solicitacoes")
fn_source=textwrap.dedent(ast.get_source_segment(generated,fn))

class PD:
    @staticmethod
    def DataFrame(rows,columns):
        return {"linhas":rows,"colunas":columns}

pedidos=[
    {"id":"garantia-completa","numero":1,"estado":"ENTREGUE","finalidade":"GARANTIA",
     "solicitante":"usuario1@exemplo.test","criado_em":"2026-10-20","entregue_em":"2026-10-20"},
    {"id":"garantia-pendente","numero":2,"estado":"ENTREGUE","finalidade":"GARANTIA",
     "solicitante":"usuario2@exemplo.test","criado_em":"2026-10-20","entregue_em":"2026-10-20"},
    {"id":"acerto-concluido","numero":3,"estado":"ENTREGUE","finalidade":"ACERTO_GERENCIAL",
     "solicitante":"usuario3@exemplo.test","criado_em":"2026-10-20","entregue_em":"2026-10-20"},
]
items={
    "garantia-completa":[{"id":31,"status":"ATENDIDA","codigo":"1","descricao":"Teste",
                          "quantidade":2,"criado_em":"2026-10-20"}],
    "garantia-pendente":[{"id":32,"status":"ATENDIDA","codigo":"2","descricao":"Teste",
                          "quantidade":1,"criado_em":"2026-10-20"}],
    "acerto-concluido":[{"id":33,"status":"ATENDIDA","codigo":"3","descricao":"Teste",
                          "quantidade":1,"criado_em":"2026-10-20"}],
}
conferencias={
    "garantia-completa":{"confirmado_em":"2026-10-21T15:00:00Z"},
    "acerto-concluido":{"confirmado_em":"2026-10-21T16:00:00Z"},
}
garantia={
    "31":{"astec_confirmado_em":"2026-10-20T09:00:00Z",
          "movimento_final_confirmado_em":"2026-10-21T12:00:00Z"},
    "32":{"astec_confirmado_em":"2026-10-21T08:00:00Z",
          "movimento_final_confirmado_em":None},
}
ctx={
    "pd":PD,
    "itens":[],
    "_conferencias_por_pedido":conferencias,
    "_garantias_por_item":garantia,
    "_itens_pedido":lambda pedido:items[pedido["id"]],
    "_protocolo":lambda pedido:"SA-"+str(pedido["numero"]),
    "_hora":lambda x: "" if x is None else str(x),
    "_labels":{"GARANTIA":"GARANTIA","ACERTO_GERENCIAL":"ACERTO GERENCIAL"},
    "_dados_complementares":lambda pedido:{"OP(s)":"NA","CR":"NA",
                                       "APROVADOR":"NA","FILIAL":"NA"},
    "_condicao_garantia_relatorio":lambda pedido,item:"NA",
}
exec(compile(fn_source,"report_function","exec"),ctx,ctx)
df=ctx["_tabela_geral_solicitacoes"](pedidos)
expected=[
    "ASTEC REALIZADA","DATA ASTEC",
    "MOVIMENTO FINAL REALIZADO","DATA MOVIMENTO FINAL",
    "VALIDAÇÃO FINAL REALIZADA","DATA VALIDAÇÃO FINAL",
]
for col in expected:
    assert col in df["colunas"],col

rows={r["S.A."]:r for r in df["linhas"]}
assert rows["SA-1"]["ASTEC REALIZADA"]=="SIM"
assert rows["SA-1"]["DATA ASTEC"]=="2026-10-20T09:00:00Z"
assert rows["SA-1"]["MOVIMENTO FINAL REALIZADO"]=="SIM"
assert rows["SA-1"]["DATA MOVIMENTO FINAL"]=="2026-10-21T12:00:00Z"
assert rows["SA-1"]["VALIDAÇÃO FINAL REALIZADA"]=="SIM"
assert rows["SA-1"]["DATA VALIDAÇÃO FINAL"]=="2026-10-21T15:00:00Z"
assert rows["SA-2"]["ASTEC REALIZADA"]=="SIM"
assert rows["SA-2"]["MOVIMENTO FINAL REALIZADO"]=="NÃO"
assert rows["SA-2"]["DATA MOVIMENTO FINAL"]==""
assert rows["SA-2"]["VALIDAÇÃO FINAL REALIZADA"]=="NÃO"
assert rows["SA-2"]["DATA VALIDAÇÃO FINAL"]==""
assert rows["SA-3"]["ASTEC REALIZADA"]=="N/A"
assert rows["SA-3"]["MOVIMENTO FINAL REALIZADO"]=="N/A"
assert rows["SA-3"]["VALIDAÇÃO FINAL REALIZADA"]=="SIM"
assert rows["SA-3"]["DATA VALIDAÇÃO FINAL"]=="2026-10-21T16:00:00Z"
print("MRP_RELATORIO_REALIZADO_DATA_OK")
