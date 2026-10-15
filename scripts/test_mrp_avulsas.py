"""Teste de regressão do fluxo por pedido, sem alterar dados de produção."""
import ast,runpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
assert "_mrp_avulsas_view" in funcs and "_mrp_avulsas_call" in funcs
view=ast.get_source_segment(source,funcs["_mrp_avulsas_view"])
for token in (
    'mrp_avulsa_area_selecao','mrp_avulsa_confirmacao',
    '_etapa("01"','_etapa("02"','_etapa("03"',
    'st.form("mrp_avulsa_criar"','st.form("mrp_avulsas_enviar_lote"',
    '"GARANTIA"','"ACERTO GERENCIAL"','"TRANSFERÊNCIA ENTRE FILIAL"',
    '"E-MAIL DO SOLICITANTE"','"CR"','"APROVADOR"','"PSY OU PSYs"',
    ''ASTEC'','"REGISTRAR SOLICITAÇÃO"',
    '"✕"','"LIMPAR LISTA"','"create_batch"',
    '"pedido_tratar"','"SEPARAR"','"RECUSAR"','"ENTREGAR"',
    '"garantia_resultado"','"UTILIZADO"','"DEVOLVIDO"',
    '"RECUSADAS ("','"ENTREGUES ("','"SEPARADAS ("',
    '"ATUALIZAR STATUS"',
):assert token in view,token
# Seleção independente do formulário; a troca de material atualiza o limite.
sel=next(n for n in ast.walk(funcs["_mrp_avulsas_view"])
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
    and n.func.attr=="selectbox" and n.args
    and isinstance(n.args[0],ast.Constant)
    and n.args[0].value=="MATERIAL"
    and any(kw.arg=="key" and isinstance(kw.value,ast.Constant)
        and kw.value.value=="mrp_avulsa_material_selecionado"
        for kw in n.keywords))
for node in ast.walk(funcs["_mrp_avulsas_view"]):
    if isinstance(node,ast.With) and any(
        isinstance(z.context_expr,ast.Call) and isinstance(z.context_expr.func,ast.Attribute)
        and z.context_expr.func.attr=="form" for z in node.items):
        assert sel not in ast.walk(node)
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
sql=(root/"supabase/migrations/20261015_mrp_avulsas_fluxo_entrega.sql").read_text("utf-8")
for item in ("mrp_avulsa_criar_lote_v2_seguro","mrp_avulsa_pedido_tratar_seguro",
             "mrp_avulsa_garantia_resultado_seguro"):
    assert item in api and item in sql,item
assert 'if(role==="CONSULTA")query=query.eq("criado_por",userId);' in api
assert 'availableAfterReservations(item.limite' in api
assert 'r.status === "ABERTA"' in api and 'r.status === "ATENDIDA"' in api
assert 'mrp_avulsa_criar_lote_seguro' in sql # reutiliza trava e auditoria originais
print("MRP_AVULSAS_PEDIDOS_FLOW_OK")
