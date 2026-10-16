"""Regressão do indicador de publicação MRP vs. disponibilidade das cinco bases."""
import ast
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[1]
codigo=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
arvore=ast.parse(codigo)
assert 'MRP DESATUALIZADO · REPROCESSAR' in codigo
assert 'MRP AGUARDA BASES ATUALIZADAS' in codigo
assert 'BASES EM ATUALIZAÇÃO' in codigo
assert 'mrp_reprocess_stale_report' in codigo
assert '"_mrp_sidebar_page"]="MRP ATUAL"' in codigo
assert '"_mrp_force_central_refresh"]=True' in codigo
assert 'if _mrp_output_stale and _mrp_base_ok == _mrp_base_total:' in codigo

# A disponibilidade de 5/5 NÃO prova que o relatório derivado está atual.
estado=next(n for n in ast.walk(arvore)
    if isinstance(n,ast.If)
    and ast.unparse(n.test).replace(" ","")=="_mrp_output_staleand_mrp_base_ok==_mrp_base_total")
assert any(isinstance(n,ast.AugAssign) and
    isinstance(n.target,ast.Name) and n.target.id=="_mrp_meta_text"
    for n in ast.walk(estado))
# O comando somente navega para a aba que já calcula o MRP.
botoes=[n for n in ast.walk(arvore)
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
    and n.func.attr=="button"
    and any(kw.arg=="key" and isinstance(kw.value,ast.Constant)
      and kw.value.value=="mrp_reprocess_stale_report" for kw in n.keywords)]
assert len(botoes)==1
assert "REPROCESSAR RELATÓRIO MRP COM AS BASES ATUAIS" in codigo
print("MRP_STATUS_PUBLICACAO_FRESCOR_E_ACAO_OK")
