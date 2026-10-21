"""Separa acompanhamento, conferência final e administração sem alterar regras operacionais."""
AVULSAS_ORGANIZACAO_PATCH = r"""
_view_start=_source.index("def _mrp_avulsas_view():\n")
_view_end=_source.index('\nif _mrp_page=="SOLICITAÇÕES AVULSAS":',_view_start)
_view=_source[_view_start:_view_end]

def _admin_uma(needle,rotulo):
    if _view.count(needle)!=1:
        raise RuntimeError("Organização de Solicitações Avulsas: "+rotulo+
                           " exige ponto único; encontrado "+str(_view.count(needle)))

def _admin_indentar(bloco):
    # Mantém indentação de blocos aninhados; não altera código de negócio.
    return "".join(("    "+linha if linha.strip() else linha)
                   for linha in bloco.splitlines(keepends=True))

# Navegação funcional apenas do ADMIN: as demais permissões são preservadas.
_nav_anchor='    _counters=st.columns(4 if perfil=="CONSULTA" else 3)'
_admin_uma(_nav_anchor,"indicadores")
_nav='''    if perfil=="ADMIN":
        st.markdown("**ÁREA DE TRABALHO**")
        _mrp_av_admin_area=st.segmented_control(
            "NAVEGAÇÃO DAS SOLICITAÇÕES AVULSAS",
            options=("SOLICITAÇÕES","CONFERÊNCIA FINAL","ADMINISTRAÇÃO"),
            default="SOLICITAÇÕES",
            selection_mode="single",
            label_visibility="collapsed",
            key="mrp_avulsas_admin_area",
        )
        _descricoes_area={
            "SOLICITAÇÕES":"Consulta e acompanhamento das S.A.s: separação, entrega, garantia e histórico.",
            "CONFERÊNCIA FINAL":"Validação administrativa de entregas, documentos Protheus e encerramento.",
            "ADMINISTRAÇÃO":"Diagnóstico de custos, configuração de e-mails e testes de integração com Teams.",
        }
        st.caption(_descricoes_area[_mrp_av_admin_area])
    else:
        _mrp_av_admin_area="SOLICITAÇÕES"
'''
_view=_view.replace(_nav_anchor,_nav+_nav_anchor,1)

# Indicadores e informações operacionais só aparecem na área de Solicitações.
_start=_view.index(_nav_anchor)
_end=_view.index("    def _etapa(numero,titulo,descricao):",_start)
_indicadores=_view[_start:_end]
_view=(_view[:_start]+
       '    if _mrp_av_admin_area=="SOLICITAÇÕES":\n'+
       _admin_indentar(_indicadores)+
       _view[_end:])

# As abas de situação e a exportação são exclusivas da área de Solicitações.
_render_start='    if perfil=="OPERADOR":\n        _retorno_operador=st.session_state.pop('
_render_end='    if perfil=="ADMIN":\n        st.markdown("---")\n        st.markdown("### CONFERÊNCIA FINAL · ADMIN")'
_admin_uma(_render_start,"fila e histórico operacional")
_admin_uma(_render_end,"conferência final")
_i=_view.index(_render_start)
_j=_view.index(_render_end,_i)
_operacional=_view[_i:_j]
_view=(_view[:_i]+
       '    if _mrp_av_admin_area=="SOLICITAÇÕES":\n'+
       _admin_indentar(_operacional)+
       _view[_j:])

# O checklist deixa de aparecer abaixo da tabela de consultas.
_view=_view.replace(
    _render_end,
    '    if perfil=="ADMIN" and _mrp_av_admin_area=="CONFERÊNCIA FINAL":\n'
    '        st.markdown("### CONFERÊNCIA FINAL · ADMIN")',
    1,
)

# Integrações deixam de ficar misturadas com as duas filas.
_admin_tools='    if perfil=="ADMIN":\n        with st.expander("ADMINISTRAÇÃO · DIAGNÓSTICO DE CUSTOS",expanded=False):'
_admin_uma(_admin_tools,"ferramentas administrativas")
_view=_view.replace(_admin_tools,
    '    if perfil=="ADMIN" and _mrp_av_admin_area=="ADMINISTRAÇÃO":\n'
    '        st.markdown("### ADMINISTRAÇÃO · INTEGRAÇÕES E DIAGNÓSTICO")\n'
    '        st.caption("Ferramentas técnicas e testes, separados das solicitações e da conferência final.")\n'
    '        with st.expander("ADMINISTRAÇÃO · DIAGNÓSTICO DE CUSTOS",expanded=False):',
    1,
)

_source=_source[:_view_start]+_view+_source[_view_end:]

# Exceções de renderização aparecem como aviso recuperável, nunca tela branca.
_ui_call='if _mrp_page=="SOLICITAÇÕES AVULSAS":\n    _mrp_avulsas_view()\n    st.stop()'
if _source.count(_ui_call)!=1:
    raise RuntimeError("Proteção de exibição MRP: chamada da página não encontrada.")
_ui_guard='''if _mrp_page=="SOLICITAÇÕES AVULSAS":
    try:
        _mrp_avulsas_view()
    except Exception:
        import logging as _mrp_log
        _mrp_log.exception("MRP: erro ao renderizar solicitações avulsas")
        st.error("Falha ao atualizar a tela de solicitações. Os registros já confirmados continuam salvos.")
        st.info("Recarregue a consulta abaixo. Se continuar, informe o momento e a operação realizada.")
        if st.button("RECARREGAR SOLICITAÇÕES",key="mrp_avulsas_retry_view"):
            st.session_state.pop("_mrp_avulsas_lista_cache",None)
            st.rerun()
    st.stop()'''
_source=_source.replace(_ui_call,_ui_guard,1)
"""