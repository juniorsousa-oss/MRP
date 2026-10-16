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
    if perfil in {"ADMIN","OPERADOR"}:
        st.caption("Separadas: materiais com separação confirmada, mas sem registro de entrega. "
                   "Entregues: solicitações cuja entrega já foi confirmada pelo operador.")
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
    def _situacao_pedido(p,filhos):
        estado=str(p.get("estado") or "")
        if estado!="LEGADO":return estado or "SEM STATUS"
        statuses=[str(i.get("status") or "") for i in filhos]
        if "ABERTA" in statuses:return "AGUARDANDO SEPARAÇÃO"
        if statuses and all(i=="ATENDIDA" for i in statuses):return "SEPARADA"
        if statuses and all(i=="RECUSADA" for i in statuses):return "RECUSADA"
        if statuses:return "TRATATIVA PARCIAL"
        return "SEM STATUS"
    def _mostrar_pedidos(lista,vazio):
        if not lista:
            st.info(vazio)
            return
        for p in lista:
            filhos=_itens_pedido(p)
            proto=_protocolo(p)
            titulo=proto+" · "+_labels.get(str(p.get("finalidade")), "SOLICITAÇÃO ANTERIOR")
            _estado_tela=_situacao_pedido(p,filhos)
            titulo+=" · "+_estado_tela+" · "+str(len(filhos))+" material(is)"
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
                if p.get("psys"):st.write("**PSYs:** "+str(p["psys"]))
                if p.get("cr"):st.write("**CR:** "+str(p["cr"]))
                if p.get("aprovador"):st.write("**Aprovador:** "+str(p["aprovador"]))
                if p.get("destino"):st.write("**Destino:** "+str(p["destino"]))
                if p.get("observacao_operador"):st.caption("Operador: "+str(p["observacao_operador"]))
                if perfil in {"OPERADOR","ADMIN"}:
                    _status_eventos=[e for e in email_eventos if str(e.get("pedido_id"))==str(p["id"])]
                    for _evento in _status_eventos:
                        _situacao=str(_evento.get("status") or "")
                        _tipo=str(_evento.get("tipo") or "")
                        st.caption("E-mail "+_tipo.lower()+": "+_situacao)
                        if _situacao not in {"ACEITO","ENVIANDO"} and st.button(
                            "TENTAR REENVIAR E-MAIL · "+_tipo,
                            key="email_retry_"+str(p["id"])+"_"+_tipo,
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
                        "SITUAÇÃO GARANTIA":str(filho.get("destino_garantia") or ""),
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
                if perfil=="CONSULTA" and p.get("estado")=="ENTREGUE" and p.get("finalidade")=="GARANTIA" and filhos:
                    st.markdown("**Destinação dos materiais de garantia**")
                    _choices={str(i["codigo"])+" · "+str(i.get("descricao") or "")+
                      " (#"+str(i["id"])+")":int(i["id"]) for i in filhos}
                    _alvo=st.selectbox("MATERIAL",list(_choices),key="garantia_item_"+str(p["id"]))
                    _resultado=st.selectbox("RESULTADO",["UTILIZADO","DEVOLVIDO"],key="garantia_status_"+str(p["id"]))
                    if st.button("SALVAR SITUAÇÃO DO MATERIAL",key="garantia_salvar_"+str(p["id"])):
                        try:
                            _mrp_avulsas_call("garantia_resultado",{
                                "id":_choices[_alvo],"resultado":_resultado})
                            st.success("Resultado registrado sem apagar o histórico.")
                            st.rerun()
                        except Exception as exc:st.error(str(exc))

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
                        psys=st.text_area("PSY OU PSYs",placeholder="Informe os PSYs separados por vírgula",
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
                        st.error("Informe pelo menos um PSY para garantia.")
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
    st.divider()
    titulo="Minhas solicitações" if perfil=="CONSULTA" else "Fila operacional" if perfil=="OPERADOR" else "Acompanhamento geral"
    _c1,_c2=st.columns([5,1],vertical_alignment="center")
    _c1.markdown("### "+titulo)
    if _c2.button("ATUALIZAR STATUS",key="mrp_avulsas_atualizar_status",use_container_width=True):
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
                    "CÓDIGO":str(_item.get("codigo") or ""),
                    "DESCRIÇÃO":str(_item.get("descricao") or ""),
                    "QUANTIDADE":float(_item.get("quantidade") or 0),
                    "SITUAÇÃO":_situacao,
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
                "CÓDIGO":str(_item.get("codigo") or ""),
                "DESCRIÇÃO":str(_item.get("descricao") or ""),
                "QUANTIDADE":float(_item.get("quantidade") or 0),
                "SITUAÇÃO":{
                    "ABERTA":"AGUARDANDO SEPARAÇÃO",
                    "ATENDIDA":"SEPARADA",
                    "RECUSADA":"RECUSADA",
                }.get(_estado_item,_estado_item or "SEM STATUS"),
            })
        return pd.DataFrame(_linhas,columns=[
            "S.A.","SOLICITADO EM","SOLICITANTE","FINALIDADE",
            "CÓDIGO","DESCRIÇÃO","QUANTIDADE","SITUAÇÃO",
        ])
    if perfil=="OPERADOR":
        _retorno_operador=st.session_state.pop("_mrp_avulsas_operador_retorno",None)
        if _retorno_operador:
            st.success(_retorno_operador)
        tab_pendentes,tab_separadas,tab_entregues,tab_recusadas=st.tabs([
            "PENDENTES ("+str(len(_pendentes)+len(_legados_pendentes))+")",
            "SEPARADAS ("+str(len(_separados)+len(_legados_separados))+")",
            "ENTREGUES ("+str(len(_entregues))+")",
            "RECUSADAS ("+str(len(_recusados)+len(_legados_recusados))+")",
        ])
        with tab_pendentes:
            _mostrar_pedidos(_pendentes+_legados_pendentes,"Nenhuma solicitação aguardando separação.")
            if _pendentes:
                with st.form("mrp_avulsa_atender",enter_to_submit=False):
                    _choices={_protocolo(p)+" · "+str(p.get("solicitante")):p["id"] for p in _pendentes}
                    alvo=st.selectbox("SOLICITAÇÃO PARA TRATATIVA",list(_choices))
                    obs=st.text_input("OBSERVAÇÃO OU MOTIVO DA RECUSA")
                    t1,t2=st.columns(2)
                    concluir=t1.form_submit_button("CONFIRMAR MATERIAL SEPARADO",
                        type="primary",use_container_width=True)
                    recusar=t2.form_submit_button("RECUSAR SOLICITAÇÃO",
                        use_container_width=True)
                if concluir or recusar:
                    if recusar and len(obs.strip())<5:
                        st.error("A recusa exige motivo de pelo menos 5 caracteres.")
                    else:
                        try:
                            resposta=_mrp_avulsas_call("pedido_tratar",{
                              "pedido_id":_choices[alvo],"acao":"RECUSAR" if recusar else "SEPARAR",
                              "observacao":obs.strip()})
                            if concluir:
                                _st_email=str(resposta.get("email_status") or "")
                                st.session_state["_mrp_avulsas_operador_retorno"]=(
                                    "Separação registrada. E-mail aceito pelo serviço."
                                    if _st_email=="ACEITO" else
                                    "Separação registrada. Notificação por e-mail: "+
                                    ("ainda não configurada" if _st_email=="NAO_CONFIGURADO"
                                     else "pendente de envio ou reenvio")+"."
                                )
                            elif recusar:
                                st.session_state["_mrp_avulsas_operador_retorno"]="Recusa registrada."
                            st.rerun()
                        except Exception as exc:st.error(str(exc))
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
            _mostrar_pedidos(_separados+_legados_separados,"Nenhum material aguardando entrega.")
            if _separados:
                st.markdown("#### Confirmar entrega da solicitação")
                st.caption("A confirmação registra a entrega dos materiais da S.A. selecionada. "
                           "Os dados da finalidade são necessários para a comunicação à gestão.")
                # Seleção FORA do formulário: ao trocar de S.A., os campos por finalidade
                # devem mudar imediatamente, antes da confirmação.
                _choices={_protocolo(p)+" · "+str(p.get("solicitante")):p["id"] for p in _separados}
                alvo=st.selectbox("SOLICITAÇÃO PARA ENTREGA",list(_choices),
                                  key="mrp_operador_sa_entrega")
                _pedido_entrega=next(p for p in _separados if p["id"]==_choices[alvo])
                _psys_entrega=str(_pedido_entrega.get("psys") or "")
                _cr_entrega=str(_pedido_entrega.get("cr") or "")
                _aprovador_entrega=str(_pedido_entrega.get("aprovador") or "")
                with st.form("mrp_avulsa_entregar",enter_to_submit=False):
                    if _pedido_entrega.get("finalidade")=="GARANTIA":
                        _psys_entrega=st.text_area(
                            "PSY OU PSYs DA GARANTIA",
                            value=_psys_entrega,
                            max_chars=1000,
                            help="Obrigatório na entrega. Informe os PSYs que serão citados no e-mail.",
                        )
                    elif _pedido_entrega.get("finalidade")=="ACERTO_GERENCIAL":
                        _cr_entrega=st.text_input(
                            "CR DO ACERTO GERENCIAL",value=_cr_entrega,max_chars=150,
                        )
                        _aprovador_entrega=st.text_input(
                            "APROVADOR DO ACERTO",value=_aprovador_entrega,max_chars=180,
                        )
                    elif _pedido_entrega.get("finalidade")=="TRANSFERENCIA":
                        st.caption("Destino da transferência: ASTEC.")
                    else:
                        st.error("Esta solicitação está sem finalidade cadastrada. "
                                 "Regularize antes de confirmar a entrega.")
                    confirmar=st.checkbox(
                        "Confirmo a entrega física de todos os materiais desta S.A.",
                    )
                    entregar=st.form_submit_button(
                        "CONFIRMAR ENTREGA",type="primary",use_container_width=True,
                    )
                if entregar:
                    if not confirmar:
                        st.error("Confirme a entrega física antes de registrar.")
                    elif _pedido_entrega.get("finalidade")=="GARANTIA" and len(_psys_entrega.strip())<2:
                        st.error("Informe os PSYs da garantia para concluir a entrega.")
                    elif _pedido_entrega.get("finalidade")=="ACERTO_GERENCIAL" and (
                        not _cr_entrega.strip() or len(_aprovador_entrega.strip())<2
                    ):
                        st.error("Informe o CR e o aprovador para concluir a entrega.")
                    else:
                        try:
                            resultado=_mrp_avulsas_call("pedido_tratar",{
                                "pedido_id":_choices[alvo],"acao":"ENTREGAR",
                                "psys":_psys_entrega.strip(),
                                "cr":_cr_entrega.strip(),
                                "aprovador":_aprovador_entrega.strip(),
                            })
                            _status_envio=str(resultado.get("email_status") or "")
                            st.session_state["_mrp_avulsas_operador_retorno"]=(
                                "Entrega registrada. E-mail à gestão aceito pelo serviço."
                                if _status_envio=="ACEITO" else
                                "Entrega registrada. Notificação por e-mail: "+
                                ("ainda não configurada" if _status_envio=="NAO_CONFIGURADO"
                                 else "pendente de envio ou reenvio")+"."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error("Entrega não registrada: "+str(exc))
        with tab_entregues:_mostrar_pedidos(_entregues,"Nenhum pedido entregue.")
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
            _mostrar_pedidos(_entregues,"Nenhuma solicitação entregue.")
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
            st.write("Situação CADASTROS: "+str(fonte_custo.get("status") or "—"))
            st.write("Campo encontrado: "+str(fonte_custo.get("coluna") or "Não identificado"))
            st.write("Versão de referência: "+str(fonte_custo.get("versao") or "—"))
            st.write("Códigos processados na coluna M (incluindo valores zero): "+
                     str(fonte_custo.get("codigos_com_valor") or 0))
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
