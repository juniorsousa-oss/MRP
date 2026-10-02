CENTRAL_DATA_PATCH = r'''
# =========================================================
# CENTRAL DE DADOS SETTA — ALIMENTAÇÃO AUTOMÁTICA DO MRP
# =========================================================
_source = "import central_mrp_data as _central_mrp\n" + _source

_central_helper_anchor = 'with st.sidebar:\n    st.header("Acesso")'
_central_helper = r"""
@st.cache_data(show_spinner=False, max_entries=4)
def _mrp_load_sources_from_central(_bundle, signature):
    bundle=_bundle
    if not bundle or not bundle.get("ready"):
        raise ValueError("As cinco bases do MRP ainda não estão disponíveis na Central de Dados.")

    # CADASTROS: leitura por cabeçalho para aceitar o relatório antigo
    # e o novo, sem depender do nome da aba.
    _cad_raw=pd.read_excel(BytesIO(bundle["cadastros_bytes"]),sheet_name=0,header=1)
    _cad_cols={str(x).strip().upper():x for x in _cad_raw.columns}
    _cad_code=_cad_cols.get("CODIGO") or _cad_cols.get("CÓDIGO")
    _cad_desc=_cad_cols.get("DESCRICAO") or _cad_cols.get("DESCRIÇÃO")
    _cad_tipo=_cad_cols.get("TIPO")
    _cad_ativo=_cad_cols.get("ATIVO")
    if not all([_cad_code,_cad_desc,_cad_tipo]):
        raise ValueError("CADASTROS sem colunas obrigatórias: Codigo, Descricao e Tipo.")

    def _cad_codigo_canonico(value):
        if value is None or pd.isna(value):
            return ""
        if not isinstance(value,str):
            parsed=pd.to_numeric(pd.Series([value]),errors="coerce").iloc[0]
            if pd.notna(parsed) and float(parsed).is_integer():
                digits=str(int(parsed))
                return digits.zfill(8) if len(digits)<=8 else digits
        return str(value).strip()

    _cad_code_text=_cad_raw[_cad_code].map(_cad_codigo_canonico)
    _cad_valid_code=_cad_code_text.str.fullmatch(r"\d{8}",na=False)

    if _cad_ativo:
        _cad_ativo_value=_cad_raw[_cad_ativo].fillna("").astype(str).str.strip().str.upper()
        _cad_ok_status=_cad_ativo_value.isin(["S",""])
        _cad_blocked=_cad_ativo_value.eq("N")
    else:
        _cad_ativo_value=pd.Series("",index=_cad_raw.index,dtype=str)
        _cad_ok_status=pd.Series(True,index=_cad_raw.index)
        _cad_blocked=pd.Series(False,index=_cad_raw.index)

    _cad_ok=_cad_valid_code & _cad_ok_status
    _cad_inconsistent=(~_cad_valid_code & _cad_ok_status) | (~_cad_ok_status & ~_cad_blocked)

    cad=pd.DataFrame({
        "Código Texto":_cad_code_text,
        "Descrição":_cad_raw[_cad_desc],
        "Tipo":_cad_raw[_cad_tipo],
        "Ativo":_cad_ativo_value,
    })
    cad=cad[_cad_ok].copy()
    cad["Código"]=pd.to_numeric(cad["Código Texto"],errors="coerce")
    cad=cad.dropna(subset=["Código"])
    cad["Código"]=cad["Código"].astype("int64")
    cad["Descrição"]=cad["Descrição"].fillna("").astype(str).str.strip()
    cad["Tipo"]=cad["Tipo"].fillna("").astype(str).str.strip()
    cad["Ativo"]=cad["Ativo"].fillna("").astype(str).str.strip()
    cad=cad.drop(columns=["Código Texto"]).drop_duplicates("Código",keep="first").reset_index(drop=True)
    _cad_valid_codes=set(cad["Código"].tolist())

    er=bundle["estoque_tratado"].copy()
    _est_req=["COD_MATERIAL","SALDO_DISPONIVEL"]
    _est_missing=[c for c in _est_req if c not in er.columns]
    if _est_missing:
        raise ValueError("ESTOQUE TRATADO sem colunas obrigatórias: "+", ".join(_est_missing))
    est=pd.DataFrame({
        "Código":num(er["COD_MATERIAL"]),
        "Saldo em Estoque":num(er["SALDO_DISPONIVEL"]).fillna(0),
    }).dropna(subset=["Código"])
    est["Código"]=est["Código"].astype("int64")
    est=est[est["Código"].isin(_cad_valid_codes)].copy()
    est=est.groupby("Código",as_index=False)["Saldo em Estoque"].sum()

    gr=bundle["relatorio_geral_tratado"].copy()
    _rg_req=[
        "Projeto","Código","Última solicitação","Qtd. necessária","Pendência",
        "DATA MRP","DATA CM","CONDIÇÃO","SEMANA DE NECESSIDADE","VINCULAÇÃO DA DATA"
    ]
    _rg_missing=[c for c in _rg_req if c not in gr.columns]
    if _rg_missing:
        raise ValueError("RELATÓRIO GERAL TRATADO sem colunas obrigatórias: "+", ".join(_rg_missing))
    rg=pd.DataFrame({
        "Código":num(gr["Código"]),
        "Pendência":num(gr["Pendência"]).fillna(0),
        "Quantidade Solicitada":num(gr["Qtd. necessária"]).fillna(0),
        "Data Solicitação":pd.to_datetime(gr["Última solicitação"],errors="coerce",dayfirst=True),
        "Data MRP":pd.to_datetime(gr["DATA MRP"],errors="coerce",dayfirst=True),
        "Data CM":pd.to_datetime(gr["DATA CM"],errors="coerce",dayfirst=True),
        "Condição":gr["CONDIÇÃO"].fillna("").astype(str).str.strip(),
        "Semana":gr["SEMANA DE NECESSIDADE"].map(semana_id),
        "Projeto":gr["Projeto"].fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.strip(),
        "Vinculação da Data":gr["VINCULAÇÃO DA DATA"].fillna("").astype(str).str.strip(),
    }).dropna(subset=["Código"])
    rg["Código"]=rg["Código"].astype("int64")
    rg=rg[rg["Código"].isin(_cad_valid_codes)].copy()
    rg_mrp=rg[
        rg["Semana"].notna()
        & rg["Semana"].between(200001,999953)
    ].copy()
    rg_mrp["Semana"]=rg_mrp["Semana"].astype("int64")

    cr=bundle["compras_tratado"].copy()
    _cp_req=[
        "CÓD","S.C","QUANTIDADE S.C","SEMANA DE ATENDIMENTO S.C",
        "P.C","QUANTIDADE P.C","SEMANA DE ATENDIMENTO P.C","PRÉ-NOTA"
    ]
    _cp_missing=[c for c in _cp_req if c not in cr.columns]
    if _cp_missing:
        raise ValueError("COMPRAS TRATADO sem colunas obrigatórias: "+", ".join(_cp_missing))
    cp=pd.DataFrame({
        "Código":num(cr["CÓD"]),
        "Quantidade S.C.":num(cr["QUANTIDADE S.C"]).fillna(0),
        "Semana S.C.":cr["SEMANA DE ATENDIMENTO S.C"].map(semana_id),
        "Quantidade P.C.":num(cr["QUANTIDADE P.C"]).fillna(0),
        "Semana P.C.":cr["SEMANA DE ATENDIMENTO P.C"].map(semana_id),
        "Nº S.C.":cr["S.C"],
        "Nº P.C.":cr["P.C"],
        "Saldo em Pré Nota":num(cr["PRÉ-NOTA"]).fillna(0),
    }).dropna(subset=["Código"])
    cp["Código"]=cp["Código"].astype("int64")
    cp=cp[cp["Código"].isin(_cad_valid_codes)].copy()
    for c in ["Nº S.C.","Nº P.C."]:
        cp[c]=cp[c].fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.strip()

    mt0=bundle["tctp_tratado"].copy()
    _mt_req=[
        "ORDEM DE PRODUÇÃO","CÓDIGO PRODUTO","SEMANA DE ENTREGA",
        "MATERIAL","QUANTIDADE POR OF","SEMANA DE NECESSIDADE"
    ]
    _mt_missing=[c for c in _mt_req if c not in mt0.columns]
    if _mt_missing:
        raise ValueError("TCTP TRATADO sem colunas obrigatórias: "+", ".join(_mt_missing))
    mt=pd.DataFrame({
        "ORDEM DE PRODUÇÃO":mt0["ORDEM DE PRODUÇÃO"].fillna("").astype(str).str.strip(),
        "Código Produto":num(mt0["CÓDIGO PRODUTO"]).fillna(0),
        "Semana Entrega":mt0["SEMANA DE ENTREGA"].map(semana_id),
        "Material":num(mt0["MATERIAL"]).fillna(0),
        "Quantidade":num(mt0["QUANTIDADE POR OF"]).fillna(0.0),
        "Semana Necessidade":mt0["SEMANA DE NECESSIDADE"].map(semana_id),
    })
    mt["Código Produto"]=mt["Código Produto"].fillna(0).astype("int64")
    mt["Material"]=mt["Material"].fillna(0).astype("int64")
    mt=mt[
        mt["Código Produto"].isin(_cad_valid_codes)
        & mt["Material"].isin(_cad_valid_codes)
    ].copy()

    return cad,est,rg,rg_mrp,cp,mt

"""
if _source.count(_central_helper_anchor) != 1:
    raise RuntimeError("Ponto de instalação da leitura central do MRP não encontrado.")
_source = _source.replace(
    _central_helper_anchor,
    _central_helper + "\n" + _central_helper_anchor,
    1,
)

_sidebar_start = _source.find('with st.sidebar:\n    st.header("Acesso")')
_sidebar_end = _source.find('if st.session_state.get("auth_role") == "CONSULTA":', _sidebar_start)
if _sidebar_start < 0 or _sidebar_end < 0:
    raise RuntimeError("Bloco lateral do MRP não encontrado para integração com a Central.")

_central_sidebar = r"""with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-title">MRP</div>'
        '<div class="sidebar-brand-sub">Planejamento de Materiais SETTA</div>'
        '</div>'
        '<div class="sidebar-section-label">NAVEGAÇÃO</div>',
        unsafe_allow_html=True,
    )

    _mrp_role=st.session_state.get("auth_role")
    st.radio(
        "NAVEGAÇÃO",
        ["MRP ATUAL"],
        label_visibility="collapsed",
        key="mrp_sidebar_navigation",
    )

    st.markdown("---")
    st.markdown(
        '<div class="sidebar-info-card">'
        f'<b>{str(st.session_state.get("auth_nome") or "USUÁRIO").upper()}</b><br>'
        f'{str(_mrp_role or "").upper()}<br>'
        'CENTRAL DE DADOS · AUTOMÁTICA'
        '</div>',
        unsafe_allow_html=True,
    )

    _mrp_use_manual=False
    _central_bundle={}
    usuario_mrp=st.session_state.get("auth_nome", "")

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
            st.error(f"Central indisponível: {_central_err}")
            _central_bundle={}

        _stale_inputs=_central_bundle.get("stale_inputs") or {}
        if _stale_inputs:
            _stale_labels={
                "relatorio_geral_tratado":"RELATÓRIO GERAL TRATADO",
                "estoque_tratado":"ESTOQUE TRATADO",
                "compras_tratado":"COMPRAS TRATADO",
                "tctp_tratado":"TCTP TRATADO",
            }
            _stale_names=[
                _stale_labels.get(_key,_key)
                for _key in _stale_inputs
            ]
            st.warning(
                "ATUALIZAÇÃO DETECTADA NA CENTRAL · "
                + " • ".join(_stale_names)
                + ". O MRP aguardará as bases tratadas atuais antes de recalcular."
            )

        if _central_bundle.get("ready"):
            cadastro_file,estoque_file,geral_file,compras_file,mt_file=_central_mrp.make_refs(_central_bundle)
        else:
            cadastro_file=estoque_file=geral_file=compras_file=mt_file=None

        st.markdown('<div class="sidebar-section-label sidebar-tools-label">ALIMENTAÇÃO</div>', unsafe_allow_html=True)
        with st.expander("CONTINGÊNCIA E RECUPERAÇÃO", expanded=False):
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

    else:
        cadastro_file=estoque_file=geral_file=compras_file=mt_file=None

    st.markdown("---")
    if st.button("SAIR", use_container_width=True, key="mrp_logout"):
        _logout()
"""
_source = _source[:_sidebar_start] + _central_sidebar + "\n" + _source[_sidebar_end:]

_status_helper = r"""
def _mrp_source_card_html(name,status,meta):
    version=meta.get("version")
    processed=meta.get("processed_at") or meta.get("last_update_at")
    when=_central_mrp.format_dt(processed)
    rows=meta.get("rows_count")
    details=[]
    if version not in (None,""):
        details.append(f"v{version}")
    if when!="—":
        details.append(when)
    if rows not in (None,""):
        try:
            details.append(f"{int(rows):,}".replace(",", ".")+" REGISTROS")
        except Exception:
            pass
    detail=" · ".join(details) if details else "—"
    return (
        '<div class="mrp-source-card">'
        f'<div class="mrp-source-name">{name}</div>'
        f'<div class="mrp-source-status">{status}</div>'
        f'<div class="mrp-source-meta">{detail}</div>'
        '</div>'
    )

def _render_mrp_central_status(bundle):
    if not bundle:
        return
    cad=bundle.get("cadastro_meta") or {}
    der=bundle.get("derived_meta") or {}
    cards=[
        _mrp_source_card_html("CADASTROS","ATUALIZADO" if cad.get("available") else "AGUARDANDO",cad),
        _mrp_source_card_html("RELATÓRIO GERAL TRATADO","ATUALIZADO" if (der.get("relatorio_geral_tratado") or {}).get("available") else "AGUARDANDO",der.get("relatorio_geral_tratado") or {}),
        _mrp_source_card_html("ESTOQUE TRATADO","ATUALIZADO" if (der.get("estoque_tratado") or {}).get("available") else "AGUARDANDO",der.get("estoque_tratado") or {}),
        _mrp_source_card_html("COMPRAS TRATADO","ATUALIZADO" if (der.get("compras_tratado") or {}).get("available") else "AGUARDANDO",der.get("compras_tratado") or {}),
        _mrp_source_card_html("TCTP TRATADO","ATUALIZADO" if (der.get("tctp_tratado") or {}).get("available") else "AGUARDANDO",der.get("tctp_tratado") or {}),
    ]
    st.markdown(
        '<div class="section-band"><div class="section-band-kicker">04 · FONTES</div>'
        '<div class="section-band-title">CENTRAL DE DADOS</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="mrp-source-grid">'+"".join(cards)+'</div>',unsafe_allow_html=True)

"""
_source = _source.replace(
    'if st.session_state.get("auth_role") == "CONSULTA":',
    _status_helper
    + '\nif st.session_state.get("auth_role") == "CONSULTA":',
    1,
)


_week_sidebar_legacy = 'with st.sidebar:\n    st.divider(); st.markdown("**Semana atual identificada nas bases**"); st.number_input("Semana atual",min_value=1,max_value=53,value=semana_atual,disabled=True); st.caption(f"Fonte: {fonte_semana}")\n'
if _week_sidebar_legacy in _source:
    _source = _source.replace(_week_sidebar_legacy, '', 1)

_load_old = 'try: cad,est,rg,rg_mrp,cp,mt=load_sources(cadastro_file.getvalue(),estoque_file.getvalue(),geral_file.getvalue(),compras_file.getvalue(),mt_file.getvalue())\nexcept Exception as e: st.error(f"Erro ao carregar as bases: {e}"); st.stop()'
_load_new = """try:
    if _mrp_use_manual:
        cad,est,rg,rg_mrp,cp,mt=load_sources(
            cadastro_file.getvalue(),
            estoque_file.getvalue(),
            geral_file.getvalue(),
            compras_file.getvalue(),
            mt_file.getvalue(),
        )
    else:
        cad,est,rg,rg_mrp,cp,mt=_mrp_load_sources_from_central(
            _central_bundle,
            str(_central_bundle.get("signature") or ""),
        )
except Exception as e:
    st.error(f"Erro ao carregar as bases: {e}")
    st.stop()"""
if _source.count(_load_old) != 1:
    raise RuntimeError("Chamada de leitura das cinco bases do MRP não encontrada.")
_source = _source.replace(_load_old, _load_new, 1)

_publish_anchor = '# Salva apenas uma vez por conjunto de arquivos carregado.'
_publish_code = r"""
# Publica automaticamente a Demanda_Projeto para os consumidores do Relatório MRP.
if st.session_state.get("auth_role") == "ADMIN" and not _mrp_use_manual and _central_bundle.get("ready"):
    try:
        _mrp_publish_result=_central_mrp.publish_relatorio_mrp_if_changed(
            demanda_projeto,
            _central_bundle.get("dependency_versions") or {},
            _central_bundle.get("output_meta") or {},
        )
        _mrp_output_meta=_mrp_publish_result.get("meta") or _central_bundle.get("output_meta") or {}
        _mrp_output_when=_central_mrp.format_dt(_mrp_output_meta.get("processed_at"))
        _mrp_output_rows=_mrp_output_meta.get("rows_count")
        st.markdown(
            '<div class="mrp-output-card">'
            '<div><div class="mrp-output-kicker">RELATÓRIO MRP</div>'
            '<div class="mrp-output-status">ATUALIZADO</div></div>'
            f'<div class="mrp-output-meta">{_mrp_output_when}'
            + (f' · {int(_mrp_output_rows):,} REGISTROS'.replace(",", ".") if _mrp_output_rows not in (None,"") else '')
            + '</div></div>',
            unsafe_allow_html=True,
        )
    except Exception as _publish_err:
        st.warning(f"MRP calculado, mas a publicação na Central falhou: {_publish_err}")

"""
if _source.count(_publish_anchor) != 1:
    raise RuntimeError("Ponto de publicação do Relatório MRP não encontrado.")
_source = _source.replace(_publish_anchor, _publish_code + "\n" + _publish_anchor, 1)

_mrp_sources_footer_anchor = """if len(compras_mrp): st.caption(f"Arquivo de compra gerado com {len(compras_mrp)} item(ns) que exigem nova S.C., considerando demandas S.A. e TC/TP.")
else: st.caption("Nenhum item das demandas S.A. ou TC/TP exige nova S.C. no momento.")
st.divider()"""
_mrp_sources_footer_new = """if len(compras_mrp): st.caption(f"Arquivo de compra gerado com {len(compras_mrp)} item(ns) que exigem nova S.C., considerando demandas S.A. e TC/TP.")
else: st.caption("Nenhum item das demandas S.A. ou TC/TP exige nova S.C. no momento.")
st.markdown('<div class="topic-divider"></div>', unsafe_allow_html=True)
if st.session_state.get("auth_role")=="ADMIN" and _central_bundle:
    _render_mrp_central_status(_central_bundle)"""
if _source.count(_mrp_sources_footer_anchor) != 1:
    raise RuntimeError("Rodapé dos relatórios do MRP não encontrado para posicionar FONTES.")
_source = _source.replace(_mrp_sources_footer_anchor, _mrp_sources_footer_new, 1)

_auto_save = """        if st.session_state.get("_mrp_saved_sig")!=_mrp_sig:
            if _mrp_sig in st.session_state.get("_mrp_pending_snapshots", {}):
                st.error("MRP calculado, mas o histórico ainda NÃO está confirmado. Use HISTÓRICO MRP PENDENTE no menu lateral para salvar sem recalcular.")
            else:
                save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp,cp,fab_det,calculation_key=_mrp_sig)
                st.session_state["_mrp_saved_sig"]=_mrp_sig
                st.success("MRP salvo no histórico compartilhado.")"""
_manual_history = """        _mrp_today=pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%Y-%m-%d")
        _mrp_daily_key=hashlib.sha256(f"MRP-DIARIO|{_mrp_today}".encode("utf-8")).hexdigest()
        if st.session_state.get("_mrp_daily_attempt_day")!=_mrp_today:
            st.session_state["_mrp_daily_attempt_day"]=_mrp_today
            save_snapshot(
                semana_atual,
                usuario_mrp,
                macro,
                proj,
                demanda_projeto,
                compras_mrp,
                cp,
                fab_det,
                calculation_key=_mrp_daily_key,
            )
            st.session_state["_mrp_saved_sig"]=_mrp_daily_key
            st.session_state["_mrp_daily_saved_day"]=_mrp_today"""
if _source.count(_auto_save) != 1:
    raise RuntimeError("Fluxo automático de histórico do MRP não encontrado.")
_source = _source.replace(_auto_save, _manual_history, 1)

_metric_anchor = 'm=st.columns(5);'
_history_ui = ""
if _source.count(_metric_anchor) != 1:
    raise RuntimeError("Ponto dos indicadores do MRP não encontrado.")
_source = _source.replace(_metric_anchor, _history_ui + "\n" + _metric_anchor, 1)
'''
