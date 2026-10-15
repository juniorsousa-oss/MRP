AVULSAS_UX_PATCH = r'''
# Redesenho de interface da aba de Solicitações Avulsas.
# Apenas apresentação: não interfere na API, nas reservas nem nas permissões.
def _avulsa_ux_substituir(antigo, novo, rotulo):
    global _source
    quantidade=_source.count(antigo)
    if quantidade!=1:
        raise RuntimeError(f"UX Solicitações: esperado um ponto '{rotulo}', encontrados {quantidade}.")
    _source=_source.replace(antigo,novo,1)

_avulsa_css = """
<style>
/* Estilos exclusivamente da página de solicitações avulsas */
.mrp-av-hero{
    background:linear-gradient(115deg,#10283e 0%,#173a55 55%,#235d73 100%);
    border:1px solid #294d63; border-radius:20px; padding:25px 30px;
    margin:8px 0 20px; display:flex; align-items:center; justify-content:space-between;
    gap:14px; box-shadow:0 12px 32px rgba(12,34,52,.12); color:#fff;
}
.mrp-av-hero h2{font-size:23px;line-height:1.22;font-weight:750;margin:8px 0;color:#fff}
.mrp-av-hero p{font-size:13px;max-width:760px;line-height:1.6;color:#e4edf3;margin:0}
.mrp-av-eyebrow{font-size:10px;letter-spacing:1.3px;text-transform:uppercase;font-weight:750;color:#80d9d9}
.mrp-av-profile{border:1px solid rgba(255,255,255,.32);color:#fff;font-size:10px;
  background:rgba(255,255,255,.09);font-weight:750;letter-spacing:.5px;
  border-radius:20px;padding:9px 15px;white-space:nowrap}
.mrp-av-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:10px 0 25px}
.mrp-av-step{background:var(--secondary-background-color,#f8fafc);border:1px solid #dbe5ed;
  border-radius:14px;min-height:66px;padding:14px 16px;display:flex;align-items:center;gap:12px}
.mrp-av-step strong{display:block;color:var(--text-color,#1c2936);font-size:12px}
.mrp-av-step small{display:block;color:#6a7988;font-size:11px;margin-top:3px}
.mrp-av-index{background:#e7f0f4;color:#18364b;border-radius:10px;
  width:32px;height:32px;display:flex;justify-content:center;
  align-items:center;font-size:12px;font-weight:800;flex-shrink:0}
.mrp-av-section{border-left:4px solid #16364e;padding:8px 0 8px 16px;margin:20px 0 10px}
.mrp-av-section span{display:block;font-size:10px;letter-spacing:1px;font-weight:750;color:#c14548}
.mrp-av-section strong{display:block;font-size:19px;font-weight:750;color:var(--text-color,#152d42);margin-top:2px}
.mrp-av-section small{display:block;font-size:12px;color:#728294;margin-top:5px;line-height:1.5}
.mrp-av-helper{background:#f1f6f8;border:1px solid #dce8ed;border-radius:12px;
  font-size:12px;color:#38556a;padding:12px 16px;margin:8px 0 15px;line-height:1.5}
.mrp-av-item{background:#f4f8fa;border:1px solid #d6e4ec;border-radius:14px;
  padding:14px 20px;margin:12px 0 6px}
.mrp-av-item b{font-weight:800;color:#14334a;font-size:13px}
.mrp-av-item p{font-size:12px;line-height:1.5;margin:4px 0;color:#52697c}
.mrp-av-rule{border-top:1px solid #dbe4eb;margin:28px 0 18px}
.mrp-av-note{color:#687b8b;font-size:11px;line-height:1.55;margin:4px 0 16px}
div[data-testid="stMetric"]{
    padding:15px 17px;border:1px solid #d9e4ec;border-radius:15px;
    background:var(--secondary-background-color,#fff);
    box-shadow:0 3px 13px rgba(18,42,61,.04);min-height:100px
}
div[data-testid="stMetric"] [data-testid="stMetricLabel"]{font-weight:750;font-size:11px}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{font-weight:750;font-size:25px}
div[data-testid="stDataFrame"]{border-radius:13px;overflow:hidden}
div[data-testid="stForm"]{border:1px solid #d7e3ed;border-radius:14px;padding:15px 18px}
@media(max-width:780px){
  .mrp-av-hero{padding:18px;align-items:flex-start;flex-direction:column;border-radius:16px}
  .mrp-av-hero h2{font-size:19px}
  .mrp-av-steps{grid-template-columns:1fr;gap:7px}
  .mrp-av-step{min-height:55px;padding:9px 12px}
  .mrp-av-section strong{font-size:16px}
  div[data-testid="stMetric"]{padding:12px;min-height:84px}
}
</style>
"""
_avulsa_header='    st.markdown(' + "'<div class=\"section-band\"><div class=\"section-band-kicker\">01 · REQUISIÇÕES</div><div class=\"section-band-title\">SOLICITAÇÕES AVULSAS DE MATERIAL</div></div>',unsafe_allow_html=True)"
_avulsa_ux_substituir(
    _avulsa_header,
    '    st.markdown(' + repr(_avulsa_css) + ',unsafe_allow_html=True)\n' + _avulsa_header,
    "estilos premium",
)

_avulsa_ux_substituir(
    '    perfil=str(dados.get("role") or "").upper()\n',
    """    perfil=str(dados.get("role") or "").upper()
    _hero_titulos={
        "CONSULTA":"Solicite materiais com tranquilidade",
        "OPERADOR":"Central de separação de materiais",
        "ADMIN":"Painel de acompanhamento",
    }
    _hero_subtitulos={
        "CONSULTA":"Escolha os materiais, revise seu pedido e acompanhe cada etapa até a separação.",
        "OPERADOR":"Veja as solicitações recebidas, confirme a separação ou registre uma recusa justificada.",
        "ADMIN":"Consulte a situação das solicitações e acompanhe o fluxo operacional, sem alterar as tratativas.",
    }
    st.markdown(
        '<div class="mrp-av-hero"><div><div class="mrp-av-eyebrow">SETTA · ALMOXARIFADO</div>'
        +'<h2>'+_hero_titulos.get(perfil,"Solicitações de materiais")+'</h2>'
        +'<p>'+_hero_subtitulos.get(perfil,"Acompanhamento de requisições")+'</p>'
        +'</div><div class="mrp-av-profile">PERFIL '+perfil+'</div></div>',
        unsafe_allow_html=True,
    )
    if perfil=="CONSULTA":
        st.markdown(
            '<div class="mrp-av-steps">'
            '<div class="mrp-av-step"><div class="mrp-av-index">01</div><div><strong>Escolher material</strong><small>Pesquise e informe a quantidade</small></div></div>'
            '<div class="mrp-av-step"><div class="mrp-av-index">02</div><div><strong>Revisar pedido</strong><small>Confirme os itens da lista</small></div></div>'
            '<div class="mrp-av-step"><div class="mrp-av-index">03</div><div><strong>Enviar e acompanhar</strong><small>Registre e consulte o andamento</small></div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
""",
    "hero conforme perfil",
)

_avulsa_ux_substituir(
    '        st.markdown("#### NOVA SOLICITAÇÃO")\n        st.caption("Adicione os materiais primeiro; o registro e a reserva só ocorrem no envio final.")',
    """        st.markdown(
            '<div class="mrp-av-section"><span>ETAPA 01 · ESCOLHA</span>'
            '<strong>Selecione o material</strong>'
            '<small>Pesquise por código ou descrição. O saldo disponível aparece antes da inclusão.</small></div>',
            unsafe_allow_html=True,
        )
        st.caption("Os itens só são registrados e reservados depois da confirmação final do pedido.")""",
    "primeira etapa",
)

_avulsa_ux_substituir(
    '            _existing=float(_cart.get(_code,{}).get("quantidade",0))',
    """            if item:
                st.markdown(
                    '<div class="mrp-av-item"><b>'+str(item["codigo"])+'</b>'
                    '<p>'+str(item["descricao"]).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")+'</p>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                _m1,_m2,_m3=st.columns(3)
                _m1.metric("SALDO EM ESTOQUE",f'{float(item["saldo"]):,.3f}')
                _m2.metric("SOBRA (DIV)",f'{float(item["div"]):,.3f}')
                _m3.metric("SOLICITÁVEL",f'{float(item["disponivel"]):,.3f}')
            _existing=float(_cart.get(_code,{}).get("quantidade",0))""",
    "detalhamento do material",
)

_avulsa_ux_substituir(
    '        if _cart:\n            st.markdown("#### REVISÃO DO PEDIDO")',
    """        if _cart:
            st.markdown(
                '<div class="mrp-av-section"><span>ETAPA 02 · CONFERÊNCIA</span>'
                '<strong>Revise os itens do pedido</strong>'
                '<small>Ajuste quantidades, retire itens indevidos e confira a relação antes de enviar.</small></div>',
                unsafe_allow_html=True,
            )
            st.info(f"{len(_cart)} material(is) na lista · máximo de 30 por pedido.")""",
    "revisão do carrinho",
)

_avulsa_ux_substituir(
    '                solicitante=st.text_input("SOLICITANTE",',
    """                st.markdown("**ETAPA 03 · CONFIRMAR E ENVIAR**")
                st.caption("Ao registrar, o sistema valida novamente os saldos e encaminha a solicitação ao almoxarifado.")
                solicitante=st.text_input("SOLICITANTE",""",
    "orientação do envio",
)

_avulsa_ux_substituir(
    '        st.markdown("### FILA OPERACIONAL")',
    """        st.markdown(
            '<div class="mrp-av-section"><span>TRATATIVAS DO ALMOXARIFADO</span>'
            '<strong>Fila de separação</strong>'
            '<small>Analise cada solicitação antes de confirmar. Recusas exigem motivo registrado.</small></div>',
            unsafe_allow_html=True,
        )""",
    "central operador",
)

_avulsa_ux_substituir(
    '        st.markdown("### ACOMPANHAMENTO ADMINISTRATIVO")',
    """        st.markdown(
            '<div class="mrp-av-section"><span>SUPERVISÃO</span>'
            '<strong>Acompanhamento das requisições</strong>'
            '<small>Visão geral de pedidos pendentes, separados e recusados, sem ações de separação.</small></div>',
            unsafe_allow_html=True,
        )""",
    "acompanhamento admin",
)

_avulsa_ux_substituir(
    """    st.markdown('<div class="topic-divider"></div>',unsafe_allow_html=True)
    if st.button("ATUALIZAR STATUS DAS SOLICITAÇÕES",key="mrp_avulsas_atualizar_status"):
        st.rerun()
    st.caption("O solicitante acompanha aqui a confirmação do operador. Use ATUALIZAR STATUS para consultar a situação mais recente.")""",
    """    st.markdown('<div class="mrp-av-rule"></div>',unsafe_allow_html=True)
    _titulo_acomp="Acompanhe suas solicitações" if perfil=="CONSULTA" else "Histórico e situação dos pedidos"
    st.markdown(
        '<div class="mrp-av-section"><span>ACOMPANHAMENTO</span><strong>'
        +_titulo_acomp+'</strong><small>Consulte os status e as observações de cada material.</small></div>',
        unsafe_allow_html=True,
    )
    _refresh,_hint=st.columns([1,3])
    with _refresh:
        if st.button("ATUALIZAR STATUS DAS SOLICITAÇÕES",key="mrp_avulsas_atualizar_status",use_container_width=True):
            st.rerun()
    with _hint:
        st.caption("Atualize para conferir separações e recusas registradas pelo operador.")""",
    "acompanhamento claro",
)

_avulsa_ux_substituir(
    '        return view.fillna("")\n',
    """        for _coluna in ("SOLICITADO EM","SEPARADO EM","RECUSADO EM"):
            # ISO/UTC do Supabase convertido para data e hora local da fábrica.
            _datas=pd.to_datetime(view[_coluna],utc=True,errors="coerce")
            view[_coluna]=_datas.dt.tz_convert("America/Sao_Paulo").dt.strftime("%d/%m/%Y %H:%M").fillna("")
        view["STATUS"]=view["STATUS"].replace({
            "PENDENTE":"AGUARDANDO SEPARAÇÃO",
            "ABERTA":"AGUARDANDO SEPARAÇÃO",
            "ATENDIDA":"SEPARADO",
        })
        return view.fillna("")
""",
    "datas legíveis na tabela",
)

_avulsa_ux_substituir(
    '            if pendentes:\n                _pendentes_df=tabela(pendentes)',
    """            if pendentes:
                st.info(f"{len(pendentes)} solicitação(ões) aguardando tratativa no almoxarifado.")
                _pendentes_df=tabela(pendentes)""",
    "fila em destaque",
)

_avulsa_ux_substituir(
    '                        alvo=st.selectbox("SOLICITAÇÃO PARA TRATATIVA",list(chaves.keys()))\n',
    """                        alvo=st.selectbox("SOLICITAÇÃO PARA TRATATIVA",list(chaves.keys()))
                        _id_escolhido=chaves.get(alvo)
                        _pedido_escolhido=next((p for p in pendentes if p.get("id")==_id_escolhido),None)
                        if _pedido_escolhido:
                            st.markdown(
                                "**Material:** "+str(_pedido_escolhido.get("codigo") or "")+
                                " · "+str(_pedido_escolhido.get("descricao") or "")+
                                "  \\\\n**Quantidade:** "+str(_pedido_escolhido.get("quantidade") or "")+
                                " · **Solicitante:** "+str(_pedido_escolhido.get("solicitante") or "")
                            )
                        st.caption("Confirme a separação apenas após disponibilizar o material. Para recusar, informe o motivo.")
""",
    "pedido em tratativa",
)
'''
