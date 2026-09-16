from __future__ import annotations

EXEC_ANCHOR = 'exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'

PERFORMANCE_PATCH = r"""
# =========================================================
# DESEMPENHO — OTIMIZAÇÕES SEGURAS
# =========================================================
def _cache_source_function(signature, decorated_signature):
    global _source
    if decorated_signature in _source:
        return
    if signature in _source:
        _source = _source.replace(signature, decorated_signature, 1)

# As cinco planilhas só são relidas quando os bytes realmente mudam.
_cache_source_function(
    "def load_sources(cb,eb,gb,pb,mb):",
    "@st.cache_data(show_spinner=False, max_entries=4)\\ndef load_sources(cb,eb,gb,pb,mb):",
)

# Exportações deixam de ser reconstruídas em todo clique/filtro.
_cache_source_function(
    "def excel_bytes(sheets):",
    "@st.cache_data(show_spinner=False, max_entries=12)\\ndef excel_bytes(sheets):",
)
_cache_source_function(
    "def csv_bytes(df):",
    "@st.cache_data(show_spinner=False, max_entries=24)\\ndef csv_bytes(df):",
)
_cache_source_function(
    "def zip_bytes(files):",
    "@st.cache_data(show_spinner=False, max_entries=12)\\ndef zip_bytes(files):",
)

# Configuração visual é compartilhada e muda pouco.
_cache_source_function(
    "def _config_get():",
    "@st.cache_data(ttl=300, show_spinner=False)\\ndef _config_get():",
)
_cfg_save_old = '                _config_save(new_cfg)\\n                st.session_state["ui_config"] = _config_get()\\n'
_cfg_save_new = '                _config_save(new_cfg)\\n                _config_get.clear()\\n                st.session_state["ui_config"] = _config_get()\\n'
if _cfg_save_old in _source:
    _source = _source.replace(_cfg_save_old, _cfg_save_new, 1)

# Tratativas são compartilhadas. Cache curto reduz chamadas ao Supabase.
_cache_source_function(
    "def _carregar_tratativas_salvas():",
    "@st.cache_data(ttl=45, show_spinner=False)\\ndef _carregar_tratativas_salvas():",
)
_trat_old = '    return len(base)\\n\\ndef render_tratativa_projetos():'
_trat_new = '    _carregar_tratativas_salvas.clear()\\n    return len(base)\\n\\ndef render_tratativa_projetos():'
if _trat_old in _source:
    _source = _source.replace(_trat_old, _trat_new, 1)

# Histórico/comparativo era recalculado em todo rerun do ADMIN.
# Agora só é executado quando o usuário realmente solicitar.
_history_marker = 'def render_consulta_view():'
if 'def render_mrp_history_lazy():' not in _source and _history_marker in _source:
    _history_helper = '''def render_mrp_history_lazy():
    carregar = st.toggle(
        "CARREGAR HISTÓRICO E COMPARATIVO",
        value=False,
        key="mrp_carregar_historico",
        help="Ative somente quando precisar consultar ou comparar MRP anteriores.",
    )
    if carregar:
        render_mrp_history()
    else:
        st.caption("Histórico e comparativo em espera para manter a navegação rápida.")

'''
    _source = _source.replace(_history_marker, _history_helper + _history_marker, 1)

_source = _source.replace(
    '                render_mrp_history()\\n',
    '                render_mrp_history_lazy()\\n',
    1,
)
_source = _source.replace(
    'if st.session_state.get("auth_role") == "ADMIN":\\n    render_mrp_history()\\n\\n# trigger-final-2',
    'if st.session_state.get("auth_role") == "ADMIN":\\n    render_mrp_history_lazy()\\n\\n# trigger-final-2',
    1,
)
"""

PRODUCTION_PATCH = r"""
# =========================================================
# PRODUÇÃO INTERNA — PERSISTÊNCIA E DETALHE NA CONSULTA
# =========================================================
_old_sig = 'def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):'
_new_sig = 'def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None,fabricacao=None):'
if _old_sig not in _source:
    raise RuntimeError("Assinatura de save_snapshot não encontrada para produção interna.")
_source = _source.replace(_old_sig, _new_sig, 1)

_old_payload = '"compra_mrp":records(compra_mrp),"compras":records(compras)}'
_new_payload = '"compra_mrp":records(compra_mrp),"compras":records(compras),"fabricacao":records(fabricacao)}'
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

_old_load = '    compras = snapshot_df(snap, "compras").copy()\\n'
_new_load = '    compras = snapshot_df(snap, "compras").copy()\\n    fabricacao = snapshot_df(snap, "fabricacao").copy()\\n'
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

_old_export = '        "Compras": compras,\\n    }'
_new_export = '        "Compras": compras,\\n        "Fabricacao": fabricacao,\\n    }'
if _old_export in _source:
    _source = _source.replace(_old_export, _new_export, 1)
"""


def patch_runtime_source(runtime_source: str) -> str:
    if EXEC_ANCHOR not in runtime_source:
        raise RuntimeError("Ponto de execução do runtime do MRP não encontrado.")
    injected = PERFORMANCE_PATCH + "\n" + PRODUCTION_PATCH + "\n" + EXEC_ANCHOR
    return runtime_source.replace(EXEC_ANCHOR, injected, 1)
