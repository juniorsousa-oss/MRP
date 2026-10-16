"""Garantias: aguardando retorno -> utilizado/devolvido; toast temporário."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
view=next(n for n in tree.body
          if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
src=ast.get_source_segment(source,view)
helpers={n.name:n for n in view.body if isinstance(n,ast.FunctionDef)}
assert "_condicao_garantia" in helpers
assert "_condicao_garantia_relatorio" in helpers
ns={}
exec(compile(ast.fix_missing_locations(ast.Module(
    body=[helpers["_condicao_garantia"]],type_ignores=[]
)),"<test-garantia>","exec"),ns)
status=ns["_condicao_garantia"]
entregue={"estado":"ENTREGUE","finalidade":"GARANTIA"}
for raw,expected in [
    (None,"AGUARDANDO RETORNO"),
    ("AGUARDANDO_RETORNO","AGUARDANDO RETORNO"),
    ("UTILIZADO","UTILIZADO"),
    ("DEVOLVIDO","DEVOLVIDO"),
]:
    assert status(entregue,{"destino_garantia":raw})==expected
assert status({"estado":"SEPARADA","finalidade":"GARANTIA"},
              {"destino_garantia":None})==""
assert status({"estado":"ENTREGUE","finalidade":"ACERTO_GERENCIAL"},
              {"destino_garantia":None})==""
exec(compile(ast.fix_missing_locations(ast.Module(
    body=[helpers["_condicao_garantia_relatorio"]],type_ignores=[]
)),"<test-garantia-relatorio>","exec"),ns)
report_status=ns["_condicao_garantia_relatorio"]
assert report_status(entregue,{"destino_garantia":None})=="AGUARDANDO RETORNO"
assert report_status({"finalidade":"GARANTIA","estado":"SEPARADA"},{} )=="AGUARDANDO ENTREGA"
assert report_status({"finalidade":"ACERTO_GERENCIAL","estado":"ENTREGUE"},{} )=="NA"

assert '\"CONDIÇÃO GARANTIA\":_condicao_garantia_relatorio(p,filho)' in src
assert '"CONDIÇÃO GARANTIA":_condicao_garantia_relatorio(_pedido,_item)' in src
assert '\"AGUARDANDO RETORNO\",\"AGUARDANDO_RETORNO\"' in src
assert '\"UTILIZADO\",\"UTILIZADO\"' in src
assert '\"DEVOLVIDO\",\"DEVOLVIDO\"' in src
assert '\"id\":_id_escolhido,\"resultado\":_codigo_resultado' in src
assert '\"garantia_resultado\"' in src
assert 'st.toast(_garantia_aviso,icon="✅")' in src
assert 'st.toast(_retorno_operador,icon="⚠️" if _aviso_email else "✅")' in src
assert 'st.success(_retorno_operador)' not in src
assert 'st.session_state.pop("_mrp_avulsas_operador_retorno",None)' in src
assert 'st.session_state.pop("_mrp_garantia_notificacao",None)' in src

api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
assert '!["AGUARDANDO_RETORNO","UTILIZADO","DEVOLVIDO"].includes(resultado)' in api
sql=(root/"supabase/migrations/20261016_mrp_garantia_aguardando_retorno.sql").read_text("utf-8")
for fragment in (
    "mrp_avulsa_ao_entregar_garantia",
    "new.estado='ENTREGUE'",
    "new.finalidade='GARANTIA'",
    "destino_garantia='AGUARDANDO_RETORNO'",
    "destino_garantia is null",
    "'AGUARDANDO_RETORNO','UTILIZADO','DEVOLVIDO'",
    "v_registro.criado_por<>p_actor",
    "v_registro.estado<>'ENTREGUE'",
    "role='CONSULTA'",
    "'GARANTIA_'||p_resultado",
):
    assert fragment in sql,fragment
print("MRP_GARANTIA_CONDICAO_E_TOAST_TEMPORARIO_OK")
