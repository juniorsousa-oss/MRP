"""Regressão de subtabs Garantias dentro de Entregues (por item, sem duplicação)."""
import ast,runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
view=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef)
          and x.name=="_mrp_avulsas_view")
parts={x.name:x for x in view.body if isinstance(x,ast.FunctionDef)}
assert "_agrupar_garantias_entregues" in parts
assert "_exibir_entregas" in parts
assert "_mostrar_pedidos" in parts

garantia={"id":"garantia-1","numero":4,"finalidade":"GARANTIA","estado":"ENTREGUE"}
garantia_pendente={"id":"garantia-2","numero":5,"finalidade":"GARANTIA","estado":"ENTREGUE"}
acerto={"id":"acerto-1","numero":6,"finalidade":"ACERTO_GERENCIAL","estado":"ENTREGUE"}
filhos={
 "garantia-1":[
   {"id":100,"codigo":"00000001","destino_garantia":"AGUARDANDO_RETORNO"},
   {"id":101,"codigo":"00000002","destino_garantia":"UTILIZADO"},
   {"id":102,"codigo":"00000003","destino_garantia":"DEVOLVIDO"},
 ],
 "garantia-2":[
   {"id":103,"codigo":"00000004","destino_garantia":None},
 ],
 "acerto-1":[{"id":104,"codigo":"00000005","destino_garantia":None}],
}
ns={"_itens_pedido":lambda p:filhos[p["id"]]}
m=ast.Module(body=[parts["_agrupar_garantias_entregues"]],type_ignores=[])
exec(compile(ast.fix_missing_locations(m),"<garantias>","exec"),ns)
split=ns["_agrupar_garantias_entregues"]([garantia,garantia_pendente,acerto])
assert [p["numero"] for p in split["garantias"]]==[4,5]
assert [p["numero"] for p in split["aguardando"]]==[4,5]
assert [p["numero"] for p in split["confirmadas"]]==[4]
assert [p["numero"] for p in split["demais"]]==[6]
assert split["itens_aguardando"]==2
assert split["itens_confirmados"]==2
assert split["itens_utilizados"]==1
assert split["itens_devolvidos"]==1
assert split["itens_aguardando"]+split["itens_confirmados"]==4
vazia=ns["_agrupar_garantias_entregues"]([])
assert vazia["itens_aguardando"]==0 and vazia["itens_confirmados"]==0
assert not vazia["garantias"] and not vazia["demais"]

src=ast.get_source_segment(source,view)
mostrar=ast.get_source_segment(source,parts["_mostrar_pedidos"])
exibir=ast.get_source_segment(source,parts["_exibir_entregas"])
assert "filtrar_itens=None" in mostrar
assert "filhos=[i for i in filhos if filtrar_itens(i)]" in mostrar
assert "if not filhos:" in mostrar
assert "grupo=\"garantia_pendente\"" in exibir
assert "grupo=\"garantia_confirmada\"" in exibir
assert "grupo=\"outras_entregas\"" in exibir
assert '"AGUARDANDO CONFIRMAÇÃO ("' in exibir
assert '"CONFIRMADAS ("' in exibir
assert '"GARANTIAS ("' in exibir
assert '"DEMAIS ENTREGAS ("' in exibir
assert '"Nenhum material de garantia aguardando confirmação."' in exibir
assert '"Nenhum material de garantia confirmado."' in exibir
assert '_exibir_entregas()' in src
assert 'with tab_entregues:_exibir_entregas()' in src
assert 'with tabs[3]:\n            _exibir_entregas()' in src
for key in (
    'key="garantia_item_"+str(p["id"])+"_"+grupo',
    'key="garantia_status_"+str(p["id"])+"_"+str(_id_escolhido)+"_"+grupo',
    'key="garantia_salvar_"+str(p["id"])+"_"+grupo',
    'key="email_retry_"+str(p["id"])+"_"+_tipo+"_"+grupo',
):
    assert key in mostrar,key
# Só o CONSULTA confirma utilização/devolução, também na aba Confirmadas.
assert 'if perfil=="CONSULTA" and p.get("estado")=="ENTREGUE" and p.get("finalidade")=="GARANTIA"' in mostrar
assert '"garantia_resultado"' in mostrar
print("MRP_GARANTIAS_ABAS_SEPARACAO_POR_ITEM_OK")
