"""Garante que o OPERADOR pode separar e entregar por S.A.; sem escrita em producao."""
import ast,runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
view=next(node for node in ast.parse(source).body
          if isinstance(node,ast.FunctionDef) and node.name=="_mrp_avulsas_view")
s=ast.get_source_segment(source,view)
# Os botoes ficam dentro do proprio expansor da SA, sem formularios ocultos ao final.
for required in (
    'if perfil=="OPERADOR" and p.get("estado")=="PENDENTE":',
    'if perfil=="OPERADOR" and p.get("estado")=="SEPARADA":',
    '"mrp_avulsa_atender_"+str(p["id"])',
    '"mrp_avulsa_entregar_"+str(p["id"])',
    '"CONFIRMAR MATERIAL SEPARADO"',
    '"RECUSAR SOLICITAÇÃO"',
    '"CONFIRMAR ENTREGA"',
    '"psys":_psys.strip()',
    '"cr":_cr.strip()',
    '"aprovador":_aprovador.strip()',
    'st.session_state["_mrp_avulsas_operador_retorno"]',
):
    assert required in s,required
assert 'if p.get("finalidade")=="GARANTIA":' in s
assert 'elif p.get("finalidade")=="ACERTO_GERENCIAL":' in s
assert 'len(_psys.strip())<2' in s
assert 'not _cr.strip()' in s

# Verificar que cada formulario foi colocado na funcao que renderiza os detalhes,
# e não na barra de acompanhamento da fila.
mostrar=next(n for n in view.body
    if isinstance(n,ast.FunctionDef) and n.name=="_mostrar_pedidos")
ms=ast.get_source_segment(source,mostrar)
assert '"mrp_avulsa_atender_"+str(p["id"])' in ms
assert '"mrp_avulsa_entregar_"+str(p["id"])' in ms
assert 'if perfil=="OPERADOR"' in ms
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
assert 'if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED",403)' in api
assert '"mrp_avulsa_entregar_com_custos_seguro"' in api
assert 'custosEntrega.valorPorCodigo.get(String(item.codigo)) ?? 0' in api
assert '"mrp_avulsa_pedido_tratar_seguro"' in api
assert 'p_precos:precosEntrega' in api

migration=(root/"supabase/migrations/20261016_mrp_regularizar_pedidos_legados_operador.sql").read_text("utf-8")
assert "p.numero in (2,3)" in migration
assert "p.numero=1" in migration
assert "i.status <> 'ABERTA'" in migration
assert "i.status <> 'ATENDIDA'" in migration
assert "estado='SEPARADA'" in migration
assert "estado='PENDENTE'" in migration
assert 'separado_em=(select max(i.atendido_em)' in migration

custos=(root/"supabase/migrations/20261016_mrp_entrega_referencia_custo_legado.sql").read_text("utf-8")
assert "i.valor_unitario_ref is null" in custos
assert "v_pedido.estado<>'SEPARADA'" in custos
assert "role='OPERADOR'" in custos
assert "INFORME_CR_E_APROVADOR_ANTES_DA_ENTREGA" in custos
assert "INFORME_OS_PSYS_ANTES_DA_ENTREGA" in custos
assert "p_precos -> i.codigo" in custos
assert "mrp_avulsa_pedido_tratar_seguro" in custos
print("MRP_OPERADOR_SEPARAR_ENTREGAR_LEGADOS_E_CUSTOS_OK")
