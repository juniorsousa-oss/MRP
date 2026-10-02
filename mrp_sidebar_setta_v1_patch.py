SIDEBAR_SETTA_V1_PATCH = r'''
# =========================================================
# SIDEBAR SETTA V1 — PADRÃO VALIDADO NO CONVERSOR MRP
# =========================================================

_sidebar_start = _source.find('with st.sidebar:\n    st.markdown(\n        \'<div class="sidebar-brand">\'')
_sidebar_end = _source.find('if st.session_state.get("auth_role") == "CONSULTA":', _sidebar_start)
if _sidebar_start < 0 or _sidebar_end < 0:
    raise RuntimeError("Sidebar central do MRP não encontrada para aplicar SIDEBAR SETTA V1.")

_sidebar_v1 = r"""_mrp_role=st.session_state.get("auth_role")
_mrp_use_manual=False
_central_bundle={}
usuario_mrp=st.session_state.get("auth_nome", "")
_mrp_central_error=""

# Navegação HTML controlada por query param.
_mrp_nav_key=str(st.query_params.get("nav") or "mrp-atual").strip().lower()
if _mrp_nav_key not in {"mrp-atual","configuracoes"}:
    _mrp_nav_key="mrp-atual"

if str(st.query_params.get("logout") or "") == "1":
    try:
        st.query_params.clear()
    except Exception:
        pass
    _logout()

if _mrp_role=="ADMIN":
    try:
        _mrp_first_central_check = not bool(
            st.session_state.get("_mrp_central_bootstrap_checked")
        )
        _central_bundle=_central_mrp.load_mrp_bundle(
            force_check=_mrp_first_central_check
        )
        st.session_state["_mrp_central_bootstrap_checked"]=True
    except Exception as _central_err:
        _mrp_central_error=str(_central_err)
        _central_bundle={}

    if _central_bundle.get("ready"):
        cadastro_file,estoque_file,geral_file,compras_file,mt_file=_central_mrp.make_refs(_central_bundle)
    else:
        cadastro_file=estoque_file=geral_file=compras_file=mt_file=None
else:
    cadastro_file=estoque_file=geral_file=compras_file=mt_file=None

# ---------------- SIDEBAR 100% HTML/CSS ----------------
_mrp_output_meta=_central_bundle.get("output_meta") or {}
_mrp_output_available=bool(_mrp_output_meta.get("available"))
_mrp_output_stale=bool(_central_bundle.get("output_stale"))
_mrp_stale_inputs=_central_bundle.get("stale_inputs") or {}

if _mrp_central_error:
    _mrp_status_label="ERRO"
    _mrp_status_class="status-error"
elif _mrp_stale_inputs or _mrp_output_stale:
    _mrp_status_label="ATENÇÃO"
    _mrp_status_class="status-warning"
elif _mrp_output_available:
    _mrp_status_label="ATUALIZADO"
    _mrp_status_class="status-ok"
else:
    _mrp_status_label="ATENÇÃO"
    _mrp_status_class="status-warning"

_mrp_output_when=_central_mrp.format_dt(_mrp_output_meta.get("processed_at"))
_mrp_output_rows=_mrp_output_meta.get("rows_count")
if _mrp_output_rows not in (None,""):
    try:
        _mrp_output_rows_label=f"{int(_mrp_output_rows):,}".replace(",", ".")+" REGISTROS"
    except Exception:
        _mrp_output_rows_label=str(_mrp_output_rows)
else:
    _mrp_output_rows_label="SEM REGISTROS"

_mrp_sidebar_week="—"
try:
    _week_frame=_central_bundle.get("relatorio_geral_tratado")
    if _week_frame is not None and not _week_frame.empty and "SEMANA DE NECESSIDADE" in _week_frame.columns:
        _week_values=_week_frame["SEMANA DE NECESSIDADE"].map(semana_id)
        _week_values=pd.to_numeric(_week_values,errors="coerce").dropna()
        _week_values=_week_values[(_week_values>=200001)&(_week_values<=999953)]
        if len(_week_values):
            _mrp_sidebar_week=formatar_semana(int(_week_values.min()))
except Exception:
    pass

_mrp_nav_current=(
    '<a class="sidebar-nav-link active" href="?nav=mrp-atual" target="_self">MRP ATUAL</a>'
    if _mrp_nav_key=="mrp-atual"
    else '<a class="sidebar-nav-link" href="?nav=mrp-atual" target="_self">MRP ATUAL</a>'
)
_mrp_nav_config=(
    '<a class="sidebar-nav-link active" href="?nav=configuracoes" target="_self">CONFIGURAÇÕES</a>'
    if _mrp_nav_key=="configuracoes"
    else '<a class="sidebar-nav-link" href="?nav=configuracoes" target="_self">CONFIGURAÇÕES</a>'
)

_mrp_sidebar_html=(
    '<div class="setta-sidebar">'
    '<div class="sidebar-brand">'
      '<div class="sidebar-brand-title">MRP</div>'
      '<div class="sidebar-brand-sub">Planejamento de Materiais SETTA</div>'
    '</div>'
    '<div class="sidebar-section-label">NAVEGAÇÃO</div>'
    '<div class="sidebar-nav">'
      + _mrp_nav_current
      + _mrp_nav_config
    + '</div>'
    '<div class="sidebar-divider"></div>'
    '<div class="sidebar-section-label">STATUS GERAL</div>'
    '<div class="sidebar-status-card">'
      '<div class="sidebar-status-name">RELATÓRIO MRP</div>'
      f'<div class="sidebar-status-value {_mrp_status_class}">{_mrp_status_label}</div>'
      '<div class="sidebar-status-meta">'
        f'<div>{_mrp_output_when} · {_mrp_output_rows_label}</div>'
      '</div>'
    '</div>'
    '<div class="sidebar-subdivider"></div>'
    '<div class="sidebar-week-card">'
      '<div class="sidebar-status-name">SEMANA ATUAL</div>'
      f'<div class="sidebar-week-value">{_mrp_sidebar_week}</div>'
    '</div>'
    '<div class="sidebar-logout-divider"></div>'
    '<a class="sidebar-logout" href="?logout=1" target="_self">SAIR</a>'
    '</div>'
)

with st.sidebar:
    st.markdown(_mrp_sidebar_html, unsafe_allow_html=True)

# Configurações/contingência permanecem acessíveis, mas fora da geometria
# fixa da navegação principal. Só aparecem quando CONFIGURAÇÕES é selecionado.
if _mrp_role=="ADMIN" and _mrp_nav_key=="configuracoes":
    with st.sidebar.expander("CONTINGÊNCIA E RECUPERAÇÃO", expanded=True):
        _manual_enabled=st.checkbox("USAR ALIMENTAÇÃO MANUAL", key="mrp_manual_feed")
        if _manual_enabled:
            _cad_manual=st.file_uploader("CADASTROS",type=["xlsx","xlsm","xltx"],key="mrp_manual_cad")
            _est_manual=st.file_uploader("ESTOQUE TRATADO",type=["xlsx","xlsm"],key="mrp_manual_est")
            _ger_manual=st.file_uploader("RELATÓRIO GERAL TRATADO",type=["xlsx","xlsm"],key="mrp_manual_ger")
            _comp_manual=st.file_uploader("COMPRAS TRATADO",type=["xlsx","xlsm"],key="mrp_manual_comp")
            _tctp_manual=st.file_uploader("TCTP TRATADO",type=["xlsx","xlsm"],key="mrp_manual_tctp")
            if all([_cad_manual,_est_manual,_ger_manual,_comp_manual,_tctp_manual]):
                cadastro_file=_cad_manual
                estoque_file=_est_manual
                geral_file=_ger_manual
                compras_file=_comp_manual
                mt_file=_tctp_manual
                _mrp_use_manual=True
                st.warning("MODO CONTINGÊNCIA ATIVO.")

        _pending=st.session_state.get("_mrp_pending_snapshots") or {}
        if _pending:
            st.markdown("**SALVAMENTO PENDENTE**")
            for _pending_key,_pending_payload in list(_pending.items()):
                _pending_label=f"SEMANA {_pending_payload.get('semana_mrp') or '-'} · {_pending_key[:8]}"
                _backups=st.session_state.setdefault("_mrp_pending_backup_bytes",{})
                if _pending_key not in _backups:
                    _backups[_pending_key]=_mrp_backup_bytes(_pending_payload)
                st.download_button(
                    "BAIXAR CÓPIA — "+_pending_label,
                    data=_backups[_pending_key],
                    file_name="MRP_Pendente_"+_pending_key[:12]+".json.gz",
                    mime="application/gzip",
                    key="mrp_backup_"+_pending_key,
                    use_container_width=True,
                )
                if st.button("SALVAR PENDENTE — "+_pending_label,key="mrp_retry_"+_pending_key,use_container_width=True):
                    try:
                        _sb_post(_pending_payload)
                        st.session_state["_mrp_saved_sig"]=_pending_key
                        st.success("Histórico confirmado.")
                        st.rerun()
                    except Exception as _pending_error:
                        st.error(str(_pending_error))

        st.markdown("**RECUPERAR CÓPIA**")
        _restore_backup=st.file_uploader(
            "Cópia .json.gz",
            type=["gz"],
            key="mrp_restore_backup_upload",
        )
        if _restore_backup is not None and st.button(
            "RECUPERAR CÓPIA",
            key="mrp_restore_backup_submit",
            use_container_width=True,
        ):
            try:
                _restore_key,_restore_payload=_mrp_restore_backup(_restore_backup)
                st.session_state.setdefault("_mrp_pending_snapshots",{})[_restore_key]=_restore_payload
                _sb_post(_restore_payload)
                st.session_state["_mrp_saved_sig"]=_restore_key
                st.success("Cópia recuperada.")
                st.rerun()
            except Exception as _restore_error:
                st.error(str(_restore_error))

        st.markdown("**RECUPERAR PELO EXCEL**")
        _restore_excel=st.file_uploader(
            "MRP completo .xlsx",
            type=["xlsx"],
            key="mrp_restore_report",
        )
        if _restore_excel is not None:
            _restore_week=st.number_input(
                "Semana do cálculo",
                min_value=1,
                max_value=53,
                value=38,
                key="mrp_restore_week",
            )
            if st.button("GRAVAR HISTÓRICO DO EXCEL",key="mrp_restore_excel_button",use_container_width=True):
                try:
                    _blob=_restore_excel.getvalue()
                    _restore_key=hashlib.sha256(
                        b"MRP-EXCEL-RESTORE-V1|"+str(_restore_week).encode("ascii")+_blob
                    ).hexdigest()
                    _names={
                        "mrp_geral":"MRP_Geral",
                        "projecao_semanal":"Projecao_Semanal",
                        "demanda_projeto":"Demanda_Projeto",
                        "compra_mrp":"Compra_MRP",
                        "compras":"Compras",
                        "fabricacao":"Fabricacao",
                    }
                    _sheets=pd.read_excel(BytesIO(_blob),sheet_name=list(_names.values()))
                    _payload={
                        "semana_mrp":int(_restore_week),
                        "usuario":str(st.session_state.get("auth_nome") or "Não informado")+" — recuperado de Excel",
                        "calculation_key":_restore_key,
                    }
                    for _field,_sheet_name in _names.items():
                        _sheet=_sheets[_sheet_name]
                        _payload[_field]=json.loads(
                            _sheet.to_json(orient="records",force_ascii=False,date_format="iso")
                        )
                    _sb_post(_payload)
                    st.session_state["_mrp_saved_sig"]=_restore_key
                    st.success("Histórico recuperado.")
                    st.rerun()
                except Exception as _excel_error:
                    st.error(f"Histórico não recuperado: {_excel_error}")

if _mrp_stale_inputs:
    _stale_labels={
        "relatorio_geral_tratado":"RELATÓRIO GERAL TRATADO",
        "estoque_tratado":"ESTOQUE TRATADO",
        "compras_tratado":"COMPRAS TRATADO",
        "tctp_tratado":"TCTP TRATADO",
    }
    _stale_names=[_stale_labels.get(_key,_key) for _key in _mrp_stale_inputs]
    st.warning(
        "ATUALIZAÇÃO DETECTADA NA CENTRAL · "
        + " • ".join(_stale_names)
        + ". O MRP aguardará as bases tratadas atuais antes de recalcular."
    )
"""

_source = _source[:_sidebar_start] + _sidebar_v1 + "\n" + _source[_sidebar_end:]

# CSS do padrão validado. Aplicado por último para neutralizar o layout
# automático e as regras antigas de radio/details da sidebar.
_sidebar_css_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
_sidebar_css_html = """
<style>
section[data-testid="stSidebar"]{
  background:#fff!important;
  border-right:1px solid #e8ebf0!important;
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  flex:0 0 260px!important;
  flex-basis:260px!important;
  overflow:hidden!important;
}
section[data-testid="stSidebar"]>div{
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  box-sizing:border-box!important;
}
section[data-testid="stSidebar"] .block-container{
  width:260px!important;
  min-width:260px!important;
  max-width:260px!important;
  box-sizing:border-box!important;
  padding-top:26px!important;
  padding-left:16px!important;
  padding-right:16px!important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
  gap:0!important;
  row-gap:0!important;
}
section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.setta-sidebar){
  margin:0!important;
  padding:0!important;
}

.setta-sidebar{
  width:100%!important;
  margin:0!important;
  padding:0!important;
  box-sizing:border-box!important;
  font-family:inherit!important;
}
.setta-sidebar *{box-sizing:border-box!important}

.sidebar-brand{
  width:100%!important;
  background:#f8fafc!important;
  border:1px solid #e5e8ee!important;
  border-radius:12px!important;
  padding:14px 16px!important;
  margin:0 0 20px 0!important;
}
.sidebar-brand-title{
  margin:0!important;
  padding:0!important;
  font-size:15px!important;
  font-weight:800!important;
  line-height:18px!important;
  color:#111827!important;
  letter-spacing:-.01em!important;
}
.sidebar-brand-sub{
  margin:3px 0 0 0!important;
  padding:0!important;
  font-size:12px!important;
  font-weight:400!important;
  line-height:16px!important;
  color:#6b7280!important;
}
.sidebar-section-label{
  display:block!important;
  margin:0 0 8px 0!important;
  padding:0!important;
  color:#374151!important;
  font-size:12px!important;
  line-height:15px!important;
  font-weight:800!important;
  text-transform:uppercase!important;
  letter-spacing:.055em!important;
}
.sidebar-nav{
  display:flex!important;
  flex-direction:column!important;
  width:100%!important;
  gap:2px!important;
  margin:0!important;
  padding:0!important;
}
.sidebar-nav-link{
  position:relative!important;
  display:flex!important;
  align-items:center!important;
  justify-content:flex-start!important;
  width:100%!important;
  height:42px!important;
  min-height:42px!important;
  max-height:42px!important;
  margin:0!important;
  padding:0 12px 0 24px!important;
  border:1px solid transparent!important;
  border-radius:10px!important;
  background:transparent!important;
  color:#374151!important;
  text-decoration:none!important;
  font-size:13px!important;
  line-height:16px!important;
  font-weight:500!important;
  text-align:left!important;
}
.sidebar-nav-link:hover{
  background:#f8fafc!important;
  border-color:#e5e7eb!important;
  color:#111827!important;
  text-decoration:none!important;
}
.sidebar-nav-link.active{
  background:#111827!important;
  border-color:#111827!important;
  color:#fff!important;
  font-weight:700!important;
  box-shadow:0 5px 14px rgba(17,24,39,.14)!important;
}
.sidebar-nav-link.active::before{
  content:""!important;
  position:absolute!important;
  left:7px!important;
  top:50%!important;
  width:4px!important;
  height:20px!important;
  border-radius:999px!important;
  background:#ef4444!important;
  transform:translateY(-50%)!important;
}
.sidebar-divider{
  display:block!important;
  width:100%!important;
  height:1px!important;
  min-height:1px!important;
  background:#d1d5db!important;
  margin:20px 0!important;
  padding:0!important;
}
.sidebar-status-card,
.sidebar-week-card{
  width:100%!important;
  background:#f8fafc!important;
  border:1px solid #e5e8ee!important;
  border-radius:10px!important;
  padding:12px 14px!important;
  margin:0!important;
  color:#6b7280!important;
}
.sidebar-status-name{
  margin:0!important;
  padding:0!important;
  font-size:11px!important;
  line-height:14px!important;
  font-weight:800!important;
  color:#64748b!important;
  text-transform:uppercase!important;
  letter-spacing:.025em!important;
}
.sidebar-status-value{
  margin:4px 0 0 0!important;
  padding:0!important;
  font-size:13px!important;
  line-height:16px!important;
  font-weight:900!important;
  text-transform:uppercase!important;
}
.sidebar-status-value.status-ok{color:#16a34a!important}
.sidebar-status-value.status-warning{color:#f59e0b!important}
.sidebar-status-value.status-error{color:#ef4444!important}
.sidebar-status-meta{
  margin:6px 0 0 0!important;
  padding:0!important;
  color:#6b7280!important;
  font-size:11px!important;
  line-height:15px!important;
  text-transform:uppercase!important;
}
.sidebar-subdivider{
  width:100%!important;
  height:1px!important;
  background:#d1d5db!important;
  margin:12px 0!important;
}
.sidebar-week-value{
  margin:5px 0 0 0!important;
  color:#111827!important;
  font-size:13px!important;
  line-height:16px!important;
  font-weight:900!important;
}
.sidebar-logout-divider{
  width:100%!important;
  height:1px!important;
  background:#d1d5db!important;
  margin:20px 0 8px 0!important;
}
.sidebar-logout{
  display:flex!important;
  align-items:center!important;
  width:100%!important;
  height:36px!important;
  padding:0 12px!important;
  color:#6b7280!important;
  text-decoration:none!important;
  font-size:12px!important;
  font-weight:700!important;
  border-radius:8px!important;
}
.sidebar-logout:hover{
  background:#f8fafc!important;
  color:#111827!important;
  text-decoration:none!important;
}

/* Widgets de contingência aparecem só quando CONFIGURAÇÕES é selecionado. */
section[data-testid="stSidebar"] details{
  margin-top:14px!important;
}
</style>
"""
_sidebar_css = 'st.markdown(' + repr(_sidebar_css_html) + ', unsafe_allow_html=True)\n'
if _source.count(_sidebar_css_anchor) != 1:
    raise RuntimeError("Âncora do título principal não encontrada para CSS da SIDEBAR SETTA V1.")
_source = _source.replace(
    _sidebar_css_anchor,
    _sidebar_css + "\n" + _sidebar_css_anchor,
    1,
)
'''
