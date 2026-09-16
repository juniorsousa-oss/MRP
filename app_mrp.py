from pathlib import Path

# Camada leve de desempenho. A lógica funcional validada permanece preservada em
# app_mrp_runtime.py; aqui apenas evitamos leituras, consultas e exportações
# repetidas a cada rerun do Streamlit.
_runtime_path = Path(__file__).with_name("app_mrp_runtime.py")
_runtime_source = _runtime_path.read_text(encoding="utf-8")

# A carga de tratativas é compartilhada e muda pouco. Cache curto evita duas ou
# mais consultas ao Supabase em cada clique/filtro, mas é invalidado ao salvar.
_runtime_source = _runtime_source.replace(
    "def _carregar_tratativas_salvas():\n",
    "@st.cache_data(ttl=45, show_spinner=False)\ndef _carregar_tratativas_salvas():\n",
    1,
)
_runtime_source = _runtime_source.replace(
    "    return len(base)\n\ndef render_tratativa_projetos():",
    "    _carregar_tratativas_salvas.clear()\n    return len(base)\n\ndef render_tratativa_projetos():",
    1,
)

_exec_anchor = 'exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
if _exec_anchor not in _runtime_source:
    raise RuntimeError("Ponto de execução do runtime do MRP não encontrado.")

_performance_patch = r'''
# =========================================================
# DESEMPENHO — CACHE E GERAÇÃO SOB DEMANDA
# =========================================================
# Excel é a operação mais cara do app. As cinco bases só voltam a ser lidas se
# seus bytes realmente mudarem.
_source = _source.replace(
    "def load_sources(cb,eb,gb,pb,mb):\n",
    "@st.cache_data(show_spinner=False, max_entries=4)\ndef load_sources(cb,eb,gb,pb,mb):\n",
    1,
)

# Configuração visual é comum a todos e não precisa consultar o banco em todo
# filtro/seleção.
_source = _source.replace(
    "def _config_get():\n",
    "@st.cache_data(ttl=300, show_spinner=False)\ndef _config_get():\n",
    1,
)
_source = _source.replace(
    '                _config_save(new_cfg)\n                st.session_state["ui_config"] = _config_get()\n',
    '                _config_save(new_cfg)\n                _config_get.clear()\n                st.session_state["ui_config"] = _config_get()\n',
    1,
)

# Arquivos de exportação iguais são reutilizados em vez de reconstruídos.
_source = _source.replace(
    "def excel_bytes(sheets):\n",
    "@st.cache_data(show_spinner=False, max_entries=8)\ndef excel_bytes(sheets):\n",
    1,
)
_source = _source.replace(
    "def csv_bytes(df):\n",
    "@st.cache_data(show_spinner=False, max_entries=16)\ndef csv_bytes(df):\n",
    1,
)
_source = _source.replace(
    "def zip_bytes(files):\n",
    "@st.cache_data(show_spinner=False, max_entries=8)\ndef zip_bytes(files):\n",
    1,
)

# Histórico/comparativo é pesado e não deve ser processado automaticamente em
# cada rerun. Só é montado quando o usuário solicitar.
_history_helper_anchor = 'def render_consulta_view():'
_history_helper = '''def render_mrp_history_lazy():
    st.divider()
    if st.toggle("CARREGAR HISTÓRICO E COMPARATIVO", value=False, key="mrp_history_lazy_toggle"):
        render_mrp_history()

def render_consulta_view():'''
_source = _source.replace(_history_helper_anchor, _history_helper, 1)
_source = _source.replace('                render_mrp_history()\n', '                render_mrp_history_lazy()\n', 1)
_source = _source.replace('    render_mrp_history()\n\n# trigger-final-2', '    render_mrp_history_lazy()\n\n# trigger-final-2', 1)

# Na consulta, Excel/ZIP não são mais montados em todo clique. O usuário prepara
# os downloads apenas quando realmente precisar deles.
_consulta_export_pattern = re.compile(
    r'    st\.markdown\("### Exportação de relatórios"\)\n'
    r'    sheets = \{.*?'
    r'    c4\.download_button\("BAIXAR COMPRA MRP".*?\n\n\ndef load_sources',
    re.S,
)
_consulta_export_replacement = '''    st.markdown("### Exportação de relatórios")
    st.caption("Os arquivos são preparados sob demanda para manter a consulta rápida.")
    sheets = {
        "MRP_Geral": mg,
        "Projecao_Semanal": proj,
        "Demanda_Projeto": dem,
        "Compra_MRP": comp,
        "Compras": compras,
    }
    _consulta_snapshot_id = int(snap.get("id") or 0)
    if st.button("PREPARAR ARQUIVOS PARA DOWNLOAD", use_container_width=True, key="consulta_prepare_exports"):
        with st.spinner("Preparando arquivos de exportação..."):
            st.session_state["_consulta_exports"] = {
                "snapshot_id": _consulta_snapshot_id,
                "excel": excel_bytes(sheets),
                "zip": zip_bytes({f"{k}.csv": csv_bytes(v) for k,v in sheets.items()}),
                "geral_csv": csv_bytes(mg),
                "compra_excel": excel_bytes({"Compra_MRP": comp}),
            }
    _consulta_exports = st.session_state.get("_consulta_exports") or {}
    if _consulta_exports.get("snapshot_id") == _consulta_snapshot_id:
        c1, c2, c3, c4 = st.columns(4)
        c1.download_button("BAIXAR TODOS — EXCEL", data=_consulta_exports["excel"], file_name="MRP_Consulta.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        c2.download_button("BAIXAR TODOS — ZIP/CSV", data=_consulta_exports["zip"], file_name="MRP_Consulta_CSV.zip", mime="application/zip", use_container_width=True)
        c3.download_button("BAIXAR MRP GERAL — CSV", data=_consulta_exports["geral_csv"], file_name="MRP_Geral.csv", mime="text/csv", use_container_width=True)
        c4.download_button("BAIXAR COMPRA MRP", data=_consulta_exports["compra_excel"], file_name="Compra_MRP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


def load_sources'''
_source, _consulta_export_count = _consulta_export_pattern.subn(lambda _m: _consulta_export_replacement, _source, count=1)
if _consulta_export_count != 1:
    raise RuntimeError("Bloco de exportação da consulta não encontrado para otimização.")

# O mesmo vale para o processamento ADMIN: gerar Excel/ZIP só quando solicitado.
_admin_export_pattern = re.compile(
    r'st\.divider\(\); st\.subheader\(UI_CONFIG\["section_export_title"\]\)\n'
    r'if UI_CONFIG\.get\("section_export_description"\):.*?'
    r'with b4: st\.download_button\("BAIXAR COMPRA MRP".*?\n'
    r'(?=if len\(compras_mrp\):)',
    re.S,
)
_admin_export_replacement = '''st.divider(); st.subheader(UI_CONFIG["section_export_title"])
if UI_CONFIG.get("section_export_description"):
    st.caption(UI_CONFIG["section_export_description"])
compras_mrp_export=normalizar_compra_mrp(compras_mrp)
export_macro=macro[macro_cols].sort_values(["Status","Código"],key=lambda s:s.map({"CRIAR S.C.":0,"OK":1}).fillna(2) if s.name=="Status" else s).copy(); export_proj=proj.copy()
if len(export_proj): export_proj["Período da Semana"]=export_proj["Semana"].apply(periodo_semana)
export_proj=export_proj[["Código","Descrição","Tipo","Semana","Período da Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]].sort_values(["Código","Semana"])
sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"Tratativas_Projetos":tratativas_projeto,"Compra_MRP":compras_mrp_export,"Compras":cp,"Fabricacao":fab_det,"Cadastro_Base":cad}
_admin_export_sig=hashlib.sha256(
    b"MRP-EXPORT-V2"+b"".join([f.getvalue() for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]])+
    json.dumps(tratativas_projeto[["Projeto","OBS"]].sort_values("Projeto").to_dict("records"),ensure_ascii=False,sort_keys=True).encode("utf-8")
).hexdigest()
st.caption("Os arquivos de exportação são preparados somente quando solicitados.")
if st.button("PREPARAR ARQUIVOS PARA DOWNLOAD", use_container_width=True, key="admin_prepare_exports"):
    with st.spinner("Preparando arquivos de exportação..."):
        st.session_state["_admin_exports"]={
            "sig":_admin_export_sig,
            "excel":excel_bytes(sheets),
            "zip":zip_bytes({name+".csv":csv_bytes(df) for name,df in sheets.items()}),
            "geral_csv":csv_bytes(export_macro),
            "compra_excel":excel_bytes({"Compra_MRP":compras_mrp_export}),
        }
_admin_exports=st.session_state.get("_admin_exports") or {}
if _admin_exports.get("sig")==_admin_export_sig:
    b1,b2,b3,b4=st.columns(4)
    with b1: st.download_button("BAIXAR TODOS — EXCEL",_admin_exports["excel"],"MRP_Relatorios_Completos.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    with b2: st.download_button("BAIXAR TODOS — ZIP/CSV",_admin_exports["zip"],"MRP_Relatorios_Completos.zip","application/zip",use_container_width=True)
    with b3: st.download_button("BAIXAR MRP GERAL — CSV",_admin_exports["geral_csv"],"MRP_Geral.csv","text/csv",use_container_width=True)
    with b4: st.download_button("BAIXAR COMPRA MRP",_admin_exports["compra_excel"],"Compra_MRP.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
'''
_source, _admin_export_count = _admin_export_pattern.subn(lambda _m: _admin_export_replacement, _source, count=1)
if _admin_export_count != 1:
    raise RuntimeError("Bloco de exportação ADMIN não encontrado para otimização.")
'''

_runtime_source = _runtime_source.replace(
    _exec_anchor,
    _performance_patch + "\n" + _exec_anchor,
    1,
)

exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())
