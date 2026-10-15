"""Testes de regressao da separacao de perfis MRP; sem dados reais."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
avulsa=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
acesso=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_require_login")
avulsa_source=ast.get_source_segment(source,avulsa)
login_source=ast.get_source_segment(source,acesso)
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")

assert '"OPERADOR"' in login_source
assert 'st.session_state.get("auth_role") in {"ADMIN", "CONSULTA", "OPERADOR"}' in source

def find_if(test_snippet):
    return next(
        (n for n in ast.walk(avulsa)
         if isinstance(n,ast.If) and test_snippet in ast.unparse(n.test)),
        None
    )
def found_call(root_node, function_name):
    return any(
        isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name)
        and n.func.id==function_name
        for n in ast.walk(root_node)
    )
def contains_string(root_node, val):
    return val in ast.unparse(root_node)

# Somente CONSULTA enxerga a criacao, carrinho e botao de envio.
bloco_consulta=next(
    (node for node in ast.walk(avulsa)
     if isinstance(node,ast.If)
     and "perfil == 'CONSULTA'" in ast.unparse(node.test)
     and 'create_batch' in ast.unparse(node)),None
)
assert bloco_consulta is not None
assert contains_string(bloco_consulta,'REGISTRAR SOLICITAÇÃO')
# Formulario de tratativa acessivel exclusivamente pelo OPERADOR.
operador=find_if("perfil == 'OPERADOR'")
assert operador is not None
assert 'OPERADOR' in avulsa_source
assert 'perfil=="OPERADOR"' in avulsa_source
assert 'if tab_minhas is not None:' in avulsa_source
assert 'if perfil in {"OPERADOR","ADMIN"}:' in avulsa_source
assert 'Tratativas exclusivas do perfil OPERADOR.' in avulsa_source
assert 'with st.form("mrp_avulsa_atender"' in avulsa_source
assert '_mrp_avulsas_call("attend"' in avulsa_source
assert '_mrp_avulsas_call("reject"' in avulsa_source
assert 'linhas_separadas=separados if perfil in {"ADMIN","OPERADOR"}' in avulsa_source

# O servidor, nao apenas a interface, restringe todas as mutacoes.
assert '["ADMIN", "CONSULTA", "OPERADOR"]' in api
assert api.count('if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED", 403);')==2
assert 'if (action !== "list" && role !== "CONSULTA") return fail("CONSULTA_REQUIRED", 403);' in api
assert 'if(role==="CONSULTA")query=query.eq("criado_por",userId);' in api
assert 'materials: role === "CONSULTA" ? materials : []' in api
assert 'if (role !== "ADMIN") return fail("ADMIN_REQUIRED", 403);' in api

sql=(root/"supabase/migrations/20261015_mrp_perfil_operador.sql").read_text("utf-8")
assert "'ADMIN'::text,'CONSULTA'::text,'OPERADOR'::text" in sql
print("MRP_TRES_PERFIS_PERMISSOES_VALIDADO")
