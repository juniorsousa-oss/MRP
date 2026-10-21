"""Testa que garantias e entregas são contadas por S.A., e materiais em cartão próprio."""
import ast
import sys
import textwrap
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
entry=(root/"app_mrp.py").read_text("utf-8")
stop='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(stop)==1
stage={"__file__":str(root/"app_mrp.py"),"__name__":"test_mrp_contadores"}
exec(compile(entry.split(stop)[0],"app_mrp.py","exec"),stage,stage)
runtime=stage["_runtime_source"]
mark='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(mark)==1
scope={"__file__":str(root/"app_mrp_runtime.py"),"__name__":"test_mrp_contadores"}
exec(compile(runtime.rsplit(mark,1)[0],"app_mrp_runtime.py","exec"),scope,scope)
source=scope["_source"]
view=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
fn=next(n for n in view.body if isinstance(n,ast.FunctionDef) and n.name=="_agrupar_garantias_entregues")
snippet=textwrap.dedent(ast.get_source_segment(source,fn))
pedidos=[
    {"id":"g-completa","finalidade":"GARANTIA"},
    {"id":"g-pendente","finalidade":"GARANTIA"},
    {"id":"g-mista","finalidade":"GARANTIA"},
    {"id":"transferencia","finalidade":"TRANSFERENCIA"},
]
itens={
    "g-completa":[{"destino_garantia":"UTILIZADO"},{"destino_garantia":"DEVOLVIDO"}],
    "g-pendente":[{"destino_garantia":"AGUARDANDO_RETORNO"}],
    "g-mista":[{"destino_garantia":"UTILIZADO"},{"destino_garantia":"AGUARDANDO_RETORNO"}],
    "transferencia":[{"destino_garantia":None}],
}
ctx={"_itens_pedido":lambda p:itens[p["id"]]}
exec(compile(snippet,"agrupar","exec"),ctx,ctx)
grupo=ctx["_agrupar_garantias_entregues"](pedidos)
assert len(grupo["garantias"])==3
assert len(grupo["demais"])==1
assert {p["id"] for p in grupo["aguardando"]}=={"g-pendente","g-mista"}
assert {p["id"] for p in grupo["confirmadas"]}=={"g-completa"}
assert not {p["id"] for p in grupo["aguardando"]}&{p["id"] for p in grupo["confirmadas"]}
assert grupo["itens_aguardando"]==2
assert grupo["itens_confirmados"]==3

# Nos títulos, unidades explícitas: S.A., não materiais.
for value in (
    '"GARANTIAS ("+str(_tot_garantias)+" S.A.s)"',
    '"DEMAIS ENTREGAS ("+str(len(_grupos["demais"]))+" S.A.s)"',
    '"AGUARDANDO CONFIRMAÇÃO ("+str(len(_grupos["aguardando"]))+" S.A.s)"',
    '"CONFIRMADAS ("+str(len(_grupos["confirmadas"]))+" S.A.s)"',
    'MATERIAIS SEPARADOS E ENTREGUES',
    '_materiais_separados',
    '_materiais_entregues',
):
    assert value in source, value
assert '_tot_garantias=(_grupos["itens_aguardando"]+_grupos["itens_confirmados"])' not in source
assert '"GARANTIAS ("+str(_tot_garantias)+" materiais)"' not in source
print("MRP_CONTADORES_SA_MATERIAIS_OK")
