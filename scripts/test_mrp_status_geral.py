"""Regressão do indicador de publicação MRP vs. disponibilidade das cinco bases."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
codigo=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
arvore=ast.parse(codigo)
assert 'MRP desatualizado · reprocessar' in codigo
assert 'MRP aguarda bases atualizadas' in codigo
assert 'Bases em atualização' in codigo
assert 'mrp_reprocess_stale_report' in codigo
assert '"_mrp_sidebar_page"]="MRP ATUAL"' in codigo
assert '"_mrp_force_central_refresh"]=True' in codigo
assert 'if _mrp_output_stale and _mrp_base_ok == _mrp_base_total:' in codigo
assert 'st.session_state["_mrp_output_meta"]=_mrp_output_meta' in codigo
assert 'st.session_state["_mrp_central_bundle"]=_central_bundle' in codigo
assert 'if _mrp_publish_result.get("changed"):' in codigo
assert '_central_mrp.clear_state_cache()' in codigo
assert '_mrp_status_refresh_token' in codigo
# A atualização visual só ocorre após nova publicação: sem mudança,
# o resultado reaproveitado não deve causar rerun em loop.

# A disponibilidade de 5/5 NÃO prova que o relatório derivado está atual.
estado=next(n for n in ast.walk(arvore)
    if isinstance(n,ast.If)
    and ast.unparse(n.test).replace(" ","")=="_mrp_output_staleand_mrp_base_ok==_mrp_base_total")
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
    and ast.unparse(n.func)=="_mrp_alertas.append"
    for n in ast.walk(estado))
assert "registros=_mrp_rows_text,alertas=_mrp_alertas" in codigo
# O comando somente navega para a aba que já calcula o MRP.
botoes=[n for n in ast.walk(arvore)
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
    and n.func.attr=="button"
    and any(kw.arg=="key" and isinstance(kw.value,ast.Constant)
      and kw.value.value=="mrp_reprocess_stale_report" for kw in n.keywords)]
assert len(botoes)==1
assert "REPROCESSAR RELATÓRIO MRP COM AS BASES ATUAIS" in codigo
print("MRP_STATUS_PUBLICACAO_FRESCOR_E_ACAO_OK")
