AVULSAS_PATCH = r'''
# ================================================================
# MRP | SOLICITAÇÕES AVULSAS — navegação + consulta autenticada
# ================================================================
_avulsas_nav_old = '_mrp_pages=["MRP ATUAL", "CONFIGURAÇÕES"] if _mrp_role=="ADMIN" else ["MRP ATUAL"]'
_avulsas_nav_new = '_mrp_pages=["MRP ATUAL", "SOLICITAÇÕES AVULSAS", "CONFIGURAÇÕES"] if _mrp_role=="ADMIN" else ["MRP ATUAL", "SOLICITAÇÕES AVULSAS"]'
if _source.count(_avulsas_nav_old) != 1:
    raise RuntimeError("Navegação do MRP não localizada para solicitações avulsas.")
_source = _source.replace(_avulsas_nav_old, _avulsas_nav_new, 1)

_avulsas_anchor = 'if not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):\n'
if _source.count(_avulsas_anchor) != 1:
    raise RuntimeError("Ponto da página avulsa não localizado.")

_avulsas_view = """
# Solicitações avulsas consomem exclusivamente a DIV do último MRP gravado.
# A API valida novamente quantidade e reservas no banco, sob bloqueio transacional.
def _mrp_avulsas_call(action,payload=None):
    import time as _av_tempo
    token=st.session_state.get("auth_access_token")
    if not token:
        raise RuntimeError("A sessão MRP expirou. Entre novamente.")
    if action=="list":
        _cached=st.session_state.get("_mrp_avulsas_lista_cache")
        if (_cached and _cached.get("token")==token
                and _cached.get("expires",0)>_av_tempo.monotonic()):
            return _cached["data"]
    url=f"{SUPABASE_URL}/functions/v1/mrp-avulsas-api"
    response=requests.post(
        url,
        headers={**_auth_headers(token)},
        json={"action":action,"payload":payload or {}},
        timeout=(8,50),
    )
    try:
        result=response.json()
    except ValueError:
        raise RuntimeError(f"Falha da API: HTTP {response.status_code}") from None
    if not response.ok or not result.get("ok"):
        raise RuntimeError(str(result.get("error") or f"HTTP {response.status_code}"))
    data=result.get("data") or {}
    if action=="list":
        st.session_state["_mrp_avulsas_lista_cache"]={
            "token":token,"data":data,"expires":_av_tempo.monotonic()+8,
        }
    else:
        # Qualquer confirmação bem-sucedida exige atualização na próxima tela.
        st.session_state.pop("_mrp_avulsas_lista_cache",None)
    return data

def _mrp_avulsas_view():
    st.markdown('<div class="section-band"><div class="section-band-kicker">01 · REQUISIÇÕES</div><div class="section-band-title">SOLICITAÇÕES AVULSAS DE MATERIAL</div></div>',unsafe_allow_html=True)
    try:
        dados=_mrp_avulsas_call("list")
    except Exception as exc:
        st.error("Não foi possível carregar as solicitações: "+str(exc))
        return
    perfil=str(dados.get("role") or "").upper()
    materiais=list(dados.get("materials") or [])
    solicitacoes=list(dados.get("rows") or [])
    pendentes=[x for x in solicitacoes if x.get("status")=="ABERTA"]
    separados=[x for x in solicitacoes if x.get("status")=="ATENDIDA"]
    recusadas=[x for x in solicitacoes if x.get("status")=="RECUSADA"]
    usuario_id=str(dados.get("user_id") or "")
    minhas=[x for x in solicitacoes if str(x.get("criado_por") or "")==usuario_id]
    meu_pendentes=[x for x in minhas if x.get("status")=="ABERTA"]
    meu_separados=[x for x in minhas if x.get("status")=="ATENDIDA"]
    minhas_recusadas=[x for x in minhas if x.get("status")=="RECUSADA"]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("MATERIAIS APTOS" if perfil=="CONSULTA" else "ITENS EM ABERTO",len(materiais) if perfil=="CONSULTA" else len(pendentes))
    c2.metric("SOLICITAÇÕES PENDENTES",len(pendentes))
    c3.metric("MATERIAIS SEPARADOS",len(separados))
    c4.metric("SOLICITAÇÕES RECUSADAS",len(recusadas))
    st.caption(f"BASE DE REFERÊNCIA · ÚLTIMO MRP GRAVADO #{dados.get('snapshot_id','—')}. Solicitações pendentes e separadas deste MRP reduzem a disponibilidade.")
    if perfil=="CONSULTA":
        st.caption("Materiais solicitáveis: saldo físico e sobra (DIV) positivos, respeitando reservas. A separação não realiza baixa no Protheus.")
    else:
        st.caption("Fila operacional de pedidos. A separação não realiza baixa no Protheus.")

    if str(dados.get("role"))=="ADMIN":
        with st.expander("CONEXÃO COM O TEAMS · TESTE",expanded=False):
            st.caption(
                "Verifica o webhook do grupo com uma mensagem identificada como TESTE. "
                "Nenhuma solicitação é criada e nenhum saldo é reservado."
            )
            if st.button("ENVIAR MENSAGEM DE TESTE AO TEAMS",key="mrp_teams_connection_test"):
                try:
                    _test=_mrp_avulsas_call("test_teams")
                    _state=str(_test.get("status") or "")
                    if _state=="ACEITO":
                        st.success("O webhook aceitou a mensagem. Confira se ela apareceu no grupo SOLICITAÇÃO DE ITENS AVULSOS - MRP.")
                    elif _state=="NAO_CONFIGURADO":
                        st.warning("A variável MRP_TEAMS_WORKFLOW_URL ainda não foi encontrada no Supabase.")
                    else:
                        st.error(f"Teste não enviado: {_test.get('error') or _test.get('message') or 'falha desconhecida'}")
                except Exception as exc:
                    st.error("Falha no teste Teams: "+str(exc))


    if perfil=="CONSULTA":
        import uuid as _uuid
        _snapshot = str(dados.get("snapshot_id") or "")
        _cart = st.session_state.setdefault("_mrp_cart",{})
        if st.session_state.get("_mrp_cart_snapshot")!=_snapshot:
            if _cart: st.warning("O MRP mudou; o pedido em preparação foi limpo para evitar saldo antigo.")
            _cart = {}
            st.session_state["_mrp_cart"] = _cart
            st.session_state["_mrp_cart_snapshot"] = _snapshot
            st.session_state["_mrp_cart_id"] = str(_uuid.uuid4())

        _last = st.session_state.get("_mrp_last_batch")
        if _last:
            st.success(f"Pedido registrado · {len(_last.get('ids') or [])} material(is) · protocolo {str(_last.get('pedido_id'))[:8]}")
            _teams_status=str(_last.get("teams_status") or "")
            if _teams_status=="ENVIADO":
                st.info("Notificação aceita pelo webhook do Teams.")
            else:
                st.warning({
                    "NAO_CONFIGURADO":"Integração Teams ainda não configurada; pedido salvo.",
                    "FALHA":"Pedido salvo, mas não foi possível notificar o Teams.",
                    "ENVIANDO":"Notificação em processamento.",
                }.get(_teams_status,"Notificação Teams ainda não confirmada."))
                if st.button("TENTAR NOTIFICAR TEAMS",key="mrp_batch_retry"):
                    try:
                        resp=_mrp_avulsas_call("notify_batch",{"pedido_id":_last["pedido_id"]})
                        _last["teams_status"]=resp.get("teams_status")
                        st.rerun()
                    except Exception as exc:
                        st.error("Pedido salvo, mas notificação falhou: "+str(exc))

        st.markdown("#### NOVA SOLICITAÇÃO")
        st.caption("Adicione os materiais primeiro; o registro e a reserva só ocorrem no envio final.")
        _available={str(x["codigo"]):x for x in materiais}
        if materiais:
            opcoes={
                f"{r['codigo']} · {r['descricao']} · SOLICITÁVEL: {r['disponivel']:,.3f}":r
                for r in materiais
            }
            # O seletor fica FORA do st.form: assim trocar o código força rerun,
            # atualizando o limite de quantidade ANTES de o usuário digitar.
            # Dentro do formulário, o Streamlit mantém o max do material anterior.
            escolha=st.selectbox(
                "MATERIAL",list(opcoes),index=None,
                placeholder="Pesquisar código ou descrição",
                key="mrp_avulsa_material_selecionado",
            )
            item=opcoes.get(escolha)
            _code=str(item["codigo"]) if item else ""
            _limit=float(item["disponivel"]) if item else 0.0
            _existing=float(_cart.get(_code,{}).get("quantidade",0))
            _room=max(0.0,_limit-_existing)
            with st.form("mrp_avulsa_criar",clear_on_submit=True,enter_to_submit=False):
                if item and _room>=0.001:
                    # Cada material possui seu próprio widget e intervalo:
                    # a quantidade do primeiro não reaparece no segundo.
                    quantidade=st.number_input(
                        "QUANTIDADE PARA ADICIONAR",min_value=0.001,
                        max_value=round(_room,3),value=min(1.0,round(_room,3)),
                        step=0.001,format="%.3f",
                        key=f"mrp_avulsa_quantidade_{_code}",
                    )
                    st.caption(
                        f"SALDO: {float(item['saldo']):,.3f} · "
                        f"SOBRA (DIV): {float(item['div']):,.3f} · "
                        f"DISPONÍVEL RESTANTE: {_room:,.3f}"
                    )
                    adicionar=st.form_submit_button(
                        "ADICIONAR MATERIAL À LISTA",type="primary",
                        use_container_width=True,
                    )
                else:
                    quantidade=0.0
                    if item:
                        st.info("Este material já atingiu seu limite na lista. Selecione outro material ou edite a revisão do pedido.")
                    else:
                        st.caption("Selecione um material acima para informar sua quantidade.")
                    adicionar=st.form_submit_button(
                        "ADICIONAR MATERIAL À LISTA",type="primary",
                        use_container_width=True,disabled=True,
                    )
            if adicionar:
                if not item: st.error("Selecione um material.")
                elif _room<0.001 or quantidade>_room+1e-9:
                    st.error("Quantidade superior à disponibilidade após reservas e itens da lista.")
                elif len(_cart)>=30 and _code not in _cart:
                    st.error("Máximo de 30 materiais diferentes por pedido.")
                else:
                    _cart[_code]={
                        "codigo":_code,"descricao":str(item["descricao"]),
                        "quantidade":round(_existing+float(quantidade),3),
                    }
                    st.session_state["_mrp_cart_id"]=str(_uuid.uuid4())
                    st.session_state["_mrp_cart_editor_id"]=str(_uuid.uuid4())
                    st.rerun()
        else:
            st.info("Não há materiais disponíveis para novas solicitações.")

        if _cart:
            st.markdown("#### REVISÃO DO PEDIDO")
            _rows=[{
                "Código":code,"Descrição":x["descricao"],
                "Quantidade":float(x["quantidade"]),
                "Disponível":float((_available.get(code) or {}).get("disponivel") or 0),
            } for code,x in _cart.items()]
            with st.form("mrp_avulsas_enviar_lote",enter_to_submit=False):
                _edited=st.data_editor(pd.DataFrame(_rows),hide_index=True,
                    use_container_width=True,disabled=["Código","Descrição","Disponível"],
                    key="mrp_cart_editor_"+st.session_state.setdefault(
                        "_mrp_cart_editor_id",str(_uuid.uuid4())),
                    column_config={
                        "Quantidade":st.column_config.NumberColumn(
                            "QUANTIDADE",min_value=0.001,step=0.001,format="%.3f",required=True),
                        "Disponível":st.column_config.NumberColumn("LIMITE",format="%.3f"),
                    })
                solicitante=st.text_input("SOLICITANTE",
                    value=str(st.session_state.get("auth_nome") or ""),max_chars=180)
                enviar=st.form_submit_button("REGISTRAR SOLICITAÇÃO",type="primary",
                    use_container_width=True)
            _remove_options={f"{r['Código']} · {r['Descrição']}":r["Código"] for r in _rows}
            c_remove,c_clear=st.columns([3,1])
            with c_remove:
                _target=st.selectbox("RETIRAR MATERIAL",list(_remove_options),key="mrp_cart_remove_choice")
                if st.button("REMOVER ITEM",key="mrp_cart_remove_button"):
                    _cart.pop(_remove_options[_target],None)
                    st.session_state["_mrp_cart_id"]=str(_uuid.uuid4())
                    st.session_state["_mrp_cart_editor_id"]=str(_uuid.uuid4())
                    st.rerun()
            with c_clear:
                st.write("")
                if st.button("LIMPAR LISTA",key="mrp_cart_clear"):
                    st.session_state["_mrp_cart"]={}
                    st.session_state["_mrp_cart_id"]=str(_uuid.uuid4())
                    st.rerun()
            if enviar:
                _lines=[]
                _error="" if solicitante.strip() else "Informe o solicitante."
                for _,r in _edited.iterrows():
                    _code=str(r["Código"])
                    _source=_available.get(_code)
                    _qty=pd.to_numeric(r["Quantidade"],errors="coerce")
                    if not _source:
                        _error=f"Material {_code} indisponível na base atual.";break
                    if pd.isna(_qty) or _qty<0.001 or round(float(_qty),3)!=float(_qty):
                        _error=f"Quantidade inválida para {_code}.";break
                    if float(_qty)>float(_source["disponivel"])+1e-9:
                        _error=f"Saldo insuficiente para {_code}; recalcule a quantidade.";break
                    _lines.append({"codigo":_code,"quantidade":float(_qty)})
                if _error:
                    st.error(_error)
                else:
                    _pedido_id=st.session_state.setdefault("_mrp_cart_id",str(_uuid.uuid4()))
                    try:
                        _result=_mrp_avulsas_call("create_batch",{
                            "pedido_id":_pedido_id,"solicitante":solicitante.strip(),
                            "itens":_lines,
                        })
                        st.session_state["_mrp_last_batch"]=_result
                        st.session_state["_mrp_cart"]={}
                        st.session_state["_mrp_cart_id"]=str(_uuid.uuid4())
                        st.session_state["_mrp_cart_editor_id"]=str(_uuid.uuid4())
                        st.rerun()
                    except Exception as exc:
                        st.error("Pedido não confirmado: "+str(exc))
    elif perfil=="OPERADOR":
        st.markdown("### FILA OPERACIONAL")
        st.caption("Acompanhe os pedidos e registre a separação ou recusa na aba PENDENTES DE SEPARAÇÃO.")
    else:
        st.markdown("### ACOMPANHAMENTO ADMINISTRATIVO")
        st.caption("Visão geral. Tratativas exclusivas do perfil OPERADOR.")

    st.markdown('<div class="topic-divider"></div>',unsafe_allow_html=True)
    if st.button("ATUALIZAR STATUS DAS SOLICITAÇÕES",key="mrp_avulsas_atualizar_status"):
        st.rerun()
    st.caption("O solicitante acompanha aqui a confirmação do operador. Use ATUALIZAR STATUS para consultar a situação mais recente.")
    if perfil in {"OPERADOR","ADMIN"}:
        tab_pendentes,tab_separadas,tab_recusadas=st.tabs([
            f"PENDENTES DE SEPARAÇÃO ({len(pendentes)})",
            f"SEPARADAS ({len(separados)})",
            f"RECUSADAS ({len(recusadas)})",
        ])
        tab_minhas=None
    else:
        tab_minhas,tab_separadas,tab_recusadas=st.tabs([
            f"MINHAS SOLICITAÇÕES ({len(minhas)})",
            f"SEPARADAS ({len(meu_separados)})",
            f"RECUSADAS ({len(minhas_recusadas)})",
        ])
        tab_pendentes=None

    def tabela(rows):
        view=pd.DataFrame(rows)
        campos=["id","codigo","descricao","quantidade","solicitante","status_exibicao",
                "criado_em","atendido_em","recusado_em","observacao_atendimento"]
        view=view.reindex(columns=campos)
        view=view.rename(columns={
            "id":"ID","codigo":"CÓDIGO","descricao":"DESCRIÇÃO",
            "quantidade":"QUANTIDADE","solicitante":"SOLICITANTE",
            "status_exibicao":"STATUS","criado_em":"SOLICITADO EM",
            "atendido_em":"SEPARADO EM","recusado_em":"RECUSADO EM",
            "observacao_atendimento":"OBSERVAÇÃO / MOTIVO DA RECUSA",
        })
        return view.fillna("")

    if tab_minhas is not None:
        with tab_minhas:
            if minhas:
                st.dataframe(tabela(minhas),use_container_width=True,hide_index=True,
                    height=min(560,38+35*len(minhas)))
                if minhas_recusadas:
                    st.warning(
                        f"{len(minhas_recusadas)} solicitação(ões) recusada(s). "
                        "Confira o motivo informado pelo operador na tabela."
                    )
                if meu_separados:
                    st.success(f"{len(meu_separados)} solicitação(ões) separada(s). Consulte as observações do operador.")
                elif meu_pendentes:
                    st.info("Suas solicitações aguardam separação pelo operador.")
            else:
                st.info("Você ainda não possui solicitações registradas nesta conta.")

    if tab_pendentes is not None:
        with tab_pendentes:
            if pendentes:
                _pendentes_df=tabela(pendentes)
                st.dataframe(_pendentes_df,use_container_width=True,hide_index=True,
                    height=min(560,38+35*len(_pendentes_df)))
                if perfil=="OPERADOR":
                    with st.form("mrp_avulsa_atender",enter_to_submit=False):
                        chaves={
                            f"#{x['id']} · {x['codigo']} · {x['quantidade']} · {x['solicitante']}":x['id']
                            for x in pendentes
                        }
                        alvo=st.selectbox("SOLICITAÇÃO PARA TRATATIVA",list(chaves.keys()))
                        obs=st.text_input(
                            "OBSERVAÇÃO AO SEPARAR / MOTIVO AO RECUSAR",
                            help="A recusa exige um motivo de pelo menos 5 caracteres.",
                        )
                        btn_sep,btn_rec=st.columns(2)
                        concluir=btn_sep.form_submit_button(
                            "CONFIRMAR MATERIAL SEPARADO",type="primary",use_container_width=True,
                        )
                        recusar=btn_rec.form_submit_button(
                            "RECUSAR SOLICITAÇÃO",use_container_width=True,
                        )
                    if concluir or recusar:
                        if recusar and len(obs.strip())<5:
                            st.error("Informe o motivo da recusa (mínimo 5 caracteres).")
                        else:
                            try:
                                if recusar:
                                    _mrp_avulsas_call("reject",{"id":chaves[alvo],"motivo":obs.strip()})
                                    st.success("Solicitação recusada. O motivo ficará disponível ao solicitante.")
                                else:
                                    _mrp_avulsas_call("attend",{"id":chaves[alvo],"observacao":obs})
                                    st.success("Separação confirmada. O novo status ficará disponível ao solicitante.")
                                st.rerun()
                            except Exception as exc:
                                st.error("Falha ao registrar tratativa: "+str(exc))
                else:
                    st.caption("Tratativas exclusivas do perfil OPERADOR.")
            else:
                st.success("Nenhuma solicitação pendente de separação.")

    with tab_separadas:
        linhas_separadas=separados if perfil in {"ADMIN","OPERADOR"} else meu_separados
        if linhas_separadas:
            st.dataframe(tabela(linhas_separadas),use_container_width=True,hide_index=True,
                height=min(560,38+35*len(linhas_separadas)))
        else:
            st.info("Nenhum material separado neste histórico.")

    with tab_recusadas:
        linhas_recusadas=recusadas if perfil in {"ADMIN","OPERADOR"} else minhas_recusadas
        if linhas_recusadas:
            st.dataframe(tabela(linhas_recusadas),use_container_width=True,hide_index=True,
                height=min(560,38+35*len(linhas_recusadas)))
        else:
            st.info("Nenhuma solicitação recusada neste histórico.")

    relatorio=tabela(solicitacoes)
    if not relatorio.empty:
        st.download_button(
            "EXPORTAR MINHAS SOLICITAÇÕES · EXCEL" if perfil=="CONSULTA" else "EXPORTAR TODAS AS SOLICITAÇÕES · EXCEL",
            excel_bytes({"Solicitacoes":relatorio}),
            "mrp_solicitacoes_avulsas.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

if _mrp_page=="SOLICITAÇÕES AVULSAS":
    _mrp_avulsas_view()
    st.stop()

"""
_source = _source.replace(_avulsas_anchor,_avulsas_view + _avulsas_anchor,1)
'''