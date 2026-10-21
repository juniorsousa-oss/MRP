FINAL_ADMIN_PATCH = r"""
# Finalização independente da entrega física: registro obrigatório por ADMIN.
_av_final_anchor = '    if perfil=="ADMIN":\n        with st.expander("ADMINISTRAÇÃO · DIAGNÓSTICO DE CUSTOS",expanded=False):'
if _source.count(_av_final_anchor) != 1:
    raise RuntimeError("Conferência ADMIN: ponto das ferramentas administrativas não encontrado.")

_av_final_section = '''    if perfil=="ADMIN":
        st.markdown("---")
        st.markdown("### CONFERÊNCIA FINAL · ADMIN")
        st.caption(
            "A entrega física não encerra a regularização administrativa. "
            "Confirme o procedimento realizado no Protheus e guarde a referência "
            "documental. Esta etapa não executa baixa, emissão de NF ou transferência."
        )
        _conferencias_finais = {
            str(_c.get("pedido_id")): _c
            for _c in (dados.get("conferencias_finais") or [])
        }
        _rotulos_procedimento = {
            "TRANSFERENCIA": "Transferência de materiais",
            "BAIXA": "Baixa de materiais",
            "EMISSAO_NF": "Emissão de nota fiscal",
            "REGULARIZACAO_GARANTIA": "Garantia regularizada (ASTEC + baixa/retorno ao estoque)",
        }
        _entregues_pendentes = [
            _p for _p in _entregues if str(_p["id"]) not in _conferencias_finais
        ]
        _entregues_concluidas = [
            _p for _p in _entregues if str(_p["id"]) in _conferencias_finais
        ]
        _col_f1, _col_f2, _col_f3 = st.columns(3)
        _col_f1.metric("AGUARDANDO REGULARIZAÇÃO", len(_entregues_pendentes))
        _col_f2.metric("ENCERRADAS PELO ADMIN", len(_entregues_concluidas))
        _col_f3.metric(
            "AGUARDANDO ENTREGA", len(_pendentes) + len(_separados)
        )
        _tab_final_pendente, _tab_final_concluida = st.tabs([
            "PENDENTES DE CONFERÊNCIA ("+str(len(_entregues_pendentes))+")",
            "CONCLUÍDAS ("+str(len(_entregues_concluidas))+")",
        ])
        with _tab_final_pendente:
            if not _entregues_pendentes:
                st.success("Não existem entregas aguardando conferência final.")
            for _p in _entregues_pendentes:
                _proto = _protocolo(_p)
                _finalidade = str(_p.get("finalidade") or "")
                with st.expander(
                    _proto + " · " + _labels.get(_finalidade, _finalidade)
                    + " · Entregue em " + (_hora(_p.get("entregue_em")) or "—"),
                    expanded=False,
                ):
                    st.write("**Solicitante:** " + str(_p.get("solicitante") or "—"))
                    st.write("**Entrega registrada:** " + (_hora(_p.get("entregue_em")) or "—"))
                    _dados_identificacao = _dados_complementares(_p)
                    for _chave, _valor in _dados_identificacao.items():
                        if _valor != "NA":
                            st.write("**"+_chave+":** "+str(_valor))
                    _items_final = _itens_pedido(_p)
                    if _items_final:
                        st.dataframe(pd.DataFrame([{
                            "CÓDIGO": str(_i.get("codigo") or ""),
                            "DESCRIÇÃO": str(_i.get("descricao") or ""),
                            "QUANTIDADE": float(_i.get("quantidade") or 0),
                        } for _i in _items_final]),use_container_width=True,hide_index=True)
                    _permitidos = {
                        "GARANTIA": ["REGULARIZACAO_GARANTIA"],
                        "ACERTO_GERENCIAL": ["BAIXA","TRANSFERENCIA"],
                        "TRANSFERENCIA": ["EMISSAO_NF"],
                    }.get(_finalidade, [])
                    _rotulos_procedimento = {
                        "TRANSFERENCIA": "Transferência de materiais",
                        "BAIXA": "Baixa de materiais",
                        "EMISSAO_NF": "Emissão de nota fiscal",
                        "REGULARIZACAO_GARANTIA": "Garantia regularizada (ASTEC + baixa/retorno ao estoque)",
                    }
                    if _finalidade == "GARANTIA":
                        _regs_garantia = {
                            int(_r["item_id"]): _r
                            for _r in (dados.get("garantia_regularizacoes") or [])
                            if str(_r.get("pedido_id")) == str(_p["id"])
                        }
                        _astec_registrada = bool(_items_final) and all(
                            bool(_regs_garantia.get(int(_i["id"]), {}).get("astec_confirmado_em"))
                            for _i in _items_final
                        )
                        st.markdown("#### ETAPA 1 · TRANSFERÊNCIA À ASTEC")
                        if _astec_registrada:
                            _data_astec = _hora(
                                _regs_garantia[int(_items_final[0]["id"])].get("astec_confirmado_em")
                            )
                            st.success("TRANSFERÊNCIA CONFIRMADA · "+(_data_astec or "Registrada"))
                        elif not _regs_garantia:
                            if st.button(
                                "CONFIRMAR TRANSFERÊNCIA À ASTEC",
                                key="mrp_confirmar_astec_"+str(_p["id"]),
                                type="primary",use_container_width=True,
                            ):
                                try:
                                    _mrp_avulsas_call("garantia_astec_confirmar",{
                                        "pedido_id":_p["id"],
                                    })
                                    st.session_state["_mrp_final_admin_confirmado"] = (
                                        "Transferência à ASTEC confirmada · "+_proto
                                    )
                                    st.rerun()
                                except Exception as exc:
                                    st.error("Não foi possível confirmar a transferência: "+str(exc))
                        else:
                            st.warning("Registro ASTEC parcial. Consulte o histórico deste pedido.")

                        st.markdown("#### ETAPA 2 · RESULTADO DA ASTEC")
                        _resultados_astec = []
                        for _i in _items_final:
                            _destino = str(_i.get("destino_garantia") or "AGUARDANDO_RETORNO")
                            _status = {
                                "AGUARDANDO_RETORNO":"AGUARDANDO ANÁLISE",
                                "UTILIZADO":"UTILIZADO",
                                "DEVOLVIDO":"DEVOLVIDO SEM USO",
                            }.get(_destino,"AGUARDANDO ANÁLISE")
                            _resultados_astec.append({
                                "CÓDIGO":str(_i.get("codigo") or ""),
                                "DESCRIÇÃO":str(_i.get("descricao") or ""),
                                "RETORNO DA ASTEC":_status,
                            })
                        if _resultados_astec:
                            st.dataframe(
                                pd.DataFrame(_resultados_astec),
                                use_container_width=True,hide_index=True,
                            )
                        st.markdown("#### ETAPA 3 · CONFIRMAÇÃO FINAL POR MATERIAL")
                        _pendencias_finais = 0
                        for _i in _items_final:
                            _item_id = int(_i["id"])
                            _g = _regs_garantia.get(_item_id,{})
                            _destino = str(_i.get("destino_garantia") or "AGUARDANDO_RETORNO")
                            _concluido = bool(_g.get("movimento_final_confirmado_em"))
                            _rotulo = (
                                "CONFIRMAR BAIXA" if _destino=="UTILIZADO"
                                else "CONFIRMAR DEVOLUÇÃO AO ESTOQUE"
                            )
                            with st.container(border=True):
                                st.markdown(
                                    "**"+str(_i.get("codigo") or "")+" · "+
                                    str(_i.get("descricao") or "")+"**"
                                )
                                if _concluido:
                                    st.success(
                                        "FINALIZADO · "+(
                                            "BAIXA CONFIRMADA" if _destino=="UTILIZADO"
                                            else "DEVOLUÇÃO CONFIRMADA"
                                        )+" · "+_hora(_g.get("movimento_final_confirmado_em"))
                                    )
                                elif not _astec_registrada:
                                    _pendencias_finais += 1
                                    st.caption("Aguardando confirmação da transferência à ASTEC.")
                                elif _destino not in ("UTILIZADO","DEVOLVIDO"):
                                    _pendencias_finais += 1
                                    st.caption("Aguardando resultado da análise da ASTEC.")
                                else:
                                    _pendencias_finais += 1
                                    if st.button(
                                        _rotulo,
                                        key="mrp_confirmar_mov_final_"+str(_item_id),
                                        type="primary",use_container_width=True,
                                    ):
                                        try:
                                            _retorno_final=_mrp_avulsas_call(
                                                "garantia_movimento_final_confirmar",
                                                {"item_id":_item_id},
                                            )
                                            st.session_state["_mrp_final_admin_confirmado"] = (
                                                "Movimentação confirmada · "+
                                                str(_i.get("codigo") or "")
                                            )
                                            st.rerun()
                                        except Exception as exc:
                                            st.error("Não foi possível confirmar a movimentação: "+str(exc))
                        if _pendencias_finais==0 and _items_final:
                            st.success("Todos os itens regularizados. O encerramento da garantia é automático.")
                        continue
                    if not _permitidos:
                        st.error("Finalidade não elegível para conclusão administrativa.")
                        continue
                    st.markdown("**CHECKLIST DE ENCERRAMENTO ADMINISTRATIVO**")
                    with st.form("mrp_final_admin_"+str(_p["id"]), enter_to_submit=False):
                        _procedimento = st.selectbox(
                            "PROCEDIMENTO EXECUTADO",
                            _permitidos,
                            format_func=lambda v: _rotulos_procedimento.get(v,v),
                            key="mrp_procedimento_final_"+str(_p["id"]),
                        )
                        if _finalidade=="GARANTIA":
                            _documento = _documento_inicial
                            st.caption(
                                "Documento de referência para o encerramento: "+
                                (_documento or "aguardando ASTEC")+
                                ". As baixas e os retornos estão registrados individualmente."
                            )
                        else:
                            _documento = st.text_input(
                                "DOCUMENTO / REFERÊNCIA NO PROTHEUS *",
                                max_chars=120,
                                placeholder="Número da NF, baixa ou transferência",
                                key="mrp_documento_final_"+str(_p["id"]),
                            )
                        _check_materiais = st.checkbox(
                            "Conferi materiais, códigos e quantidades da solicitação.",
                            key="mrp_check_material_"+str(_p["id"]),
                        )
                        _check_movimentacao = st.checkbox(
                            "Confirmei que a movimentação foi efetivada no Protheus.",
                            key="mrp_check_movimento_"+str(_p["id"]),
                        )
                        _check_documento = st.checkbox(
                            "Conferi o documento e sua vinculação à solicitação.",
                            key="mrp_check_documento_"+str(_p["id"]),
                        )
                        _obs = st.text_area(
                            "OBSERVAÇÕES (OPCIONAL)",
                            max_chars=1000,
                            key="mrp_obs_final_"+str(_p["id"]),
                        )
                        _submit_final = st.form_submit_button(
                            "CONFIRMAR ENCERRAMENTO ADMINISTRATIVO",
                            type="primary", use_container_width=True,
                            disabled=(_finalidade=="GARANTIA" and not _ready_garantia),
                        )
                    if _submit_final:
                        if len(_documento.strip()) < 3:
                            st.error("Informe a referência do documento no Protheus (mínimo 3 caracteres).")
                        elif not all([_check_materiais,_check_movimentacao,_check_documento]):
                            st.error("Todos os três itens do checklist são obrigatórios.")
                        else:
                            try:
                                _mrp_avulsas_call("conferencia_final_confirmar", {
                                    "pedido_id": _p["id"],
                                    "procedimento": _procedimento,
                                    "documento_referencia": _documento.strip(),
                                    "confere_materiais": True,
                                    "confere_movimentacao": True,
                                    "confere_documento": True,
                                    "observacao": _obs.strip(),
                                })
                                st.session_state["_mrp_final_admin_confirmado"] = _proto
                                st.rerun()
                            except Exception as exc:
                                st.error("Não foi possível concluir a conferência: "+str(exc))
        with _tab_final_concluida:
            if not _entregues_concluidas:
                st.info("Nenhuma solicitação possui conferência final concluída.")
            _historico_final = []
            for _p in _entregues_concluidas:
                _conf = _conferencias_finais[str(_p["id"])]
                _linha_historico = {
                    "S.A.": _protocolo(_p),
                    "FINALIDADE": _labels.get(str(_p.get("finalidade")), "—"),
                    "SOLICITANTE": str(_p.get("solicitante") or ""),
                    "PROCEDIMENTO": _rotulos_procedimento.get(
                        str(_conf.get("procedimento")),str(_conf.get("procedimento") or "")
                    ),
                    "DOCUMENTO PROTHEUS": str(_conf.get("documento_referencia") or ""),
                    "CONFIRMADO EM": _hora(_conf.get("confirmado_em")),
                    "ADMIN RESPONSÁVEL": str(_conf.get("admin_nome") or _conf.get("confirmado_por") or ""),
                    "OBSERVAÇÃO": str(_conf.get("observacao") or ""),
                }
                _historico_final.append(_linha_historico)
            if _historico_final:
                st.dataframe(pd.DataFrame(_historico_final),use_container_width=True,hide_index=True)
                st.download_button(
                    "EXPORTAR CONFERÊNCIAS FINAIS (CSV)",
                    pd.DataFrame(_historico_final).to_csv(
                        index=False,sep=";"
                    ).encode("utf-8-sig"),
                    "mrp_conferencias_finais.csv",
                    mime="text/csv", use_container_width=True,
                    key="mrp_admin_exportar_conferencias",
                )
        _ultima_confirmacao = st.session_state.pop("_mrp_final_admin_confirmado",None)
        if _ultima_confirmacao:
            st.success("Conferência final registrada para "+_ultima_confirmacao+".")
'''
_source = _source.replace(
    _av_final_anchor, _av_final_section + "\n" + _av_final_anchor, 1
)

# Relatório enxuto: controle operacional e flags da ASTEC e validação final.
# As datas e demais movimentações ficam no histórico, não nas colunas da consulta/Excel.
_tabela_anchor = '                    "SITUAÇÃO":_situacao,\n                    "CONDIÇÃO GARANTIA":_condicao_garantia_relatorio(_pedido,_item),'
if _source.count(_tabela_anchor) != 1:
    raise RuntimeError("Relatório de conferência: linha base não localizada.")
_campos_relatorio = '''                    "SITUAÇÃO":_situacao,
                    "ASTEC REALIZADA": (
                        "SIM" if _garantias_por_item.get(str(_item.get("id")), {}).get("astec_confirmado_em")
                        else "NÃO"
                    ) if _pedido.get("finalidade")=="GARANTIA" else "N/A",
                    "VALIDAÇÃO FINAL": (
                        "SIM" if _conferencias_por_pedido.get(str(_pedido.get("id")), {}).get("confirmado_em")
                        else "NÃO"
                    ),'''
_source = _source.replace(_tabela_anchor,_campos_relatorio,1)

_initial_anchor = '    def _tabela_geral_solicitacoes(_lista):'
if _source.count(_initial_anchor) != 1:
    raise RuntimeError("Relatório de conferência: função analítica não localizada.")
_mapa_relatorio = '''    _conferencias_por_pedido = {
        str(c.get("pedido_id")): c for c in (dados.get("conferencias_finais") or [])
    }
    _garantias_por_item = {
        str(g.get("item_id")): g for g in (dados.get("garantia_regularizacoes") or [])
    }
'''
_source = _source.replace(_initial_anchor,_mapa_relatorio+_initial_anchor,1)

# Renomear apenas a coluna de saída; preservar OP(s) nos dados e outros formulários.
_retorno_anchor = '        return pd.DataFrame(_linhas,columns=['
if _source.count(_retorno_anchor) != 1:
    raise RuntimeError("Relatório de conferência: retorno da tabela não localizado.")
_source = _source.replace(_retorno_anchor,
    '        for _linha in _linhas:\n'
    '            _linha["OP"] = _linha.pop("OP(s)","NA")\n'
    + _retorno_anchor,1)

_cols_anchor = '''        return pd.DataFrame(_linhas,columns=[
            "S.A.","SOLICITADO EM","SOLICITANTE","FINALIDADE",
            "CÓDIGO","DESCRIÇÃO","QUANTIDADE","SITUAÇÃO","CONDIÇÃO GARANTIA",
            "OP(s)","CR","APROVADOR","FILIAL",
        ])'''
if _source.count(_cols_anchor) != 1:
    raise RuntimeError("Relatório de conferência: ordem de colunas não localizada.")
_source = _source.replace(_cols_anchor,
    '''        return pd.DataFrame(_linhas,columns=[
            "S.A.","SOLICITADO EM","SOLICITANTE",
            "CÓDIGO","DESCRIÇÃO","QUANTIDADE","SITUAÇÃO","FINALIDADE",
            "OP","CR","APROVADOR","FILIAL","ASTEC REALIZADA","VALIDAÇÃO FINAL",
        ])''',1)

# Linhas históricas sem protocolo não têm ASTEC nem fechamento rastreável.
_legacy_anchor = '                "CONDIÇÃO GARANTIA":"NA",'
if _source.count(_legacy_anchor) != 1:
    raise RuntimeError("Relatório de conferência: material legado não localizado.")
_source = _source.replace(_legacy_anchor,
    '                "ASTEC REALIZADA":"N/A","VALIDAÇÃO FINAL":"N/A",',1)

# O DataFrame de consulta e a exportação Excel usam a mesma ordem.
_config_anchor = '                        "SITUAÇÃO":st.column_config.TextColumn("SITUAÇÃO"),'
if _source.count(_config_anchor) != 1:
    raise RuntimeError("Relatório de conferência: configuração visual ausente.")
_source = _source.replace(_config_anchor,
    _config_anchor+'\n'
    '                        "ASTEC REALIZADA":st.column_config.TextColumn("ASTEC REALIZADA"),\n'
    '                        "VALIDAÇÃO FINAL":st.column_config.TextColumn("VALIDAÇÃO FINAL"),',
    1,
)
"""