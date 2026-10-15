"""Regressao de UX e visualizacao de solicitacoes, sem chamadas de API."""
import ast
import runpy
from pathlib import Path

import pandas as pd

root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
tree=ast.parse(source)
view=next(node for node in tree.body
          if isinstance(node,ast.FunctionDef) and node.name=="_mrp_avulsas_view")
view_code=ast.get_source_segment(source,view)

for style in ("mrp-av-hero","mrp-av-steps","mrp-av-section","mrp-av-item"):
    assert style in source, style
# Segunda revisao: banner legivel e acesso rapido ao acompanhamento.
assert 'color:#ffffff!important' in source
assert '.mrp-av-meta' in source
assert 'c1,c2,c3=st.columns(3,gap="small")' in view_code
assert 'c1.metric("AGUARDANDO SEPARAÇÃO",len(pendentes))' in view_code
assert 'st.button("ATUALIZAR STATUS",key="mrp_avulsas_atualizar_status"' in view_code
assert "ADMINISTRAÇÃO · TESTAR CONEXÃO COM O TEAMS" in view_code
assert view_code.index("ADMINISTRAÇÃO · TESTAR CONEXÃO COM O TEAMS") > view_code.index("EXPORTAR TODAS AS SOLICITAÇÕES")
assert '<div class="section-band"><div class="section-band-kicker">01 · REQUISIÇÕES' not in view_code

assert "ETAPA 01 · ESCOLHA" in source
assert "ETAPA 02 · CONFERÊNCIA" in source
assert "ETAPA 03 · CONFIRMAR E ENVIAR" in source
assert "SOLICITAÇÃO PARA TRATATIVA" in view_code
assert "CONFIRMAR MATERIAL SEPARADO" in view_code
assert "RECUSAR SOLICITAÇÃO" in view_code
assert "if perfil==\"CONSULTA\":" in view_code
assert "elif perfil==\"OPERADOR\":" in view_code
assert "if tab_minhas is not None:" in view_code

# A apresentacao converte datas UTC para horario local, nao muda valores do banco.
tabela=next(n for n in ast.walk(view)
            if isinstance(n,ast.FunctionDef) and n.name=="tabela")
namespace={"pd":pd}
exec(compile(ast.Module(body=[tabela],type_ignores=[]),"tabela_avulsas.py","exec"),namespace)
rows=[{
    "id":5,
    "codigo":"00000042",
    "descricao":"MATERIAL DE TESTE",
    "quantidade":2,
    "solicitante":"Consulta",
    "status_exibicao":"ABERTA",
    "criado_em":"2026-10-15T15:25:00+00:00",
    "atendido_em":None,
    "recusado_em":None,
    "observacao_atendimento":"",
}]
visual=namespace["tabela"](rows)
assert visual.loc[0,"SOLICITADO EM"]=="15/10/2026 12:25",visual
assert visual.loc[0,"SEPARADO EM"]==""
assert visual.loc[0,"RECUSADO EM"]==""
assert visual.loc[0,"STATUS"]=="AGUARDANDO SEPARAÇÃO",visual
assert visual.loc[0,"CÓDIGO"]=="00000042"
assert visual.loc[0,"QUANTIDADE"]==2
print("MRP_SOLICITACOES_UX_LAYOUT_E_DATAS_OK")
