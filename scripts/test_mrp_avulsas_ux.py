"""Regressão de visual e acessibilidade das solicitações por pedido."""
import ast,runpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
view=next(n for n in ast.parse(source).body
          if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")
s=ast.get_source_segment(source,view)
for x in ('mrp-ped-hero','mrp-ped-section','mrp_avulsa_area_selecao',
          'mrp_avulsa_confirmacao','"✕"','"ATUALIZAR STATUS"',
          '_etapa("01"','_etapa("02"','_etapa("03"',
          'REGISTRAR SOLICITAÇÃO','Destino','ASTEC',
          'MINHAS SOLICITAÇÕES','SEPARADAS','ENTREGUES','RECUSADAS'):
    assert x in s,x
assert "max 30" not in s.lower()
assert 'maximo 30' not in s.lower()
assert 'max_value=round(_room,3)' in s
assert 'st.container(key="mrp_avulsa_area_selecao",border=True)' in s
assert 'st.container(key="mrp_avulsa_confirmacao",border=True)' in s
assert 'st.form("mrp_avulsas_enviar_lote",enter_to_submit=False)' in s
assert '.tz_convert("America/Sao_Paulo")' in s
assert 'email' in s.lower()
print("MRP_AVULSAS_UX_FLUXO_VALIDADO")
