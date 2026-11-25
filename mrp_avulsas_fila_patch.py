AVULSAS_FILA_PATCH = r'''
def _av_fila_sub(a,b):
    global _source
    if _source.count(a)!=1:
        raise RuntimeError("Layout de solicitações: âncora incompatível: "+a[:100])
    _source=_source.replace(a,b,1)

_av_fila_sub("""def _mrp_avulsas_view():
    import re as _av_re""","""def _mrp_avulsas_view():
    from contextlib import nullcontext as _av_nullcontext
    from mrp_avulsas_fila import PAGE_CSS as _av_fila_css, preparar_fila as _av_fila, fila_view as _av_fila_view
    st.html(_av_fila_css)
    import re as _av_re""")
_av_hero_ini=_source.index('    _titulos={\n        "CONSULTA":"Solicitações de materiais",')
_av_hero_fim=_source.index('    _pendentes=[p for p in pedidos',_av_hero_ini)
_source=_source[:_av_hero_ini]+'    st.caption("Almoxarifado · Perfil "+perfil)\n'+_source[_av_hero_fim:]
_av_fila_sub("""    if _mrp_av_admin_area=="SOLICITAÇÕES":
        _counters=st.columns(4 if perfil=="CONSULTA" else 3)
""","""    _mrp_av_consulta_area="MINHAS SOLICITAÇÕES"
    if perfil=="CONSULTA":
        _mrp_av_consulta_area=st.segmented_control(
            "Área das solicitações",
            ("MINHAS SOLICITAÇÕES","NOVA SOLICITAÇÃO","EXCEÇÕES"),
            default="MINHAS SOLICITAÇÕES",key="mrp_sa_area_consulta",
        ) or "MINHAS SOLICITAÇÕES"
    if _mrp_av_admin_area=="SOLICITAÇÕES" and _mrp_av_consulta_area=="NOVA SOLICITAÇÃO":
        _counters=st.columns(4 if perfil=="CONSULTA" else 3)
""")
_av_fila_sub("        st.caption(_descricoes_area[_mrp_av_admin_area])",
             '        _mrp_av_admin_area = _mrp_av_admin_area or "SOLICITAÇÕES"\n        st.caption(_descricoes_area[_mrp_av_admin_area])')
_av_fila_sub('    def _mostrar_pedidos(lista,vazio,filtrar_itens=None,grupo="geral"):',
             '    def _mostrar_pedidos(lista,vazio,filtrar_itens=None,grupo="geral",detalhe=False):')
_av_fila_sub("""            with st.expander(titulo,expanded=False):
                if p.get("excecao_id"):""","""            with (_av_nullcontext() if detalhe else st.expander(titulo,expanded=False)):
                if detalhe:
                    st.subheader(proto)
                    st.caption(titulo)
                if p.get("excecao_id"):""")
_av_fila_sub("""    if perfil=="CONSULTA":
        _snapshot=str(dados.get("snapshot_id") or "")""","""    if perfil=="CONSULTA" and _mrp_av_consulta_area=="NOVA SOLICITAÇÃO":
        _snapshot=str(dados.get("snapshot_id") or "")""")
_av_fila_sub("""    if perfil=="CONSULTA":
        with st.expander("SOLICITAÇÃO EXCEPCIONAL""","""    if perfil=="CONSULTA" and _mrp_av_consulta_area=="EXCEÇÕES":
        with st.expander("SOLICITAÇÃO EXCEPCIONAL""")
# Preservar a sequência do bloco ADMIN de autorizações sem alterar as suas ações.
_av_fila_sub("""    st.divider()
    titulo="Minhas solicitações" if perfil=="CONSULTA" else "Fila operacional" if perfil=="OPERADOR" else "Acompanhamento geral"
    _c1,_c2=st.columns([5,1],vertical_alignment="center")
    _c1.markdown("### "+titulo)
    if _c2.button("ATUALIZAR STATUS",key="mrp_avulsas_atualizar_status",use_container_width=True):
        st.session_state.pop("_mrp_avulsas_lista_cache",None)
        st.rerun()
""",'')
_av_fila_ini=_source.index('    if _mrp_av_admin_area=="SOLICITAÇÕES":\n        if perfil=="OPERADOR":\n            _retorno_operador')
_av_fila_fim=_source.index('    if perfil=="ADMIN" and _mrp_av_admin_area=="CONFERÊNCIA FINAL":',_av_fila_ini)
_av_leg_ini=_source.index('                _ids_legado=',_av_fila_ini)
_av_leg_fim=_source.index('            with tab_separadas:',_av_leg_ini)
_av_legado=_source[_av_leg_ini:_av_leg_fim]
_av_fila_main="""    if _mrp_av_admin_area=="SOLICITAÇÕES" and _mrp_av_consulta_area=="MINHAS SOLICITAÇÕES":
        _titulo_fila="Minhas solicitações" if perfil=="CONSULTA" else "Fila operacional" if perfil=="OPERADOR" else "Acompanhamento geral"
        _c1,_c2=st.columns([4,1],vertical_alignment="center")
        _c1.subheader(_titulo_fila)
        if _c2.button("ATUALIZAR STATUS",key="mrp_avulsas_atualizar_status",use_container_width=True):
            st.session_state.pop("_mrp_avulsas_lista_cache",None)
            st.rerun()
        if perfil=="OPERADOR":
            _retorno_operador=st.session_state.pop("_mrp_avulsas_operador_retorno",None)
            if _retorno_operador:
                _aviso_email=("não configurado" in _retorno_operador.lower()
                             or "pendente" in _retorno_operador.lower())
                st.toast(_retorno_operador,icon="⚠️" if _aviso_email else "✅")
        _legados_fila={
            str(p["id"]):estado for estado, grupo in (
                ("PENDENTE",_legados_pendentes),("SEPARADA",_legados_separados),("RECUSADA",_legados_recusados)
            ) for p in grupo
        }
        _dataset=_av_fila(pedidos,itens,_protocolo,_hora,_labels,_legados_fila)
        _id_fila=_av_fila_view(_dataset,"mrp_sa_fila_"+perfil,
            ("PENDENTE","SEPARADA","ENTREGUE","RECUSADA","LEGADO"),
            padrao="PENDENTE" if perfil=="OPERADOR" else "TODAS")
        if _id_fila:
            with st.container(key="mrp_sa_detalhe"):
                _mostrar_pedidos([p for p in pedidos if str(p["id"])==_id_fila],
                    "Solicitação não encontrada.",grupo="fila",detalhe=True)
        else:
            if _entregues and st.toggle("Abrir histórico de garantias e demais entregas",
                    key="mrp_sa_garantias_"+perfil):
                _exibir_entregas()
            if perfil=="OPERADOR":
"""+_av_legado+"""            _exportar=_tabela_geral_solicitacoes(pedidos)
            if not _exportar.empty:
                if perfil!="OPERADOR":
                    _sa_sem_protocolo=_exportar[_exportar["S.A."].str.startswith("REGISTRO #",na=False)]
                    if not _sa_sem_protocolo.empty:
                        with st.expander("Registros anteriores sem protocolo",expanded=False):
                            st.dataframe(_sa_sem_protocolo,use_container_width=True,hide_index=True)
                st.download_button("EXPORTAR SOLICITAÇÕES · EXCEL",
                    lambda: excel_bytes({"Materiais_por_SA":_exportar}),
                    "mrp_solicitacoes_avulsas.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
"""
_source=_source[:_av_fila_ini]+_av_fila_main+_source[_av_fila_fim:]
_av_fila_sub("""            for _p in _entregues_pendentes:
                _proto = _protocolo(_p)""","""            _id_conferencia=_av_fila_view(
                _av_fila(_entregues_pendentes,itens,_protocolo,_hora,_labels,conferencia="FINAL_PENDENTE"),
                "mrp_sa_conferencia")
            for _p in (_p for _p in _entregues_pendentes if str(_p["id"])==_id_conferencia):
                _proto = _protocolo(_p)""")
_av_fila_sub("""                    + " · Entregue em " + (_hora(_p.get("entregue_em")) or "—"),
                    expanded=False,""","""                    + " · Entregue em " + (_hora(_p.get("entregue_em")) or "—"),
                    expanded=True,""")

_av_fila_sub("""            _historico_final = []
            for _p in _entregues_concluidas:""","""            _id_concluida = _av_fila_view(
                _av_fila(_entregues_concluidas,itens,_protocolo,_hora,_labels,conferencia="FINAL_CONCLUIDA"),
                "mrp_sa_concluidas")
            _historico_final = []
            _historico_selecionado = []
            for _p in _entregues_concluidas:""")
_av_fila_sub("""                _historico_final.append(_linha_historico)
            if _historico_final:
                st.dataframe(pd.DataFrame(_historico_final),use_container_width=True,hide_index=True)""","""                _historico_final.append(_linha_historico)
                if str(_p["id"]) == _id_concluida:
                    _historico_selecionado.append(_linha_historico)
            if _historico_final:
                if _historico_selecionado:
                    for _chave,_valor in _historico_selecionado[0].items():
                        st.caption(_chave)
                        st.text(str(_valor or "—"))""")
'''
