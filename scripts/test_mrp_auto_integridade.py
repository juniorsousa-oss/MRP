"""Regressão: informações nunca desaparecem durante reprocessamento MRP."""
from pathlib import Path
import pandas as pd
from mrp_integridade_compra import (
    codigo_canonico, descricoes_por_codigo, preencher_descricoes_compra,
)

assert codigo_canonico(50590)=="00050590"
assert codigo_canonico("50590.0")=="00050590"

compra=pd.DataFrame({"produto":["00050590","00070001"],"Qtd":[3,2]})
foto=pd.DataFrame({"Código":[50590,70001],"Descrição":[
    "TC 15KV 100/5 25 VA","MATERIAL DE TESTE COM DESCRIÇÃO",
]})
res,sem=preencher_descricoes_compra(compra,foto)
assert len(res)==2 and not sem
assert res.loc[0,"Descrição"]=="TC 15KV 100/5 25 VA"
assert res.loc[1,"Descrição"]=="MATERIAL DE TESTE COM DESCRIÇÃO"

cad=pd.DataFrame({"Código":["00050590"],"Descrição":["TC 15KV 100/5 25 VA"]})
valido,sem=preencher_descricoes_compra(compra.iloc[:1],cad)
assert not sem and valido.iloc[0]["Descrição"]=="TC 15KV 100/5 25 VA"
ausente,sem=preencher_descricoes_compra(compra,None)
assert sem==["00050590","00070001"]
assert len(ausente)==len(compra)
assert ausente["Descrição"].str.contains("CONFERIR CADASTRO").all()

root=Path(__file__).resolve().parents[1]
patch=(root/"mrp_central_data_patch.py").read_text("utf-8")
central=(root/"central_mrp_data.py").read_text("utf-8")
compra_patch=(root/"mrp_compra_validacao_patch.py").read_text("utf-8")
filtros=(root/"mrp_filtros_tratativas_patch.py").read_text("utf-8")

for part in (
    'run_every="60s"',
    "_mrp_estado = _central_mrp.inspect_mrp_state(",
    '_central_bundle["output_meta"] = _mrp_estado.get("output_meta")',
    "A versão íntegra anterior continua no sistema.",
    "render_consulta_view()",
):
    assert part in patch,part
for part in (
    'latest.get("signature") != bundle.get("signature")',
    'latest.get("state_token") != bundle.get("state_token")',
    'frame.empty',
    "As fontes mudaram durante a leitura",
):
    assert part in central,part
assert 'render_validacao_compra_mrp(comp,"consulta",mg)' in compra_patch
assert 'preencher_descricoes_compra(por_produto, cad)' in compra_patch
assert 'if _sem_descricao:' in compra_patch
assert 'st.session_state.pop(_key,None)' not in filtros

print("MRP_INTEGRIDADE_DESCRICOES_E_REFRESH_OK")
