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
    token=st.session_state.get("auth_access_token")
    if not token:
        raise RuntimeError("A sessão MRP expirou. Entre novamente.")
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
    return result.get("data") or {}

def _mrp_avulsas_view():
    st.markdown('<div class="section-band"><div class="section-band-kicker">01 · REQUISIÇÕES</div><div class="section-band-title">SOLICITAÇÕES AVULSAS DE MATERIAL</div></div>',unsafe_allow_html=True)
    try:
        dados=_mrp_avulsas_call("list")
    except Exception as exc:
        st.error("Não foi possível carregar as solicitações: "+str(exc))
        return
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
    c1.metric("MATERIAIS APTOS",len(materiais))
    c2.metric("SOLICITAÇÕES PENDENTES",len(pendentes))
    c3.metric("MATERIAIS SEPARADOS",len(separados))
    c4.metric("SOLICITAÇÕES RECUSADAS",len(recusadas))
    st.caption(f"BASE DE REFERÊNCIA · ÚLTIMO MRP GRAVADO #{dados.get('snapshot_id','—')}. Solicitações pendentes e separadas deste MRP reduzem a disponibilidade.")
    st.caption("Só aparecem materiais com SALDO EM ESTOQUE > 0 e SOBRA (DIV) > 0. A quantidade liberada é limitada ao menor valor, descontando reservas. A separação não realiza baixa no Protheus.")

    st.markdown("#### NOVA SOLICITAÇÃO")
    if not materiais:
        st.info("Nenhum material possui DIV positiva ainda disponível para novas solicitações.")
    else:
        opcoes={
            f"{row['codigo']} · {row['descricao']} · SALDO: {row['saldo']:,.3f} · SOBRA: {row['div']:,.3f} · SOLICITÁVEL: {row['disponivel']:,.3f}": row
            for row in materiais
        }
        with st.form("mrp_avulsa_criar",clear_on_submit=True,enter_to_submit=False):
            escolha=st.selectbox("MATERIAL",list(opcoes.keys()),index=None,placeholder="Pesquisar código ou descrição")
            item=opcoes.get(escolha)
            maximo=float(item.get("disponivel") or 0) if item else 0.0
            quantidade=st.number_input(
                "QUANTIDADE SOLICITADA",min_value=0.001,
                max_value=max(0.001,maximo),
                value=min(1.0,max(0.001,maximo)),
                step=1.0,format="%.3f",
            )
            if item:
                st.caption(f"SALDO FÍSICO: {float(item['saldo']):,.3f} · SOBRA DO MRP (DIV): {float(item['div']):,.3f} · DISPONÍVEL APÓS RESERVAS: {maximo:,.3f}")
            solicitante=st.text_input("SOLICITANTE",value=str(st.session_state.get("auth_nome") or ""))
            enviar=st.form_submit_button("REGISTRAR SOLICITAÇÃO",type="primary",use_container_width=True)
        if enviar:
            if not item or not solicitante.strip():
                st.error("Selecione um material e informe o solicitante.")
            elif quantidade>maximo+1e-9:
                st.error("A quantidade solicitada ultrapassa o saldo/sobra disponível após reservas.")
            else:
                try:
                    _mrp_avulsas_call("create",{
                        "codigo":item["codigo"],"quantidade":float(quantidade),
                        "solicitante":solicitante.strip(),
                    })
                    st.success("Solicitação registrada no banco.")
                    st.rerun()
                except Exception as exc:
                    st.error("Não foi possível registrar a solicitação: "+str(exc))

    st.markdown('<div class="topic-divider"></div>',unsafe_allow_html=True)
    if st.button("ATUALIZAR STATUS DAS SOLICITAÇÕES",key="mrp_avulsas_atualizar_status"):
        st.rerun()
    st.caption("O solicitante acompanha aqui a confirmação do operador. Use ATUALIZAR STATUS para consultar a situação mais recente.")
    if str(dados.get("role"))=="ADMIN":
        tab_minhas,tab_pendentes,tab_separadas,tab_recusadas=st.tabs([
            f"MINHAS SOLICITAÇÕES ({len(minhas)})",
            f"PENDENTES DE SEPARAÇÃO ({len(pendentes)})",
            f"SEPARADAS ({len(separados)})",
            f"RECUSADAS ({len(recusadas)})",
        ])
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
                st.success("Nenhuma solicitação pendente de separação.")

    with tab_separadas:
        linhas_separadas=separados if str(dados.get("role"))=="ADMIN" else meu_separados
        if linhas_separadas:
            st.dataframe(tabela(linhas_separadas),use_container_width=True,hide_index=True,
                height=min(560,38+35*len(linhas_separadas)))
        else:
            st.info("Nenhum material separado neste histórico.")

    with tab_recusadas:
        linhas_recusadas=recusadas if str(dados.get("role"))=="ADMIN" else minhas_recusadas
        if linhas_recusadas:
            st.dataframe(tabela(linhas_recusadas),use_container_width=True,hide_index=True,
                height=min(560,38+35*len(linhas_recusadas)))
        else:
            st.info("Nenhuma solicitação recusada neste histórico.")

    relatorio=tabela(solicitacoes)
    if not relatorio.empty:
        st.download_button(
            "EXPORTAR TODAS AS SOLICITAÇÕES · EXCEL",
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