"""Autorização em camadas: UI/servidor/banco, sem dados reais."""
import ast,runpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
v=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
login=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_require_login")
view=ast.get_source_segment(source,v)
login_src=ast.get_source_segment(source,login)
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
assert '"operador": "operador.almox@gruposetta.com"' in login_src
assert 'st.session_state.get("auth_role") in {"ADMIN", "CONSULTA", "OPERADOR"}' in source
assert 'if perfil=="CONSULTA":' in view
assert 'if perfil=="OPERADOR":' in view
assert '"GARANTIA"' in view and '"ACERTO GERENCIAL"' in view
assert '"pedido_tratar"' in view and '"garantia_resultado"' in view
assert 'role !== "OPERADOR"' in api
assert 'role!=="CONSULTA"' in api
assert 'role==="CONSULTA"' in api
assert 'materials: role === "CONSULTA" ? materials : []' in api
assert 'if(role==="CONSULTA")pedidosQuery=pedidosQuery.eq("criado_por",userId)' in api
sql=(root/"supabase/migrations/20261015_mrp_avulsas_fluxo_entrega.sql").read_text("utf-8")
assert "role='OPERADOR'" in sql and "role='CONSULTA'" in sql
print("MRP_TRES_PERFIS_PEDIDOS_OK")
