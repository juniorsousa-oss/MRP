PADRONIZACAO_NFS_PATCH = r'''
# =========================================================
# PADRONIZAÇÃO FINAL — MRP NO PADRÃO CONTROLE DE NFs | SETTA
# =========================================================
# Este patch é aplicado por último. O objetivo é preservar toda a lógica
# funcional do MRP e substituir apenas navegação, posicionamento dos status
# e acabamento visual pelo padrão validado do Controle de Notas Fiscais.

# ---------------------------------------------------------
# 1) CSS final: mesmos espaçamentos, cabeçalho e menu do Controle de NFs.
# ---------------------------------------------------------
_title_anchor = 'st.markdown(f\'<h1 class="app-title">{UI_CONFIG["section_main_title"]}</h1>\', unsafe_allow_html=True)\n'
if _source.count(_title_anchor) != 1:
    raise RuntimeError("Título principal do MRP não encontrado para padronização NFS.")

_nfs_css = """
<style>
[data-testid="stAppViewContainer"]{background:#f4f7fb!important}
[data-testid="stHeader"]{background:rgba(255,255,255,.96)!important}
.block-container{max-width:1780px!important;padding-top:3.2rem!important;padding-left:2.7rem!important;padding-right:2.7rem!important;padding-bottom:3rem!important;width:100%!important}

section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e8ebf0!important;width:260px!important;min-width:260px!important;max-width:260px!important;flex:0 0 260px!important;flex-basis:260px!important;overflow:hidden!important}
section[data-testid="stSidebar"]>div{width:260px!important;min-width:260px!important;max-width:260px!important;box-sizing:border-box!important}
section[data-testid="stSidebar"] .block-container{width:260px!important;min-width:260px!important;max-width:260px!important;box-sizing:border-box!important;padding-top:1.6rem!important;padding-left:1rem!important;padding-right:1rem!important}

.sidebar-brand{background:#f8fafc;border:1px solid #e5e8ee;border-radius:12px;padding:.9rem 1rem;margin:0 0 1.05rem 0}
.sidebar-brand-title{font-size:.92rem;font-weight:800;color:#111827;letter-spacing:-.01em}
.sidebar-brand-sub{margin-top:.18rem;font-size:.75rem;color:#6b7280}
.sidebar-section-label{margin:.25rem 0 .45rem 0;color:#374151;font-size:.76rem;font-weight:800;text-transform:uppercase;letter-spacing:.055em}
.sidebar-info-card{background:#f8fafc;border:1px solid #e5e8ee;border-radius:10px;padding:.75rem .85rem;color:#6b7280;font-size:.76rem;line-height:1.55}

section[data-testid="stSidebar"] div[role="radiogroup"]{display:flex;flex-direction:column;gap:.55rem!important}
section[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"],
section[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stMarkdownContainer"] + div{position:absolute!important;opacity:0!important;pointer-events:none!important}
section[data-testid="stSidebar"] div[role="radiogroup"] label{position:relative;width:100%;min-height:42px;display:flex!important;align-items:center!important;padding:.56rem .72rem .56rem .88rem!important;margin:0!important;border:1px solid transparent!important;border-radius:10px!important;background:transparent!important;cursor:pointer;transition:background .14s ease,border-color .14s ease,box-shadow .14s ease,transform .14s ease;box-sizing:border-box}
section[data-testid="stSidebar"] div[role="radiogroup"] > label{margin:0!important}
section[data-testid="stSidebar"] div[role="radiogroup"] label>div:first-child{position:absolute!important;opacity:0!important;width:0!important;height:0!important;overflow:hidden!important}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{margin:0!important;font-size:.83rem!important;font-weight:600!important;color:#374151!important;line-height:1.2!important}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:#f8fafc!important;border-color:#e5e7eb!important;transform:translateX(1px)}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:#111827!important;border-color:#111827!important;box-shadow:0 5px 14px rgba(17,24,39,.14)!important}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked)::before{content:"";position:absolute;left:.42rem;top:50%;width:4px;height:20px;border-radius:999px;background:#ef4444;transform:translateY(-50%)}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{color:#fff!important;font-weight:700!important}

[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] .main,
[data-testid="stMain"],
.stMain{width:100%!important;max-width:100%!important;margin-left:0!important;margin-right:0!important}
[data-testid="stAppViewContainer"] .main .block-container,
[data-testid="stMain"] .block-container,
.stMain .block-container{width:100%!important;max-width:100%!important;margin-left:0!important;margin-right:0!important;padding-top:3.2rem!important;padding-left:2.7rem!important;padding-right:2.7rem!important;padding-bottom:3rem!important}
div[data-testid="stElementContainer"]:has(.app-title){margin-top:0!important;padding-top:0!important}
div[data-testid="stElementContainer"]:has(.setta-logo-card){margin-top:0!important;padding-top:15px!important}
section[data-testid="stSidebar"][aria-expanded="false"]{width:0!important;min-width:0!important;max-width:0!important;flex:0 0 0!important;flex-basis:0!important}
section[data-testid="stSidebar"][aria-expanded="false"]>div{width:0!important;min-width:0!important;max-width:0!important}

.setta-logo-card{width:100%!important;min-height:128px!important;display:flex!important;align-items:center!important;justify-content:center!important;background:#fff!important;border:1px solid #e5e8ee!important;border-radius:16px!important;box-shadow:0 4px 14px rgba(24,39,75,.08)!important;box-sizing:border-box!important;margin:0 0 2.55rem 0!important;padding:1.1rem 2rem!important}
.setta-logo-card img{display:block!important;width:auto!important;height:auto!important;max-width:205px!important;max-height:86px!important;object-fit:contain!important}
.app-title{margin:0!important;padding:0!important;font-size:2.55rem!important;line-height:1.08!important;font-weight:800!important;letter-spacing:-.04em!important;color:#050505!important}
.app-subtitle,.app-sub,.setta-main-description{margin-top:.72rem!important;margin-bottom:1.65rem!important;color:#4f5661!important;font-size:.94rem!important;line-height:1.35!important;text-transform:uppercase!important}

.section-title{margin:0 0 1rem!important;color:#0f172a!important;font-size:1.28rem!important;font-weight:900!important;letter-spacing:-.02em;text-transform:uppercase}
.section-band{margin:0 0 .95rem!important;padding:.82rem 1rem!important;background:#fff!important;border:1px solid #e5e8ee!important;border-left:5px solid #111827!important;border-radius:12px!important;box-shadow:0 3px 12px rgba(15,23,42,.035)!important}
.section-band-kicker{font-size:.66rem!important;font-weight:900!important;letter-spacing:.085em!important;text-transform:uppercase!important;color:#ef4444!important;margin-bottom:.18rem!important}
.section-band-title{font-size:1.08rem!important;font-weight:900!important;color:#111827!important;letter-spacing:-.015em!important;line-height:1.2!important;text-transform:uppercase!important}
.topic-divider{height:1px!important;background:#cbd5e1!important;margin:1.55rem 0 1.05rem!important;width:100%!important}

.mrp-source-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.72rem;margin:.25rem 0 1rem}
.mrp-source-card{position:relative;background:#fff;border:1px solid #dfe3e8;border-radius:12px;padding:.82rem .9rem;box-shadow:0 3px 12px rgba(15,23,42,.035);overflow:hidden;min-height:96px}
.mrp-source-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:#22c55e}
.mrp-source-name{font-size:.69rem;font-weight:900;color:#64748b;text-transform:uppercase;letter-spacing:.035em}
.mrp-source-status{margin-top:.26rem;font-size:.88rem;font-weight:900;color:#111827;text-transform:uppercase}
.mrp-source-meta{margin-top:.28rem;font-size:.64rem;color:#94a3b8;text-transform:uppercase}

.sidebar-status-card{background:#f8fafc;border:1px solid #e5e8ee;border-radius:10px;padding:.75rem .85rem;color:#6b7280;font-size:.72rem;line-height:1.5}
.sidebar-status-name{font-size:.68rem;font-weight:900;color:#64748b;text-transform:uppercase;letter-spacing:.025em}
.sidebar-status-value{margin-top:.16rem;font-size:.8rem;font-weight:900;color:#111827;text-transform:uppercase}
.sidebar-status-meta{margin-top:.24rem;color:#6b7280;font-size:.66rem;line-height:1.45;text-transform:uppercase}
section[data-testid="stSidebar"] hr{margin:.85rem 0!important}
.sidebar-week-card{background:#f8fafc;border:1px solid #e5e8ee;border-radius:10px;padding:.72rem .85rem;color:#6b7280;font-size:.72rem;line-height:1.45}
.sidebar-week-label{font-size:.66rem;font-weight:900;color:#64748b;text-transform:uppercase;letter-spacing:.035em}
.sidebar-week-value{margin-top:.16rem;font-size:.82rem;font-weight:900;color:#111827;text-transform:uppercase}

[data-testid="stTabs"] button{font-weight:800!important;text-transform:uppercase!important;letter-spacing:.015em!important}
div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3,
div[data-testid="stMarkdownContainer"] h4{text-transform:uppercase}
[data-testid="stAlert"]{border-radius:12px!important;box-shadow:0 3px 12px rgba(15,23,42,.035)}

@media(max-width:1250px){.mrp-source-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:900px){
  .block-container{padding-top:2rem!important;padding-left:1rem!important;padding-right:1rem!important;padding-bottom:2rem!important}
  .setta-logo-card{min-height:105px!important;margin-bottom:1.8rem!important;padding:.9rem 1rem!important}
  .setta-logo-card img{max-width:170px!important;max-height:72px!important}
  .app-title{font-size:2rem!important;line-height:1.12!important}
  .app-subtitle,.app-sub,.setta-main-description{font-size:.86rem!important;margin-bottom:1.35rem!important}
  .section-title{font-size:1.14rem!important}
  .mrp-source-grid{grid-template-columns:1fr!important}
}
</style>
"""
_source = _source.replace(
    _title_anchor,
    'st.markdown(' + repr(_nfs_css) + ', unsafe_allow_html=True)\n' + _title_anchor,
    1,
)

# ---------------------------------------------------------
# 2) Menu lateral: mesma arquitetura do Controle de NFs.
#    ALIMENTAÇÃO/CONTINGÊNCIA sai da lateral e vai para CONFIGURAÇÕES.
# ---------------------------------------------------------
_sidebar_start = _source.find(
    'with st.sidebar:\n    st.markdown(\n        \'<div class="sidebar-brand">\''
)
_sidebar_end = _source.find('\ndef _mrp_source_card_html(', _sidebar_start)
if _sidebar_start < 0 or _sidebar_end < 0:
    raise RuntimeError("Menu lateral atual do MRP não encontrado para padronização.")

_new_sidebar = r"""with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-title">MRP</div>'
        '<div class="sidebar-brand-sub">Planejamento de Materiais SETTA</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sidebar-section-label">NAVEGAÇÃO</div>',
        unsafe_allow_html=True,
    )

    _mrp_role=st.session_state.get("auth_role")
    _mrp_pages=["MRP ATUAL", "CONFIGURAÇÕES"] if _mrp_role=="ADMIN" else ["MRP ATUAL"]
    _mrp_page=st.radio(
        "Página",
        _mrp_pages,
        label_visibility="collapsed",
        key="mrp_sidebar_navigation",
    )

    _mrp_use_manual=False
    _central_bundle={}
    usuario_mrp=st.session_state.get("auth_nome", "")

    # A Central é a mesma fonte de dados para ADMIN e CONSULTA.
    # A diferença de perfil afeta apenas ações administrativas.
    try:
        _central_bundle=_central_mrp.load_mrp_bundle()
        st.session_state.pop("_mrp_central_error",None)
    except Exception as _central_err:
        st.session_state["_mrp_central_error"]=str(_central_err)
        _central_bundle={}

    _manual_store=st.session_state.get("_mrp_manual_files") or {}
    _manual_active=bool(st.session_state.get("_mrp_manual_active"))
    _manual_keys=("cadastros","estoque","geral","compras","tctp")

    if (
        _mrp_role=="ADMIN"
        and _manual_active
        and all(k in _manual_store for k in _manual_keys)
    ):
        cadastro_file=BytesIO(_manual_store["cadastros"])
        estoque_file=BytesIO(_manual_store["estoque"])
        geral_file=BytesIO(_manual_store["geral"])
        compras_file=BytesIO(_manual_store["compras"])
        mt_file=BytesIO(_manual_store["tctp"])
        _mrp_use_manual=True
    elif _central_bundle.get("ready"):
        cadastro_file,estoque_file,geral_file,compras_file,mt_file=_central_mrp.make_refs(_central_bundle)
    else:
        cadastro_file=estoque_file=geral_file=compras_file=mt_file=None

    st.divider()
    st.markdown(
        '<div class="sidebar-info-card">'
        f'<b>{str(st.session_state.get("auth_nome") or "USUÁRIO").upper()}</b><br>'
        f'{str(_mrp_role or "").upper()}'
        + ('<br>MODO CONTINGÊNCIA' if _mrp_use_manual else '<br>ALIMENTAÇÃO AUTOMÁTICA')
        + '</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        '<div class="sidebar-section-label">STATUS GERAL</div>',
        unsafe_allow_html=True,
    )

    def _mrp_sidebar_status_html(_meta):
        _meta=_meta or {}
        _available=bool(_meta.get("available"))
        _status="ATUALIZADO" if _available else "AGUARDANDO"
        _when=_central_mrp.format_dt(_meta.get("processed_at"))
        _rows=_meta.get("rows_count")
        _rows_text=""
        if _rows not in (None,""):
            try:
                _rows_text=f'{int(_rows):,}'.replace(",", ".")+" REGISTROS"
            except Exception:
                _rows_text=""
        _parts=[x for x in (_when,_rows_text) if x and x!="—"]
        _meta_text=" · ".join(_parts) if _parts else "SEM ATUALIZAÇÃO REGISTRADA"
        return (
            '<div class="sidebar-status-card">'
            '<div class="sidebar-status-name">RELATÓRIO MRP</div>'
            f'<div class="sidebar-status-value">{_status}</div>'
            f'<div class="sidebar-status-meta">{_meta_text}</div>'
            '</div>'
        )

    _mrp_status_placeholder=st.empty()
    _initial_output_meta=(
        st.session_state.get("_mrp_output_meta")
        or (_central_bundle.get("output_meta") if _central_bundle else {})
        or {}
    )
    _mrp_status_placeholder.markdown(
        _mrp_sidebar_status_html(_initial_output_meta),
        unsafe_allow_html=True,
    )
"""
_source = _source[:_sidebar_start] + _new_sidebar + "\n" + _source[_sidebar_end:]

# ---------------------------------------------------------
# 3) Retira a Central de Dados do rodapé da página MRP.
# ---------------------------------------------------------
_footer_sources = """st.markdown('<div class="topic-divider"></div>', unsafe_allow_html=True)
if st.session_state.get("auth_role")=="ADMIN" and _central_bundle:
    _render_mrp_central_status(_central_bundle)"""
if _footer_sources in _source:
    _source = _source.replace(_footer_sources, "", 1)

# ---------------------------------------------------------
# 4) O status geral deixa o corpo principal e passa a atualizar o card
#    inferior do menu lateral.
# ---------------------------------------------------------
_output_marker = "'<div class=\"mrp-output-card\">'"
_output_marker_index = _source.find(_output_marker)
if _output_marker_index >= 0:
    _output_start = _source.rfind("        st.markdown(", 0, _output_marker_index)
    _output_close = '            unsafe_allow_html=True,\n        )'
    _output_end = _source.find(_output_close, _output_marker_index)
    if _output_start < 0 or _output_end < 0:
        raise RuntimeError("Card de status geral do MRP não pôde ser movido para a lateral.")
    _output_end += len(_output_close)
    _output_replacement = """        st.session_state["_mrp_output_meta"]=_mrp_output_meta
        try:
            _mrp_status_placeholder.markdown(
                _mrp_sidebar_status_html(_mrp_output_meta),
                unsafe_allow_html=True,
            )
        except Exception:
            pass"""
    _source = _source[:_output_start] + _output_replacement + _source[_output_end:]

# ---------------------------------------------------------
# 5) CONFIGURAÇÕES > STATUS API.
#    Todas as fontes da Central ficam reunidas em uma única página.
# ---------------------------------------------------------
_config_anchor = 'if st.session_state.get("auth_role") == "CONSULTA":'
if _source.count(_config_anchor) != 1:
    raise RuntimeError("Ponto de entrada da página de Configurações não encontrado.")

_config_page = r"""
if st.session_state.get("auth_role")=="ADMIN" and _mrp_page=="CONFIGURAÇÕES":
    _tab_status_api, = st.tabs(["STATUS API"])

    with _tab_status_api:
        st.markdown(
            '<div class="section-band">'
            '<div class="section-band-kicker">01 · FONTES</div>'
            '<div class="section-band-title">CENTRAL DE DADOS</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.get("_mrp_central_error"):
            st.warning(
                "CENTRAL INDISPONÍVEL · "
                + str(st.session_state.get("_mrp_central_error"))
            )

        _cad_meta=(_central_bundle.get("cadastro_meta") or {}) if _central_bundle else {}
        _derived_meta=(_central_bundle.get("derived_meta") or {}) if _central_bundle else {}
        _api_cards=[
            _mrp_source_card_html(
                "CADASTROS",
                "ATUALIZADO" if _cad_meta.get("available") else "AGUARDANDO",
                _cad_meta,
            ),
            _mrp_source_card_html(
                "RELATÓRIO GERAL TRATADO",
                "ATUALIZADO" if (_derived_meta.get("relatorio_geral_tratado") or {}).get("available") else "AGUARDANDO",
                _derived_meta.get("relatorio_geral_tratado") or {},
            ),
            _mrp_source_card_html(
                "ESTOQUE TRATADO",
                "ATUALIZADO" if (_derived_meta.get("estoque_tratado") or {}).get("available") else "AGUARDANDO",
                _derived_meta.get("estoque_tratado") or {},
            ),
            _mrp_source_card_html(
                "COMPRAS TRATADO",
                "ATUALIZADO" if (_derived_meta.get("compras_tratado") or {}).get("available") else "AGUARDANDO",
                _derived_meta.get("compras_tratado") or {},
            ),
            _mrp_source_card_html(
                "TCTP TRATADO",
                "ATUALIZADO" if (_derived_meta.get("tctp_tratado") or {}).get("available") else "AGUARDANDO",
                _derived_meta.get("tctp_tratado") or {},
            ),
        ]
        st.markdown(
            '<div class="mrp-source-grid">'+"".join(_api_cards)+'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="topic-divider"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-band">'
            '<div class="section-band-kicker">02 · CONTINGÊNCIA</div>'
            '<div class="section-band-title">ALIMENTAÇÃO E RECUPERAÇÃO</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("ALIMENTAÇÃO MANUAL", expanded=False):
            _manual_active_now=bool(st.session_state.get("_mrp_manual_active"))
            if _manual_active_now:
                st.warning("MODO CONTINGÊNCIA ATIVO. O MRP ESTÁ USANDO AS BASES MANUAIS.")

            _cad_manual=st.file_uploader(
                "CADASTROS",
                type=["xlsx","xlsm","xltx"],
                key="mrp_manual_cad_config",
            )
            _est_manual=st.file_uploader(
                "ESTOQUE TRATADO",
                type=["xlsx","xlsm"],
                key="mrp_manual_est_config",
            )
            _ger_manual=st.file_uploader(
                "RELATÓRIO GERAL TRATADO",
                type=["xlsx","xlsm"],
                key="mrp_manual_ger_config",
            )
            _comp_manual=st.file_uploader(
                "COMPRAS TRATADO",
                type=["xlsx","xlsm"],
                key="mrp_manual_comp_config",
            )
            _tctp_manual=st.file_uploader(
                "TCTP TRATADO",
                type=["xlsx","xlsm"],
                key="mrp_manual_tctp_config",
            )

            if all([
                _cad_manual,
                _est_manual,
                _ger_manual,
                _comp_manual,
                _tctp_manual,
            ]):
                if st.button(
                    "ATIVAR ALIMENTAÇÃO MANUAL",
                    type="primary",
                    use_container_width=True,
                    key="mrp_activate_manual_config",
                ):
                    st.session_state["_mrp_manual_files"]={
                        "cadastros":_cad_manual.getvalue(),
                        "estoque":_est_manual.getvalue(),
                        "geral":_ger_manual.getvalue(),
                        "compras":_comp_manual.getvalue(),
                        "tctp":_tctp_manual.getvalue(),
                    }
                    st.session_state["_mrp_manual_active"]=True
                    st.success("ALIMENTAÇÃO MANUAL ATIVADA.")
                    st.rerun()

            if _manual_active_now:
                if st.button(
                    "VOLTAR PARA ALIMENTAÇÃO AUTOMÁTICA",
                    use_container_width=True,
                    key="mrp_disable_manual_config",
                ):
                    st.session_state["_mrp_manual_active"]=False
                    st.session_state.pop("_mrp_manual_files",None)
                    st.success("ALIMENTAÇÃO AUTOMÁTICA RESTAURADA.")
                    st.rerun()

        with st.expander("SALVAMENTO PENDENTE E RECUPERAÇÃO", expanded=False):
            _pending=st.session_state.get("_mrp_pending_snapshots") or {}
            if _pending:
                st.markdown("**SALVAMENTO PENDENTE**")
                for _pending_key,_pending_payload in list(_pending.items()):
                    _pending_label=f'SEMANA {_pending_payload.get("semana_mrp") or "-"} · {_pending_key[:8]}'
                    _backups=st.session_state.setdefault("_mrp_pending_backup_bytes",{})
                    if _pending_key not in _backups:
                        _backups[_pending_key]=_mrp_backup_bytes(_pending_payload)
                    st.download_button(
                        "BAIXAR CÓPIA — "+_pending_label,
                        data=_backups[_pending_key],
                        file_name="MRP_Pendente_"+_pending_key[:12]+".json.gz",
                        mime="application/gzip",
                        key="mrp_backup_config_"+_pending_key,
                        use_container_width=True,
                    )
                    if st.button(
                        "SALVAR PENDENTE — "+_pending_label,
                        key="mrp_retry_config_"+_pending_key,
                        use_container_width=True,
                    ):
                        try:
                            _sb_post(_pending_payload)
                            st.session_state["_mrp_saved_sig"]=_pending_key
                            st.success("HISTÓRICO CONFIRMADO.")
                            st.rerun()
                        except Exception as _pending_error:
                            st.error(str(_pending_error))
            else:
                st.caption("NENHUM SALVAMENTO PENDENTE.")

            st.markdown("**RECUPERAR CÓPIA**")
            _restore_backup=st.file_uploader(
                "CÓPIA .JSON.GZ",
                type=["gz"],
                key="mrp_restore_backup_config",
            )
            if _restore_backup is not None and st.button(
                "RECUPERAR CÓPIA",
                key="mrp_restore_backup_submit_config",
                use_container_width=True,
            ):
                try:
                    _restore_key,_restore_payload=_mrp_restore_backup(_restore_backup)
                    st.session_state.setdefault("_mrp_pending_snapshots",{})[_restore_key]=_restore_payload
                    _sb_post(_restore_payload)
                    st.session_state["_mrp_saved_sig"]=_restore_key
                    st.success("CÓPIA RECUPERADA.")
                    st.rerun()
                except Exception as _restore_error:
                    st.error(str(_restore_error))

            st.markdown("**RECUPERAR PELO EXCEL**")
            _restore_excel=st.file_uploader(
                "MRP COMPLETO .XLSX",
                type=["xlsx"],
                key="mrp_restore_report_config",
            )
            if _restore_excel is not None:
                _restore_week=st.number_input(
                    "SEMANA DO CÁLCULO",
                    min_value=1,
                    max_value=53,
                    value=38,
                    key="mrp_restore_week_config",
                )
                if st.button(
                    "GRAVAR HISTÓRICO DO EXCEL",
                    key="mrp_restore_excel_button_config",
                    use_container_width=True,
                ):
                    try:
                        _blob=_restore_excel.getvalue()
                        _restore_key=hashlib.sha256(
                            b"MRP-EXCEL-RESTORE-V1|"
                            +str(_restore_week).encode("ascii")
                            +_blob
                        ).hexdigest()
                        _names={
                            "mrp_geral":"MRP_Geral",
                            "projecao_semanal":"Projecao_Semanal",
                            "demanda_projeto":"Demanda_Projeto",
                            "compra_mrp":"Compra_MRP",
                            "compras":"Compras",
                            "fabricacao":"Fabricacao",
                        }
                        _sheets=pd.read_excel(
                            BytesIO(_blob),
                            sheet_name=list(_names.values()),
                        )
                        _payload={
                            "semana_mrp":int(_restore_week),
                            "usuario":str(
                                st.session_state.get("auth_nome")
                                or "Não informado"
                            )+" — recuperado de Excel",
                            "calculation_key":_restore_key,
                        }
                        for _field,_sheet_name in _names.items():
                            _sheet=_sheets[_sheet_name]
                            _payload[_field]=json.loads(
                                _sheet.to_json(
                                    orient="records",
                                    force_ascii=False,
                                    date_format="iso",
                                )
                            )
                        _sb_post(_payload)
                        st.session_state["_mrp_saved_sig"]=_restore_key
                        st.success("HISTÓRICO RECUPERADO.")
                        st.rerun()
                    except Exception as _excel_error:
                        st.error(
                            "HISTÓRICO NÃO RECUPERADO: "
                            +str(_excel_error)
                        )

        st.markdown(
            '<div class="topic-divider"></div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "SAIR",
            use_container_width=True,
            key="mrp_logout_config",
        ):
            _logout()

    st.stop()

"""
_source = _source.replace(
    _config_anchor,
    _config_page + "\n" + _config_anchor,
    1,
)

# PERFIS — ADMIN e CONSULTA compartilham a mesma visualização operacional.
# CONSULTA não entra em CONFIGURAÇÕES e os uploads de tratativas continuam protegidos por ADMIN.
_consulta_start = _source.find('if st.session_state.get("auth_role") == "CONSULTA":')
_consulta_end = _source.find('\nif not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):', _consulta_start)
if _consulta_start < 0 or _consulta_end < 0:
    raise RuntimeError("Bloco legado de visualização CONSULTA não encontrado para unificação.")
_source = _source[:_consulta_start] + _source[_consulta_end + 1:]

# Histórico/comparativo é informação de consulta e deve aparecer para os dois perfis.
_hist_fallback_old = '''            render_consulta_view()
            if st.session_state.get("auth_role") == "ADMIN":
                render_mrp_history()'''
_hist_fallback_new = '''            render_consulta_view()
            render_mrp_history()'''
if _hist_fallback_old in _source:
    _source = _source.replace(_hist_fallback_old, _hist_fallback_new, 1)

_hist_bottom_old = '''st.divider()
if st.session_state.get("auth_role") == "ADMIN":
    render_mrp_history()'''
_hist_bottom_new = '''st.divider()
render_mrp_history()'''
if _hist_bottom_old in _source:
    _source = _source.replace(_hist_bottom_old, _hist_bottom_new, 1)


# ---------------------------------------------------------
# 6) LIMPEZA DE CONTEÚDO — títulos duplicados e instrução discreta.
# ---------------------------------------------------------
_source = _source.replace(
    '    st.subheader(UI_CONFIG["title_demanda_geral"])\n',
    '',
    1,
)
_source = _source.replace(
    '    st.subheader(UI_CONFIG["title_demanda_projeto"])\n',
    '',
    1,
)
# Compatibilidade com a forma antiga, caso algum patch anterior volte a usá-la.
_source = _source.replace(
    '    st.subheader(UI_CONFIG["title_demanda_geral"]); ',
    '    ',
    1,
)
_source = _source.replace(
    '    st.subheader(UI_CONFIG["title_demanda_projeto"]); ',
    '    ',
    1,
)
_source = _source.replace(
    '    st.markdown("**Clique em uma linha para abrir o detalhamento do material.**")',
    '    st.caption("Clique em uma linha para abrir o detalhamento do material.")',
    1,
)


# ---------------------------------------------------------
# 7) SIDEBAR — mantém abaixo do STATUS GERAL apenas a SEMANA ATUAL.
# ---------------------------------------------------------
_old_week_sidebar_number = 'with st.sidebar:\n    st.divider(); st.markdown("**Semana atual identificada nas bases**"); st.number_input("Semana atual",min_value=1,max_value=53,value=semana_atual,disabled=True); st.caption(f"Fonte: {fonte_semana}")'
_old_week_sidebar_text = 'with st.sidebar:\n    st.divider(); st.markdown("**Semana atual identificada nas bases**"); st.text_input("Semana atual",value=formatar_semana(semana_atual),disabled=True); st.caption(f"Fonte: {fonte_semana}")'
_new_week_sidebar = """with st.sidebar:
    st.divider()
    st.markdown(
        '<div class="sidebar-week-card">'
        '<div class="sidebar-week-label">SEMANA ATUAL</div>'
        f'<div class="sidebar-week-value">{formatar_semana(semana_atual)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )"""
if _old_week_sidebar_text in _source:
    _source = _source.replace(_old_week_sidebar_text, _new_week_sidebar, 1)
elif _old_week_sidebar_number in _source:
    _source = _source.replace(_old_week_sidebar_number, _new_week_sidebar, 1)
'''
