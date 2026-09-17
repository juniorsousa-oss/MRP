from pathlib import Path
from mrp_entrega_patch import ENTREGA_PATCH
from mrp_layout_patch import LAYOUT_PATCH
from mrp_compra_tctp_patch import COMPRA_TCTP_PATCH
from mrp_filtros_patch import FILTROS_PATCH
from mrp_comparativo_patch import COMPARATIVO_PATCH
from mrp_login_patch import LOGIN_PATCH
from mrp_login_spacing_patch import LOGIN_SPACING_PATCH

# Mantém toda a lógica funcional validada no runtime estável e aplica somente
# a persistência/detalhamento das OPs de produção interna e o status de entrega.
_runtime_path = Path(__file__).with_name("app_mrp_runtime.py")
_runtime_source = _runtime_path.read_text(encoding="utf-8")

_exec_anchor = 'exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
if _exec_anchor not in _runtime_source:
    raise RuntimeError("Ponto de execução do runtime do MRP não encontrado.")

_producao_patch = r"""
# =========================================================
# PRODUÇÃO INTERNA — PERSISTÊNCIA E DETALHE NA CONSULTA
# =========================================================
_old_sig = 'def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):'
_new_sig = 'def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None,fabricacao=None):'
if _old_sig not in _source:
    raise RuntimeError("Assinatura de save_snapshot não encontrada para produção interna.")
_source = _source.replace(_old_sig, _new_sig, 1)

_old_payload = '\"compra_mrp\":records(compra_mrp),\"compras\":records(compras)}'
_new_payload = '\"compra_mrp\":records(compra_mrp),\"compras\":records(compras),\"fabricacao\":records(fabricacao)}'
if _old_payload not in _source:
    raise RuntimeError("Payload de snapshot não encontrado para produção interna.")
_source = _source.replace(_old_payload, _new_payload, 1)

_old_call = 'save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp,cp)'
_new_call = 'save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp,cp,fab_det)'
if _old_call not in _source:
    raise RuntimeError("Chamada de save_snapshot não encontrada para produção interna.")
_source = _source.replace(_old_call, _new_call, 1)

_source = _source.replace(
    'MRP-SNAPSHOT-V3-COMPRAS-PERIODO',
    'MRP-SNAPSHOT-V4-FABRICACAO',
    1,
)

_old_load = '    compras = snapshot_df(snap, \"compras\").copy()\n'
_new_load = '    compras = snapshot_df(snap, \"compras\").copy()\n    fabricacao = snapshot_df(snap, \"fabricacao\").copy()\n'
if _old_load not in _source:
    raise RuntimeError("Carga do snapshot na consulta não encontrada para produção interna.")
_source = _source.replace(_old_load, _new_load, 1)

_old_detail_anchor = '''                    st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")

    with tab_projeto:'''
_new_detail = '''                    st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")

                d_fab = pd.DataFrame()
                if not fabricacao.empty and "Código Produto" in fabricacao.columns:
                    _fab_code = fabricacao["Código Produto"].astype(str).str.replace(".0", "", regex=False)
                    d_fab = fabricacao[_fab_code == selecionado].copy()

                if not d_fab.empty:
                    if "ORDEM DE PRODUÇÃO" in d_fab.columns:
                        d_fab["ORDEM DE PRODUÇÃO"] = d_fab["ORDEM DE PRODUÇÃO"].fillna("").astype(str).str.replace(".0", "", regex=False)
                    if "Código Produto" in d_fab.columns:
                        d_fab["Código Produto"] = d_fab["Código Produto"].fillna("").astype(str).str.replace(".0", "", regex=False)
                    if "Semana Entrega" in d_fab.columns:
                        d_fab["Período da Semana"] = pd.to_numeric(d_fab["Semana Entrega"], errors="coerce").apply(periodo_semana)
                    else:
                        d_fab["Período da Semana"] = ""
                    fab_cols = ["ORDEM DE PRODUÇÃO", "Código Produto", "Semana Entrega", "Período da Semana", "Quantidade"]
                    for c in fab_cols:
                        if c not in d_fab.columns:
                            d_fab[c] = ""
                    st.markdown("**PRODUÇÃO INTERNA — OPs**")
                    st.caption("Ordens de produção vinculadas ao material selecionado. Cada OP representa 1 peça em fabricação.")
                    st.dataframe(d_fab[fab_cols], use_container_width=True, hide_index=True, column_order=fab_cols)
                else:
                    _mg_sel = mg[mg["Código"].astype(str).str.replace(".0", "", regex=False) == selecionado].copy() if "Código" in mg.columns else pd.DataFrame()
                    _produzindo = pd.to_numeric(_mg_sel.get("Produzindo", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not _mg_sel.empty else 0
                    if _produzindo > 0:
                        st.markdown("**PRODUÇÃO INTERNA — OPs**")
                        st.info("Este MRP foi salvo antes do detalhamento das OPs ser incorporado ao histórico. Processe novamente as 5 bases para gravar e exibir as ordens de produção deste material.")

    with tab_projeto:'''
if _old_detail_anchor not in _source:
    raise RuntimeError("Ponto do detalhamento de produção interna não encontrado.")
_source = _source.replace(_old_detail_anchor, _new_detail, 1)

_old_export = '        \"Compras\": compras,\n    }'
_new_export = '        \"Compras\": compras,\n        \"Fabricacao\": fabricacao,\n    }'
if _old_export in _source:
    _source = _source.replace(_old_export, _new_export, 1)
"""

_runtime_source = _runtime_source.replace(
    _exec_anchor,
    _producao_patch + "\n" + ENTREGA_PATCH + "\n" + LAYOUT_PATCH + "\n" + COMPRA_TCTP_PATCH + "\n" + FILTROS_PATCH + "\n" + COMPARATIVO_PATCH + "\n" + LOGIN_PATCH + "\n" + LOGIN_SPACING_PATCH + "\n" + _exec_anchor,
    1,
)

exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())