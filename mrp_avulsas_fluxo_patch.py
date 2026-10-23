AVULSAS_FLUXO_PATCH = r'''
# Nova interface de pedidos por protocolo, com fluxo de finalidade e entrega.
_pedido_view_start=_source.index("def _mrp_avulsas_view():\n")
_pedido_view_end=_source.index('\nif _mrp_page=="SOLICITAÇÕES AVULSAS":',_pedido_view_start)
_pedido_nova_view = """def _mrp_avulsas_view():
    import re as _av_re
    import uuid as _av_uuid
    st.markdown('<style> .mrp-ped-hero{background:linear-gradient(110deg,#102c43,#1b5264); color:#fff;padding:19px 24px;border-radius:16px;margin:9px 0 17px} .mrp-ped-hero h2{color:#fff!important;font-size:24px!important;margin:4px 0 7px;font-weight:800} .mrp-ped-hero p{color:#e2f0f5!important;font-size:13px!important;margin:0} .mrp-ped-kicker{color:#a8e5e2;font-size:10px;letter-spacing:1.5px;font-weight:800} .mrp-ped-section{margin:16px 0 10px;padding:8px 13px;border-left:4px solid #193f59} .mrp-ped-section strong{font-size:18px;color:#17374e} .mrp-ped-section span{display:block;font-size:10px;color:#be3943;font-weight:800;letter-spacing:1px} .st-key-mrp_avulsa_area_selecao{border:2px solid #4a8293!important; background:rgba(229,242,246,.64)!important;border-radius:17px!important; padding:19px!important;box-shadow:0 5px 19px rgba(12,46,64,.09)} .st-key-mrp_avulsa_confirmacao{border:2px solid #285b76!important; border-radius:15px!important;padding:16px!important;background:rgba(232,241,247,.60)} .st-key-mrp_avulsa_area_selecao [data-testid="stForm"]{border:0!important;padding:0!important} div[data-testid="stMetric"]{border-radius:12px!important;min-height:84px!important} .mrp-ped-meta{font-size:12px;color:#547082;margin:8px 0 14px} .mrp-ped-item-head{font-size:11px;color:#667a8c;font-weight:750} .mrp-ped-item{padding:10px 4px;border-bottom:1px solid #d9e4eb} @media(max-width:780px){.mrp-ped-hero{padding:15px}.mrp-ped-hero h2{font-size:20px!important}} </style>',unsafe_allow_html=True)
    try:
        dados=_mrp_avulsas_call("list")
    except Exception as exc:
        st.error("Não foi possível carregar as solicitações: "+str(exc))
        return
    perfil=str(dados.get("role") or "").upper()
    pedidos=list(dados.get("pedidos") or [])
    email_eventos=list(dados.get("email_eventos") or [])
    itens=list(dados.get("rows") or [])
    materiais=list(dados.get("materials") or [])
    fonte_custo=dados.get("custo_referencia") or {}
    _titulos={
        "CONSULTA":"Solicitações de materiais",
        "OPERADOR":"Separação e entrega de materiais",
        "ADMIN":"Acompanhamento de requisições",
    }
    st.markdown(
        '<div class="mrp-ped-hero"><div class="mrp-ped-kicker">MRP SETTA · ALMOXARIFADO · '
        +perfil+'</div><h2>'+_titulos.get(perfil,"Solicitações")+'</h2>'
        '<p>Controle por solicitação: materiais, finalidade, separação, entrega e histórico.</p></div>',
        unsafe_allow_html=True,
    )
    _pendentes=[p for p in pedidos if p.get("estado")=="PENDENTE"]
    _separados=[p for p in pedidos if p.get("estado")=="SEPARADA"]
    _entregues=[p for p in pedidos if p.get("estado")=="ENTREGUE"]
    _recusados=[p for p in pedidos if p.get("estado")=="RECUSADA"]
    _legados_pendentes=[]
    _legados_separados=[]
    _legados_recusados=[]
    for _pedido_antigo in pedidos:
        if _pedido_antigo.get("estado")!="LEGADO":continue
        _filhos=[i for i in itens if str(i.get("pedido_id") or "")==str(_pedido_antigo.get("id") or "")]
        if not _filhos:continue
        if any(i.get("status")=="ABERTA" for i in _filhos):
            _legados_pendentes.append(_pedido_antigo)
        elif all(i.get("status")=="ATENDIDA" for i in _filhos):
            _legados_separados.append(_pedido_antigo)
        elif all(i.get("status")=="RECUSADA" for i in _filhos):
            _legados_recusados.append(_pedido_antigo)
        else:
            # Tratativas parciais anteriores continuam aparecendo no acompanhamento.
            _legados_separados.append(_pedido_antigo)
    _counters=st.columns(4 if perfil=="CONSULTA" else 3)
    if perfil=="CONSULTA":
        _counters[0].metric("MATERIAIS DISPONÍVEIS",len(materiais))
        _counters[1].metric("AGUARDANDO",len(_pendentes)+len(_legados_pendentes))
        _counters[2].metric("SEPARADAS",len(_separados)+len(_legados_separados))
        _counters[3].metric("ENTREGUES",len(_entregues))
    else:
        _counters[0].metric("AGUARDANDO SEPARAÇÃO",len(_pendentes)+len(_legados_pendentes))
        _counters[1].metric("SEPARADAS · NÃO ENTREGUES",len(_separados)+len(_legados_separados))
        _counters[2].metric("ENTREGUES",len(_entregues))
    st.markdown(
        '<div class="mrp-ped-meta"><b>MRP de referência #'
        +str(dados.get("snapshot_id") or "—")
        +'</b> · Disponibilidade validada pelo estoque, sobra DIV e reservas. '
        'A separação não efetua baixa no Protheus.</div>',unsafe_allow_html=True,
    )
    def _etapa(numero,titulo,descricao):
        st.markdown(
            '<div class="mrp-ped-section"><span>ETAPA '+str(numero)+'</span><strong>'
            +titulo+'</strong><div class="mrp-ped-meta">'+descricao+'</div></div>',
            unsafe_allow_html=True,
        )
    def _hora(valor):
        dt=pd.to_datetime(valor,utc=True,errors="coerce")
        return "" if pd.isna(dt) else dt.tz_convert("America/Sao_Paulo").strftime("%d/%m/%Y %H:%M")
    def _protocolo(p):
        valor=p.get("numero")
        return "SA-"+str(int(valor)).zfill(6) if valor is not None else str(p.get("id") or "")[:8]
    _labels={"GARANTIA":"GARANTIA","ACERTO_GERENCIAL":"ACERTO GERENCIAL",
             "TRANSFERENCIA":"TRANSFERÊNCIA ENTRE FILIAL"}
    def _itens_pedido(p):
        return [i for i in itens if str(i.get("pedido_id") or "")==str(p.get("id") or "")]
    def _dados_complementares(p):
        # Rotulos da interface e Excel; chaves de persistencia permanecem
        # psys/cr/aprovador/destino para preservar dados ja registrados.
        finalidade=str(p.get("finalidade") or "")
        return {
            "OP(s)":(str(p.get("psys") or "").strip() or "A PREENCHER NA ENTREGA")
                if finalidade=="GARANTIA" else "NA",
            "CR":(str(p.get("cr") or "").strip() or "A PREENCHER NA ENTREGA")
                if finalidade=="ACERTO_GERENCIAL" else "NA",
            "APROVADOR":(str(p.get("aprovador") or "").strip() or "A PREENCHER NA ENTREGA")
                if finalidade=="ACERTO_GERENCIAL" else "NA",
            "FILIAL":(str(p.get("destino") or "").strip() or "ASTEC")
                if finalidade=="TRANSFERENCIA" else "NA",
        }
    def _situacao_pedido(p,filhos):
        estado=str(p.get("estado") or "")
        if estado!="LEGADO":return estado or "SEM STATUS"
        statuses=[str(i.get("status") or "") for i in filhos]
        if "ABERTA" in statuses:return "AGUARDANDO SEPARAÇÃO"
        if statuses and all(i=="ATENDIDA" for i in statuses):return "SEPARADA"
        if statuses and all(i=="RECUSADA" for i in statuses):return "RECUSADA"
        if statuses:return "TRATATIVA PARCIAL"
        return "SEM STATUS"
    def _condicao_garantia(pedido,material):
        if pedido.get("finalidade")!="GARANTIA" or pedido.get("estado")!="ENTREGUE":
            return ""
        _codigo=str(material.get("destino_garantia") or "AGUARDANDO_RETORNO").upper()
        return {
            "AGUARDANDO_RETORNO":"AGUARDANDO RETORNO",
            "UTILIZADO":"UTILIZADO",
            "DEVOLVIDO":"DEVOLVIDO",
        }.get(_codigo,"AGUARDANDO RETORNO")
    def _condicao_garantia_relatorio(pedido,material):
        # "NA" para finalidades fora da garantia. Para garantia não entregue,
        # o retorno ainda não pode ser classificado (não é campo inaplicável).
        if pedido.get("finalidade")!="GARANTIA":
            return "NA"
        return _condicao_garantia(pedido,material) or "AGUARDANDO ENTREGA"
    def _mostrar_pedidos(lista,vazio,filtrar_itens=None,grupo="geral"):
        if not lista:
            st.info(vazio)
            return
        for p in lista:
            filhos=_itens_pedido(p)
            if filtrar_itens is not None:
                filhos=[i for i in filhos if filtrar_itens(i)]
            if not filhos:
                continue
            proto=_protocolo(p)
            titulo=proto+" · "+_labels.get(str(p.get("finalidade")), "SOLICITAÇÃO ANTERIOR")
            _estado_tela=_situacao_pedido(p,filhos)
            titulo+=" · "+_estado_tela
            with st.expander(titulo,expanded=False):
                _nome_col,_data_col,_situacao_col=st.columns([5,2.4,2.2],gap="medium")
                with _nome_col:
                    st.caption("SOLICITANTE")
                    st.write(str(p.get("solicitante") or "—"))
                with _data_col:
                    st.caption("SOLICITADO EM")
                    st.write(_hora(p.get("criado_em")) or "—")
                with _situacao_col:
                    st.caption("SITUAÇÃO")
                    st.write(_estado_tela)
                # Identificadores operacionais visiveis na separacao, entrega,
                # historico e acompanhamento, mesmo quando ainda pendentes.
                _identificacao=_dados_complementares(p)
                _campos_da_finalidade={
                    "GARANTIA":["OP(s)"],
                    "ACERTO_GERENCIAL":["CR","APROVADOR"],
                    "TRANSFERENCIA":["FILIAL"],
                }.get(str(p.get("finalidade") or ""),[])
                if _campos_da_finalidade:
                    st.markdown("**DADOS DA SOLICITAÇÃO**")
                    for _campo in _campos_da_finalidade:
                        _valor_identificacao=_identificacao[_campo]
                        st.write("**"+_campo+":** "+_valor_identificacao)
                if p.get("observacao_operador"):st.caption("Operador: "+str(p["observacao_operador"]))
                if perfil in {"OPERADOR","ADMIN"}:
                    _status_eventos=[e for e in email_eventos if str(e.get("pedido_id"))==str(p["id"])]
                    for _evento in _status_eventos:
                        _situacao=str(_evento.get("status") or "")
                        _tipo=str(_evento.get("tipo") or "")
                        st.caption("E-mail "+_tipo.lower()+": "+_situacao)
                        if _situacao not in {"ACEITO","ENVIANDO"} and st.button(
                            "TENTAR REENVIAR E-MAIL · "+_tipo,
                            key="email_retry_"+str(p["id"])+"_"+_tipo+"_"+grupo,
                        ):
                            try:
                                _r=_mrp_avulsas_call("email_retry",{
                                    "pedido_id":p["id"],"tipo":_tipo})
                                st.info("Situação do envio: "+str(_r.get("email_status")))
                                st.rerun()
                            except Exception as exc:st.error(str(exc))
                _linhas=[]
                _total=0.0
                _sem_preco=False
                for filho in filhos:
                    _valor=filho.get("valor_unitario_ref")
                    _referencia_atual=filho.get("valor_ultima_compra_atual")
                    _preco=float(_valor) if _valor is not None else None
                    if _preco is None:
                        _preco=float(_referencia_atual) if _referencia_atual is not None else 0.0
                    _subtotal=round(float(filho.get("quantidade") or 0)*_preco,2) if _preco is not None else None
                    if _subtotal is not None:_total+=_subtotal
                    _linhas.append({
                        "CÓDIGO":str(filho.get("codigo") or ""),
                        "DESCRIÇÃO":str(filho.get("descricao") or ""),
                        "QTD":float(filho.get("quantidade") or 0),
                        "UNITÁRIO R$":_preco,
                        "TOTAL R$":_subtotal,
                        "CONDIÇÃO GARANTIA":_condicao_garantia_relatorio(p,filho),
                    })
                if _linhas:
                    _planilha_pedido=pd.DataFrame(_linhas)
                    _planilha_pedido["UNITÁRIO R$"]=_planilha_pedido["UNITÁRIO R$"].map(
                        lambda n: "—" if pd.isna(n) else "R$ "+f"{float(n):,.2f}".replace(",","X").replace(".",",").replace("X","."))
                    _planilha_pedido["TOTAL R$"]=_planilha_pedido["TOTAL R$"].map(
                        lambda n: "—" if pd.isna(n) else "R$ "+f"{float(n):,.2f}".replace(",","X").replace(".",",").replace("X","."))
                    st.dataframe(_planilha_pedido,use_container_width=True,hide_index=True)
                    if not _sem_preco:
                        st.markdown("**Valor total de referência: R$ "+
                            f"{_total:,.2f}".replace(",","X").replace(".",",").replace("X",".")+"**")
                    if _sem_preco:
                        st.caption("Alguns materiais continuam sem custo identificado no CADASTROS. "
                                   "Não será exibido um total completo até obter todos os valores.")
                # Acoes no proprio cartao da S.A.: evita que o operador precise
                # procurar um formulario escondido no fim da fila.
                if perfil=="OPERADOR" and p.get("estado")=="PENDENTE":
                    st.markdown("**TRATATIVA DA "+proto+"**")
                    with st.form("mrp_avulsa_atender_"+str(p["id"]),enter_to_submit=False):
                        _obs=st.text_input("OBSERVAÇÃO / MOTIVO DA RECUSA",
                            key="obs_pedido_"+str(p["id"]))
                        _a,_b=st.columns(2)
                        _sep=_a.form_submit_button("CONFIRMAR MATERIAL SEPARADO",
                            type="primary",use_container_width=True)
                        _rec=_b.form_submit_button("RECUSAR SOLICITAÇÃO",
                            use_container_width=True)
                    if _sep or _rec:
                        if _rec and len(_obs.strip())<5:
                            st.error("A recusa exige motivo de pelo menos 5 caracteres.")
                        else:
                            try:
                                _resp=_mrp_avulsas_call("pedido_tratar",{
                                    "pedido_id":p["id"],
                                    "acao":"RECUSAR" if _rec else "SEPARAR",
                                    "observacao":_obs.strip(),
                                })
                                if _rec:
                                    _msg="Recusa registrada para "+proto+"."
                                else:
                                    _email_status=str(_resp.get("email_status") or "")
                                    _msg="Separação confirmada para "+proto+". "
                                    _msg+=("E-mail aceito pelo serviço."
                                      if _email_status=="ACEITO" else
                                      "E-mail ainda não configurado."
                                      if _email_status=="NAO_CONFIGURADO" else
                                      "Aviso por e-mail pendente de envio.")
                                st.session_state["_mrp_avulsas_operador_retorno"]=_msg
                                st.rerun()
                            except Exception as exc:
                                st.error("Não foi possível registrar a tratativa: "+str(exc))
                if perfil=="OPERADOR" and p.get("estado")=="SEPARADA":
                    st.markdown("**CONFIRMAR ENTREGA DA "+proto+"**")
                    with st.form("mrp_avulsa_entregar_"+str(p["id"]),enter_to_submit=False):
                        _psys=str(p.get("psys") or "")
                        _cr=str(p.get("cr") or "")
                        _aprovador=str(p.get("aprovador") or "")
                        if p.get("finalidade")=="GARANTIA":
                            _psys=st.text_area("OP(s) DA GARANTIA",
                                value=_psys,max_chars=1000,
                                key="psys_entrega_"+str(p["id"]),
                                help="Identificação obrigatória para o comunicado da entrega.")
                        elif p.get("finalidade")=="ACERTO_GERENCIAL":
                            _cr=st.text_input("CR DO ACERTO GERENCIAL",
                                value=_cr,max_chars=150,
                                key="cr_entrega_"+str(p["id"]))
                            _aprovador=st.text_input("APROVADOR DO ACERTO",
                                value=_aprovador,max_chars=180,
                                key="aprovador_entrega_"+str(p["id"]))
                        elif p.get("finalidade")=="TRANSFERENCIA":
                            st.caption("Destino de transferência: ASTEC.")
                        else:
                            st.error("Finalidade não cadastrada. Regularize antes da entrega.")
                        _confirmar=st.checkbox(
                            "Confirmo a entrega física de todos os materiais desta S.A.",
                            key="confirmar_entrega_"+str(p["id"]),
                        )
                        _entregar=st.form_submit_button("CONFIRMAR ENTREGA",
                            type="primary",use_container_width=True)
                    if _entregar:
                        if not _confirmar:
                            st.error("Confirme a entrega física antes de registrar.")
                        elif p.get("finalidade")=="GARANTIA" and len(_psys.strip())<2:
                            st.error("Informe a(s) OP(s) desta garantia.")
                        elif p.get("finalidade")=="ACERTO_GERENCIAL" and (
                            not _cr.strip() or len(_aprovador.strip())<2
                        ):
                            st.error("Informe o CR e o aprovador antes da entrega.")
                        else:
                            try:
                                _resp=_mrp_avulsas_call("pedido_tratar",{
                                    "pedido_id":p["id"],"acao":"ENTREGAR",
                                    "psys":_psys.strip(),"cr":_cr.strip(),
                                    "aprovador":_aprovador.strip(),
                                })
                                _email_status=str(_resp.get("email_status") or "")
                                _msg="Entrega confirmada para "+proto+". "
                                _msg+=("E-mail aceito pelo serviço."
                                    if _email_status=="ACEITO" else
                                    "E-mail ainda não configurado."
                                    if _email_status=="NAO_CONFIGURADO" else
                                    "Aviso por e-mail pendente de envio.")
                                st.session_state["_mrp_avulsas_operador_retorno"]=_msg
                                st.rerun()
                            except Exception as exc:
                                st.error("Não foi possível confirmar a entrega: "+str(exc))
                if perfil=="CONSULTA" and p.get("estado")=="ENTREGUE" and p.get("finalidade")=="GARANTIA" and filhos:
                    st.markdown("**CONDIÇÃO DOS MATERIAIS DE GARANTIA**")
                    st.caption("Cada material inicia como AGUARDANDO RETORNO. "
                               "Registre quando ele for UTILIZADO ou DEVOLVIDO; "
                               "a solicitação permanece no histórico.")
                    _choices={str(i["codigo"])+" · "+str(i.get("descricao") or "")+
                      " (#"+str(i["id"])+")":int(i["id"]) for i in filhos}
                    _alvo=st.selectbox("MATERIAL",list(_choices),key="garantia_item_"+str(p["id"])+"_"+grupo)
                    _id_escolhido=_choices[_alvo]
                    _item_escolhido=next(i for i in filhos if int(i["id"])==_id_escolhido)
                    _regularizacao_item=next(
                        (g for g in (dados.get("garantia_regularizacoes") or [])
                         if int(g.get("item_id") or 0)==_id_escolhido),
                        {},
                    )
                    _astec_liberada=bool(_regularizacao_item.get("astec_documento"))
                    _movimentacao_final=bool(_regularizacao_item.get("movimento_final_documento"))
                    if not _astec_liberada:
                        st.warning("Aguardando o gestor confirmar o endereçamento para ASTEC antes da decisão de uso/devolução.")
                    elif _movimentacao_final:
                        st.success("Destino já regularizado no Protheus: "+
                                   str(_regularizacao_item.get("movimento_final_tipo") or "")+
                                   " · Documento "+str(_regularizacao_item.get("movimento_final_documento") or ""))
                    else:
                        st.info("ASTEC confirmada. Informe se o material foi UTILIZADO ou DEVOLVIDO SEM USO.")
                    _opcoes=[
                        ("AGUARDANDO RETORNO","AGUARDANDO_RETORNO"),
                        ("UTILIZADO","UTILIZADO"),
                        ("DEVOLVIDO","DEVOLVIDO"),
                    ]
                    _rotulos=[o[0] for o in _opcoes]
                    _valor_atual=str(_item_escolhido.get("destino_garantia") or "AGUARDANDO_RETORNO")
                    _indice=next((i for i,o in enumerate(_opcoes) if o[1]==_valor_atual),0)
                    _resultado=st.selectbox(
                        "CONDIÇÃO DA GARANTIA",_rotulos,index=_indice,
                        key="garantia_status_"+str(p["id"])+"_"+str(_id_escolhido)+"_"+grupo,
                    )
                    _codigo_resultado=dict(_opcoes)[_resultado]
                    if st.button("SALVAR CONDIÇÃO DO MATERIAL",
                                 key="garantia_salvar_"+str(p["id"])+"_"+grupo,
                                 disabled=(not _astec_liberada or _movimentacao_final)):
                        if _codigo_resultado==_valor_atual:
                            st.toast("A condição deste material já está atualizada.",icon="ℹ️")
                        else:
                            try:
                                _mrp_avulsas_call("garantia_resultado",{
                                    "id":_id_escolhido,"resultado":_codigo_resultado})
                                st.session_state["_mrp_garantia_notificacao"]=(
                                    "Condição da garantia atualizada para "+_resultado+"."
                                )
                                st.rerun()
                            except Exception as exc:st.error(str(exc))

    _garantia_aviso=st.session_state.pop("_mrp_garantia_notificacao",None)
    if _garantia_aviso:
        st.toast(_garantia_aviso,icon="✅")
    if perfil=="CONSULTA":
        _snapshot=str(dados.get("snapshot_id") or "")
        _cart=st.session_state.setdefault("_mrp_cart",{})
        if st.session_state.get("_mrp_cart_snapshot")!=_snapshot:
            if _cart:st.warning("O MRP foi atualizado. Sua lista anterior foi limpa para conferir o saldo.")
            _cart={}
            st.session_state["_mrp_cart"]=_cart
            st.session_state["_mrp_cart_snapshot"]=_snapshot
            st.session_state["_mrp_cart_id"]=str(_av_uuid.uuid4())
        _last=st.session_state.get("_mrp_last_batch")
        if _last:
            _num_criado=_last.get("numero")
            _id_criado=("SA-"+str(int(_num_criado)).zfill(6)) if _num_criado is not None else str(_last.get("pedido_id") or "")[:8]
            st.success("Solicitação registrada · "+_id_criado)
            if _last.get("teams_status")!="ENVIADO":
                st.warning("Solicitação registrada; confirme a notificação no Teams.")
        _etapa("01","Selecionar materiais","Escolha um material e informe quanto deseja solicitar.")
        with st.container(key="mrp_avulsa_area_selecao",border=True):
            _available={str(i["codigo"]):i for i in materiais}
            if fonte_custo.get("status")=="FONTE_INDISPONIVEL":
                st.warning("CADASTROS indisponível para consulta do preço da coluna M. "
                           "Enquanto não houver leitura da fonte, o valor unitário será considerado R$ 0,00, "
                           "sem impedir a solicitação ou a entrega.")
            if not materiais:
                st.info("Nenhum material disponível para solicitar neste momento.")
            else:
                _options={str(m["codigo"])+" · "+str(m["descricao"]):m for m in materiais}
                escolha=st.selectbox("MATERIAL",list(_options),index=None,
                    placeholder="Pesquise pelo código ou pela descrição",
                    key="mrp_avulsa_material_selecionado")
                item=_options.get(escolha)
                _code=str(item["codigo"]) if item else ""
                _room=max(0.0,float(item.get("disponivel") or 0)-
                    float(_cart.get(_code,{}).get("quantidade",0))) if item else 0
                if item:
                    st.markdown("**"+str(item["codigo"])+" · "+str(item["descricao"])+"**")
                    m1,m2,m3=st.columns(3)
                    m1.metric("ESTOQUE",f'{float(item["saldo"]):,.3f}')
                    m2.metric("SOBRA (DIV)",f'{float(item["div"]):,.3f}')
                    m3.metric("DISPONÍVEL",f'{_room:,.3f}')
                with st.form("mrp_avulsa_criar",clear_on_submit=True,enter_to_submit=False):
                    if item and _room>=0.001:
                        quantidade=st.number_input(
                            "QUANTIDADE PARA ADICIONAR",min_value=0.001,
                            max_value=round(_room,3),value=min(1.0,round(_room,3)),
                            step=0.001,format="%.3f",key=f"mrp_avulsa_quantidade_{_code}")
                    else:
                        quantidade=0.0
                        st.caption("Selecione um material com disponibilidade acima para informar a quantidade.")
                    adicionar=st.form_submit_button("ADICIONAR MATERIAL À LISTA",
                        type="primary",use_container_width=True,
                        disabled=not (item and _room>=0.001))
                if adicionar:
                    if len(_cart)>=30 and _code not in _cart:
                        st.error("O pedido atingiu o limite operacional de materiais.")
                    else:
                        _cart[_code]={"codigo":_code,"descricao":str(item["descricao"]),
                           "quantidade":round(float(_cart.get(_code,{}).get("quantidade",0))
                              +float(quantidade),3)}
                        st.session_state["_mrp_cart_id"]=str(_av_uuid.uuid4())
                        st.rerun()
        if _cart:
            _etapa("02","Revisar itens","Corrija as quantidades ou remova qualquer material clicando no X da sua linha.")
            _cab=st.columns([2,7,2,1])
            for col,label in zip(_cab,["CÓDIGO","DESCRIÇÃO","QUANTIDADE",""]):
                col.caption(label)
            for code,item in list(_cart.items()):
                with st.container(border=True):
                    r1,r2,r3,r4=st.columns([2,7,2,1],vertical_alignment="center")
                    r1.write(code)
                    r2.write(str(item["descricao"]))
                    _limite=float((_available.get(code) or {}).get("disponivel") or 0)
                    _qty=r3.number_input("QUANTIDADE",min_value=0.001,
                        max_value=max(0.001,round(_limite,3)),
                        value=min(float(item["quantidade"]),max(0.001,round(_limite,3))),
                        step=0.001,format="%.3f",label_visibility="collapsed",key="revisar_"+code)
                    _cart[code]["quantidade"]=round(_qty,3)
                    if r4.button("✕",key="excluir_"+code,help="Remover este material"):
                        _cart.pop(code,None)
                        st.session_state["_mrp_cart_id"]=str(_av_uuid.uuid4())
                        st.rerun()
            if st.button("LIMPAR LISTA",key="mrp_cart_clear"):
                st.session_state["_mrp_cart"]={}
                st.session_state["_mrp_cart_id"]=str(_av_uuid.uuid4())
                st.rerun()
            _etapa("03","Finalidade e confirmação","Identifique o solicitante, selecione a finalidade e confirme os materiais.")
            with st.container(key="mrp_avulsa_confirmacao",border=True):
                with st.form("mrp_avulsas_enviar_lote",enter_to_submit=False):
                    solicitante=st.text_input("E-MAIL DO SOLICITANTE",
                        value=str(st.session_state.get("auth_email") or ""),
                        placeholder="nome.sobrenome@gruposetta.com")
                    _opcoes={
                       "GARANTIA":"GARANTIA",
                       "ACERTO GERENCIAL":"ACERTO_GERENCIAL",
                       "TRANSFERÊNCIA ENTRE FILIAL":"TRANSFERENCIA",
                    }
                    finalidade=st.selectbox("FINALIDADE",list(_opcoes),index=None,
                        placeholder="Selecione a finalidade")
                    psys=cr=aprovador=""
                    if finalidade=="GARANTIA":
                        psys=st.text_area("OP(s) DA GARANTIA",placeholder="Informe as OP(s) separadas por vírgula",
                            max_chars=1000)
                    elif finalidade=="ACERTO GERENCIAL":
                        cr=st.text_input("CR",max_chars=150)
                        aprovador=st.text_input("APROVADOR",max_chars=180)
                    elif finalidade=="TRANSFERÊNCIA ENTRE FILIAL":
                        st.info("Destino definido automaticamente: ASTEC")
                    enviar=st.form_submit_button("REGISTRAR SOLICITAÇÃO",type="primary",
                        use_container_width=True)
                if enviar:
                    _email=solicitante.strip().lower()
                    if not _av_re.fullmatch(r"[a-z0-9][a-z0-9._%+-]*[.][a-z0-9._%+-]+@gruposetta[.]com",_email):
                        st.error("Informe o e-mail corporativo completo no padrão nome.sobrenome@gruposetta.com.")
                    elif not finalidade:
                        st.error("Selecione a finalidade da solicitação.")
                    elif finalidade=="GARANTIA" and len(psys.strip())<2:
                        st.error("Informe pelo menos uma OP para garantia.")
                    elif finalidade=="ACERTO GERENCIAL" and (not cr.strip() or not aprovador.strip()):
                        st.error("Informe o CR e o aprovador.")
                    else:
                        _pedido_id=st.session_state.setdefault("_mrp_cart_id",str(_av_uuid.uuid4()))
                        _lines=[{"codigo":k,"quantidade":float(v["quantidade"])} for k,v in _cart.items()]
                        try:
                            _result=_mrp_avulsas_call("create_batch",{
                                "pedido_id":_pedido_id,"solicitante":_email,
                                "finalidade":_opcoes[finalidade],
                                "psys":psys.strip(),"cr":cr.strip(),
                                "aprovador":aprovador.strip(),"itens":_lines,
                            })
                            st.session_state["_mrp_last_batch"]=_result
                            st.session_state["_mrp_cart"]={}
                            st.session_state["_mrp_cart_id"]=str(_av_uuid.uuid4())
                            st.rerun()
                        except Exception as exc:st.error("Pedido não registrado: "+str(exc))

    # Exceções são rastreadas à parte e NUNCA ficam disponíveis ao operador antes
    # da aprovação e regularização Protheus. S.A. só nasce na última etapa.
    if perfil=="CONSULTA":
        with st.expander("SOLICITAÇÃO EXCEPCIONAL · UTILIZAÇÃO DE MATERIAL RESERVADO",expanded=False):
            st.warning("Esta modalidade NÃO libera automaticamente a reserva. "
                "A solicitação passa pela autorização do ADMIN e só entra na separação "
                "depois da confirmação de regularização da reserva no Protheus.")
            _cod_ex=st.text_input("CÓDIGO DO MATERIAL",placeholder="Ex.: 50590",
                key="mrp_exc_codigo")
            if st.button("CONSULTAR ESTOQUE FÍSICO",key="mrp_exc_lookup"):
                try:
                    _local=_mrp_avulsas_call("exception_lookup",{"codigo":_cod_ex.strip()})
                    st.session_state["_mrp_exc_material"]=_local
                    st.session_state["_mrp_exc_codigo_consultado"]=_cod_ex.strip().lstrip("0")
                except Exception as exc:
                    st.session_state.pop("_mrp_exc_material",None)
                    st.error("Consulta não realizada: "+str(exc))
            _mat_ex=st.session_state.get("_mrp_exc_material")
            if _mat_ex and _cod_ex.strip().lstrip("0")!=st.session_state.get("_mrp_exc_codigo_consultado"):
                _mat_ex=None
            if _mat_ex:
                st.markdown("**"+str(_mat_ex.get("codigo") or "")+" · "+
                            str(_mat_ex.get("descricao") or "")+"**")
                _e1,_e2,_e3=st.columns(3)
                _e1.metric("ESTOQUE FÍSICO",_mat_ex.get("saldo"))
                _e2.metric("DIV / SOBRA",_mat_ex.get("div"))
                _e3.metric("MRP REFERÊNCIA",str(_mat_ex.get("snapshot_id") or "—"))
                with st.form("mrp_exc_pedido_form",enter_to_submit=False):
                    _exc_qty=st.number_input("QUANTIDADE EXCEPCIONAL",
                        min_value=0.001,max_value=max(0.001,float(_mat_ex.get("saldo") or 0)),
                        value=min(1.0,float(_mat_ex.get("saldo") or 1)),
                        step=0.001,format="%.3f")
                    _exc_just=st.text_area("JUSTIFICATIVA DA UTILIZAÇÃO *",max_chars=1000,
                        placeholder="Explique por que será necessário utilizar material comprometido")
                    _exc_opts={"GARANTIA":"GARANTIA",
                        "ACERTO GERENCIAL":"ACERTO_GERENCIAL",
                        "TRANSFERÊNCIA ENTRE FILIAL":"TRANSFERENCIA"}
                    _exc_finalidade=st.selectbox("FINALIDADE DA SOLICITAÇÃO",
                        list(_exc_opts),index=None)
                    _exc_psys=_exc_cr=_exc_ap=""
                    if _exc_finalidade=="GARANTIA":
                        _exc_psys=st.text_input("OP(s) DE GARANTIA",max_chars=1000)
                    elif _exc_finalidade=="ACERTO GERENCIAL":
                        _exc_cr=st.text_input("CR",max_chars=150)
                        _exc_ap=st.text_input("APROVADOR DA FINALIDADE",max_chars=180)
                    _exc_submit=st.form_submit_button("ENCAMINHAR PARA AUTORIZAÇÃO",
                        type="primary",use_container_width=True)
                if _exc_submit:
                    if len(_exc_just.strip())<10:
                        st.error("Justificativa obrigatória (mínimo de 10 caracteres).")
                    elif not _exc_finalidade:
                        st.error("Selecione a finalidade.")
                    else:
                        try:
                            _resp=_mrp_avulsas_call("exception_submit",{
                                "id":st.session_state.setdefault("_mrp_exc_uuid",str(_av_uuid.uuid4())),
                                "codigo":_mat_ex["codigo"],"quantidade":_exc_qty,
                                "justificativa":_exc_just.strip(),
                                "finalidade":_exc_opts[_exc_finalidade],
                                "psys":_exc_psys.strip(),"cr":_exc_cr.strip(),
                                "aprovador":_exc_ap.strip(),
                            })
                            st.session_state["_mrp_exc_ultima"]=_resp
                            st.session_state["_mrp_exc_uuid"]=str(_av_uuid.uuid4())
                            st.session_state.pop("_mrp_exc_cache",None)
                            st.rerun()
                        except Exception as exc:
                            st.error("Solicitação excepcional não registrada: "+str(exc))
            _ultima_ex=st.session_state.pop("_mrp_exc_ultima",None)
            if _ultima_ex:
                st.success("Pedido excepcional registrado para análise do ADMIN. "
                    "NÃO está liberado para separação. ID: "+str(_ultima_ex.get("id") or ""))
            if st.button("CONSULTAR MINHAS EXCEÇÕES",key="mrp_exc_minhas"):
                try:
                    st.session_state["_mrp_exc_cache"]=_mrp_avulsas_call("exception_list").get("solicitacoes",[])
                except Exception as exc:st.error(str(exc))
            if "_mrp_exc_cache" in st.session_state:
                _minhas_ex=st.session_state["_mrp_exc_cache"]
                if _minhas_ex:
                    st.dataframe(pd.DataFrame([{
                        "SOLICITADO EM":_hora(e.get("criado_em")),
                        "CÓDIGO":e.get("codigo"),"QUANTIDADE":e.get("quantidade"),
                        "SITUAÇÃO":e.get("situacao"),
                        "S.A.":str(e.get("pedido_id") or "AGUARDANDO LIBERAÇÃO"),
                    } for e in _minhas_ex]),use_container_width=True,hide_index=True)
                else:st.info("Nenhuma solicitação excepcional cadastrada.")
    elif perfil=="ADMIN":
        with st.expander("ADMINISTRAÇÃO · AUTORIZAÇÕES DE MATERIAIS RESERVADOS",expanded=False):
            st.caption("Aprovação reserva capacidade física no MRP. Somente após comprovar "
                "a regularização da reserva original no Protheus é criada uma S.A. "
                "para a fila operacional. Autorizações antigas não passam automaticamente.")
            _carregar_exc=st.button("CARREGAR / ATUALIZAR EXCEÇÕES",key="mrp_exc_admin_load")
            if _carregar_exc or "_mrp_exc_admin_data" in st.session_state:
                if _carregar_exc or "_mrp_exc_admin_data" not in st.session_state:
                    try:
                        st.session_state["_mrp_exc_admin_data"]=_mrp_avulsas_call(
                            "exception_list").get("solicitacoes",[])
                    except Exception as exc:st.error("Consulta indisponível: "+str(exc))
                _ex_admin=st.session_state.get("_mrp_exc_admin_data",[])
                _atencao_ex=[e for e in _ex_admin if e.get("situacao") in ("PENDENTE","APROVADA")]
                st.metric("EXCEÇÕES AGUARDANDO TRATATIVA",len(_atencao_ex))
                if not _atencao_ex:st.info("Nenhuma exceção aguardando atuação.")
                for _ex in _atencao_ex:
                    _ex_id=str(_ex["id"])
                    _ex_codigo=str(_ex.get("codigo") or "")
                    with st.expander(
                        _ex_codigo+" · "+str(_ex.get("quantidade"))+" unidade(s) · "+
                        str(_ex.get("situacao")),expanded=False):
                        st.write("**Solicitante:** "+str(_ex.get("solicitante") or "—"))
                        st.write("**Material:** "+str(_ex.get("descricao") or ""))
                        st.write("**Justificativa:** "+str(_ex.get("justificativa") or ""))
                        st.caption("Estoque na solicitação: "+str(_ex.get("saldo_fisico_referencia"))+
                            " · DIV: "+str(_ex.get("div_referencia"))+
                            " · MRP #"+str(_ex.get("snapshot_id")))
                        if _ex.get("situacao")=="PENDENTE":
                            with st.form("mrp_exc_approve_"+_ex_id,enter_to_submit=False):
                                _ex_autorizador=st.text_input("GESTOR QUE AUTORIZOU *",
                                    key="mrp_exc_author_"+_ex_id)
                                _ex_ref=st.text_input("REFERÊNCIA DA AUTORIZAÇÃO *",
                                    key="mrp_exc_ref_"+_ex_id)
                                _ex_proj=st.text_input("PROJETO / OP COM RESERVA IMPACTADA *",
                                    key="mrp_exc_project_"+_ex_id)
                                _ex_obs=st.text_area("OBSERVAÇÕES (OPCIONAL)",
                                    key="mrp_exc_obs_"+_ex_id,max_chars=1000)
                                _ex_ok=st.form_submit_button("APROVAR EXCEÇÃO",
                                    type="primary",use_container_width=True)
                                _ex_no=st.form_submit_button("RECUSAR EXCEÇÃO",
                                    use_container_width=True)
                            if _ex_ok or _ex_no:
                                try:
                                    if _ex_no and len(_ex_obs.strip())<5:
                                        st.error("Informe o motivo da recusa nas observações.")
                                    else:
                                        _mrp_avulsas_call("exception_decide",{
                                            "id":_ex_id,"decisao":"APROVAR" if _ex_ok else "RECUSAR",
                                            "autorizador":_ex_autorizador.strip(),
                                            "referencia":_ex_ref.strip(),"projeto_op":_ex_proj.strip(),
                                            "observacao":_ex_obs.strip(),
                                        })
                                        st.session_state.pop("_mrp_exc_admin_data",None)
                                        st.success("Decisão registrada com rastreabilidade.")
                                        st.rerun()
                                except Exception as exc:
                                    st.error("Não foi possível registrar decisão: "+str(exc))
                        if _ex.get("situacao")=="APROVADA":
                            st.info("APROVADA. Projeto/OP afetado: "+
                                str(_ex.get("projeto_op_impactado"))+
                                ". Regularize a reserva original no Protheus antes de liberar.")
                            with st.form("mrp_exc_release_"+_ex_id,enter_to_submit=False):
                                _ex_doc=st.text_input("REFERÊNCIA DO DOCUMENTO DE REGULARIZAÇÃO *",
                                    key="mrp_exc_doc_"+_ex_id)
                                _ex_check=st.checkbox(
                                    "Confirmo que a reserva original foi regularizada no Protheus.",
                                    key="mrp_exc_check_"+_ex_id)
                                _ex_release=st.form_submit_button(
                                    "CONFIRMAR REGULARIZAÇÃO E CRIAR S.A.",
                                    type="primary",use_container_width=True)
                            if _ex_release:
                                if not _ex_check:
                                    st.error("Confirme a regularização antes da liberação.")
                                else:
                                    try:
                                        _resp=_mrp_avulsas_call("exception_regularize",{
                                            "id":_ex_id,"documento":_ex_doc.strip(),
                                            "confirmacao":True,
                                        })
                                        st.session_state.pop("_mrp_exc_admin_data",None)
                                        st.session_state["_mrp_exc_admin_result"]=_resp
                                        st.rerun()
                                    except Exception as exc:
                                        st.error("Liberação não concluída: "+str(exc))
            _exc_done=st.session_state.pop("_mrp_exc_admin_result",None)
            if _exc_done:
                st.success("Exceção regularizada; S.A. "+
                    ("SA-"+str(_exc_done["numero"]).zfill(6) if _exc_done.get("numero") is not None
                     else str(_exc_done.get("pedido_id")))+
                    " criada e disponibilizada ao almoxarifado.")
    st.divider()
    titulo="Minhas solicitações" if perfil=="CONSULTA" else "Fila operacional" if perfil=="OPERADOR" else "Acompanhamento geral"
    _c1,_c2=st.columns([5,1],vertical_alignment="center")
    _c1.markdown("### "+titulo)
    if _c2.button("ATUALIZAR STATUS",key="mrp_avulsas_atualizar_status",use_container_width=True):
        st.session_state.pop("_mrp_avulsas_lista_cache",None)
        st.rerun()
    def _tabela_geral_solicitacoes(_lista):
        # Visao analitica: uma linha por MATERIAL, repetindo a S.A. para cada item.
        # O detalhamento expansivel permanece exclusivamente nas abas de situacao.
        _linhas=[]
        _pedidos_ids={str(p.get("id") or "") for p in _lista}
        for _pedido in _lista:
            _filhos=_itens_pedido(_pedido)
            for _item in _filhos:
                _estado_item=str(_item.get("status") or "").upper()
                if str(_pedido.get("estado") or "")=="ENTREGUE":
                    _situacao="ENTREGUE"
                elif _estado_item=="ABERTA":
                    _situacao="AGUARDANDO SEPARAÇÃO"
                elif _estado_item=="ATENDIDA":
                    _situacao="SEPARADA"
                elif _estado_item=="RECUSADA":
                    _situacao="RECUSADA"
                else:
                    _situacao=_situacao_pedido(_pedido,_filhos)
                _linhas.append({
                    "S.A.":_protocolo(_pedido),
                    "SOLICITADO EM":_hora(_item.get("criado_em") or _pedido.get("criado_em")),
                    "SOLICITANTE":str(_pedido.get("solicitante") or "—"),
                    "FINALIDADE":_labels.get(str(_pedido.get("finalidade") or ""), "NÃO INFORMADA"),
                    **_dados_complementares(_pedido),
                    "CÓDIGO":str(_item.get("codigo") or ""),
                    "DESCRIÇÃO":str(_item.get("descricao") or ""),
                    "QUANTIDADE":float(_item.get("quantidade") or 0),
                    "SITUAÇÃO":_situacao,
                    "CONDIÇÃO GARANTIA":_condicao_garantia_relatorio(_pedido,_item),
                })
        # Manter itens históricos não associados a um protocolo, se existirem.
        for _item in itens:
            if _item.get("pedido_id") and str(_item.get("pedido_id")) in _pedidos_ids:
                continue
            if _item.get("pedido_id"):
                continue
            _estado_item=str(_item.get("status") or "").upper()
            _linhas.append({
                "S.A.":"REGISTRO #"+str(_item.get("id") or "—"),
                "SOLICITADO EM":_hora(_item.get("criado_em")),
                "SOLICITANTE":str(_item.get("solicitante") or "—"),
                "FINALIDADE":"NÃO INFORMADA",
                "OP(s)":"NA","CR":"NA","APROVADOR":"NA","FILIAL":"NA",
                "CÓDIGO":str(_item.get("codigo") or ""),
                "DESCRIÇÃO":str(_item.get("descricao") or ""),
                "QUANTIDADE":float(_item.get("quantidade") or 0),
                "SITUAÇÃO":{
                    "ABERTA":"AGUARDANDO SEPARAÇÃO",
                    "ATENDIDA":"SEPARADA",
                    "RECUSADA":"RECUSADA",
                }.get(_estado_item,_estado_item or "SEM STATUS"),
                "CONDIÇÃO GARANTIA":"NA",
            })
        return pd.DataFrame(_linhas,columns=[
            "S.A.","SOLICITADO EM","SOLICITANTE","FINALIDADE",
            "CÓDIGO","DESCRIÇÃO","QUANTIDADE","SITUAÇÃO","CONDIÇÃO GARANTIA",
            "OP(s)","CR","APROVADOR","FILIAL",
        ])
    def _agrupar_garantias_entregues(entregas):
        # Cada protocolo pode surgir nos dois grupos, porém apenas seus próprios
        # materiais pertinentes aparecem em cada um. Não altera o estado da S.A.
        _garantias=[]
        _aguardando=[]
        _confirmadas=[]
        _demais=[]
        _n_aguardando=0
        _n_confirmadas=0
        _n_utilizados=0
        _n_devolvidos=0
        for _pedido in entregas:
            if _pedido.get("finalidade")!="GARANTIA":
                _demais.append(_pedido)
                continue
            _garantias.append(_pedido)
            _filhos=_itens_pedido(_pedido)
            _pend=[i for i in _filhos if str(i.get("destino_garantia") or
                    "AGUARDANDO_RETORNO").upper() not in {"UTILIZADO","DEVOLVIDO"}]
            _con=[i for i in _filhos if str(i.get("destino_garantia") or "").upper()
                  in {"UTILIZADO","DEVOLVIDO"}]
            # Um pedido pertence somente a uma subaba: se algum material
            # aguarda resultado, a S.A. inteira permanece pendente.
            if _pend:
                _aguardando.append(_pedido)
                _n_aguardando+=len(_pend)
            elif _con:
                _confirmadas.append(_pedido)
            if _con:
                _n_confirmadas+=len(_con)
                _n_utilizados+=sum(str(i.get("destino_garantia")).upper()=="UTILIZADO"
                                   for i in _con)
                _n_devolvidos+=sum(str(i.get("destino_garantia")).upper()=="DEVOLVIDO"
                                   for i in _con)
        return {
            "garantias":_garantias,"aguardando":_aguardando,
            "confirmadas":_confirmadas,"demais":_demais,
            "itens_aguardando":_n_aguardando,
            "itens_confirmados":_n_confirmadas,
            "itens_utilizados":_n_utilizados,
            "itens_devolvidos":_n_devolvidos,
        }
    def _exibir_entregas():
        _grupos=_agrupar_garantias_entregues(_entregues)
        _tot_garantias=len(_grupos["garantias"])
        _tab_garantias,_tab_demais=st.tabs([
            "GARANTIAS ("+str(_tot_garantias)+" S.A.s)",
            "DEMAIS ENTREGAS ("+str(len(_grupos["demais"]))+" S.A.s)",
        ])
        with _tab_garantias:
            _aba_aguardando,_aba_confirmadas=st.tabs([
                "AGUARDANDO CONFIRMAÇÃO ("+str(len(_grupos["aguardando"]))+" S.A.s)",
                "CONFIRMADAS ("+str(len(_grupos["confirmadas"]))+" S.A.s)",
            ])
            with _aba_aguardando:
                st.caption("S.A.s com pelo menos um material aguardando resultado da ASTEC.")
                _mostrar_pedidos(
                    _grupos["aguardando"],
                    "Nenhum material de garantia aguardando confirmação.",
                    filtrar_itens=lambda item: str(item.get("destino_garantia") or
                        "AGUARDANDO_RETORNO").upper() not in {"UTILIZADO","DEVOLVIDO"},
                    grupo="garantia_pendente",
                )
            with _aba_confirmadas:
                st.caption("S.A.s com resultado da ASTEC informado para todos os materiais.")
                _mostrar_pedidos(
                    _grupos["confirmadas"],
                    "Nenhum material de garantia confirmado.",
                    filtrar_itens=lambda item: str(item.get("destino_garantia") or "").upper()
                        in {"UTILIZADO","DEVOLVIDO"},
                    grupo="garantia_confirmada",
                )
        with _tab_demais:
            _mostrar_pedidos(
                _grupos["demais"],
                "Nenhuma entrega de outras finalidades registrada.",
                grupo="outras_entregas",
            )
    if perfil=="OPERADOR":
        _retorno_operador=st.session_state.pop("_mrp_avulsas_operador_retorno",None)
        if _retorno_operador:
            _aviso_email=("não configurado" in _retorno_operador.lower()
                         or "pendente" in _retorno_operador.lower())
            st.toast(_retorno_operador,icon="⚠️" if _aviso_email else "✅")
        tab_pendentes,tab_separadas,tab_entregues,tab_recusadas=st.tabs([
            "PENDENTES ("+str(len(_pendentes)+len(_legados_pendentes))+")",
            "SEPARADAS ("+str(len(_separados)+len(_legados_separados))+")",
            "ENTREGUES ("+str(len(_entregues))+")",
            "RECUSADAS ("+str(len(_recusados)+len(_legados_recusados))+")",
        ])
        with tab_pendentes:
            _mostrar_pedidos(_pendentes+_legados_pendentes,
                            "Nenhuma solicitação aguardando separação.")
        with tab_pendentes:
            _ids_legado={str(p["id"]) for p in pedidos if p.get("estado")=="LEGADO"}
            _antigos=[i for i in itens if not i.get("pedido_id") or str(i.get("pedido_id")) in _ids_legado]
            if _antigos:
                with st.expander("REGISTROS ANTERIORES · CONFERÊNCIA POR MATERIAL",expanded=False):
                    st.caption("Registros anteriores preservados. Seus números originais continuam disponíveis.")
                    st.dataframe(pd.DataFrame(_antigos),use_container_width=True,hide_index=True)
                    _abertos=[i for i in _antigos if i.get("status")=="ABERTA"]
                    if perfil=="OPERADOR" and _abertos:
                        st.markdown("**Tratativa de pendências anteriores**")
                        with st.form("mrp_avulsa_legado_tratar",enter_to_submit=False):
                            chaves={
                               "#"+str(i["id"])+" · "+str(i.get("codigo"))+" · "+str(i.get("solicitante")):i["id"]
                               for i in _abertos
                            }
                            alvo=st.selectbox("SOLICITAÇÃO LEGADA",list(chaves))
                            obs=st.text_input("OBSERVAÇÃO / MOTIVO DA RECUSA",key="mrp_obs_legado")
                            sep,rec=st.columns(2)
                            separar=sep.form_submit_button("CONFIRMAR SEPARAÇÃO",type="primary")
                            recusar=rec.form_submit_button("RECUSAR ITEM")
                        if separar or recusar:
                            if recusar and len(obs.strip())<5:
                                st.error("Informe o motivo da recusa.")
                            else:
                                try:
                                    if recusar:
                                        _mrp_avulsas_call("reject",{"id":chaves[alvo],"motivo":obs.strip()})
                                    else:
                                        _mrp_avulsas_call("attend",{"id":chaves[alvo],"observacao":obs.strip()})
                                    st.rerun()
                                except Exception as exc:st.error(str(exc))
        with tab_separadas:
            _mostrar_pedidos(_separados+_legados_separados,
                            "Nenhum material aguardando entrega.")
        with tab_entregues:_exibir_entregas()
        with tab_recusadas:_mostrar_pedidos(_recusados+_legados_recusados,"Nenhuma solicitação recusada.")
    else:
        # CONSULTA e ADMIN: aba geral somente com tabela, detalhes nas abas de status.
        tabs=st.tabs([
          "MINHAS SOLICITAÇÕES ("+str(len(pedidos)) +")" if perfil=="CONSULTA"
              else "TODAS AS SOLICITAÇÕES ("+str(len(pedidos))+")",
          "AGUARDANDO SEPARAÇÃO ("+str(len(_pendentes)+len(_legados_pendentes))+")",
          "SEPARADAS ("+str(len(_separados)+len(_legados_separados))+")",
          "ENTREGUES ("+str(len(_entregues))+")",
          "RECUSADAS ("+str(len(_recusados)+len(_legados_recusados))+")",
        ])
        with tabs[0]:
            _tabela_itens=_tabela_geral_solicitacoes(pedidos)
            if not _tabela_itens.empty:
                st.caption(str(len(pedidos))+" solicitação(ões) · "+
                           str(len(_tabela_itens))+" linha(s) de materiais")
                st.dataframe(
                    _tabela_itens,
                    use_container_width=True,hide_index=True,
                    height=min(640,40+len(_tabela_itens)*36),
                    column_config={
                        "S.A.":st.column_config.TextColumn("S.A."),
                        "SOLICITADO EM":st.column_config.TextColumn("SOLICITADO EM"),
                        "SOLICITANTE":st.column_config.TextColumn("SOLICITANTE"),
                        "FINALIDADE":st.column_config.TextColumn("FINALIDADE"),
                        "CÓDIGO":st.column_config.TextColumn("CÓDIGO"),
                        "DESCRIÇÃO":st.column_config.TextColumn("DESCRIÇÃO",width="large"),
                        "QUANTIDADE":st.column_config.NumberColumn("QUANTIDADE",format="%.3f"),
                        "SITUAÇÃO":st.column_config.TextColumn("SITUAÇÃO"),
                        "CONDIÇÃO GARANTIA":st.column_config.TextColumn("CONDIÇÃO GARANTIA"),
                        "OP(s)":st.column_config.TextColumn("OP(s)"),
                        "CR":st.column_config.TextColumn("CR"),
                        "APROVADOR":st.column_config.TextColumn("APROVADOR"),
                        "FILIAL":st.column_config.TextColumn("FILIAL"),
                    },
                )
            else:
                st.info("Nenhuma solicitação registrada.")
        with tabs[1]:
            _mostrar_pedidos(
                _pendentes+_legados_pendentes,
                "Nenhuma solicitação aguardando separação.",
            )
        with tabs[2]:
            _mostrar_pedidos(
                _separados+_legados_separados,
                "Nenhuma solicitação separada.",
            )
        with tabs[3]:
            _exibir_entregas()
        with tabs[4]:
            _mostrar_pedidos(
                _recusados+_legados_recusados,
                "Nenhuma solicitação recusada.",
            )
    _exportar=_tabela_geral_solicitacoes(pedidos)
    if not _exportar.empty:
        st.download_button("EXPORTAR SOLICITAÇÕES · EXCEL",
           excel_bytes({"Materiais_por_SA":_exportar}),
           "mrp_solicitacoes_avulsas.xlsx",
           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
           use_container_width=True)
    if perfil=="ADMIN":
        with st.expander("ADMINISTRAÇÃO · DIAGNÓSTICO DE CUSTOS",expanded=False):
            st.caption("O diagnóstico de custos é carregado sob demanda para não atrasar a consulta de solicitações.")
            if st.button("CONSULTAR DIAGNÓSTICO DE CUSTOS",key="mrp_avulsas_cost_status"):
                try:
                    st.session_state["_mrp_avulsas_custo_diagnostico"]=_mrp_avulsas_call("cost_status")
                except Exception as exc:
                    st.error("Não foi possível consultar o cadastro: "+str(exc))
            _diag=st.session_state.get("_mrp_avulsas_custo_diagnostico")
            if _diag:
                st.write("Situação CADASTROS: "+str(_diag.get("status") or "—"))
                st.write("Campo encontrado: "+str(_diag.get("coluna") or "Não identificado"))
                st.write("Versão de referência: "+str(_diag.get("versao") or "—"))
                st.write("Códigos processados na coluna M: "+
                         str(_diag.get("codigos_com_valor") or 0))
        with st.expander("ADMINISTRAÇÃO · NOTIFICAÇÕES POR E-MAIL",expanded=False):
            st.caption("Separação: e-mail ao solicitante. Entrega: e-mail à gestão "+
                       "do almoxarifado, com cópia ao solicitante.")
            if st.button("VERIFICAR CONFIGURAÇÃO DE E-MAIL",key="mrp_email_config_check"):
                try:
                    _mailcfg=_mrp_avulsas_call("email_config_status")
                    _estado=str(_mailcfg.get("status") or "INDETERMINADO")
                    if _estado=="CONFIGURADO":
                        st.info("Integração cadastrada. Ainda é necessário confirmar "+
                                "um teste de entrega no Outlook.")
                    else:
                        st.warning("Serviço de e-mail: "+_estado+". Configure "+
                                   "MRP_EMAIL_WORKFLOW_URL no Supabase.")
                except Exception as exc:
                    st.error("Não foi possível conferir o serviço de e-mail: "+str(exc))
        with st.expander("ADMINISTRAÇÃO · TESTAR CONEXÃO COM O TEAMS",expanded=False):
            if st.button("ENVIAR MENSAGEM DE TESTE AO TEAMS",key="mrp_teams_connection_test"):
                try:
                    _test=_mrp_avulsas_call("test_teams")
                    if _test.get("status")=="ACEITO":st.success("Webhook aceitou o teste.")
                    else:st.warning(str(_test.get("message") or "Integração não configurada."))
                except Exception as exc:st.error(str(exc))

"""
_source=_source[:_pedido_view_start]+_pedido_nova_view+_source[_pedido_view_end:]
'''
