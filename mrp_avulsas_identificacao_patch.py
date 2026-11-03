"""Correção para identificação obrigatória nas solicitações avulsas."""
AVULSAS_IDENTIFICACAO_PATCH = r'''
def _av_ident_trocar(antes, depois, rotulo):
    global _source
    ocorrencias = _source.count(antes)
    if ocorrencias != 1:
        raise RuntimeError("Identificação S.A. " + rotulo + ": esperado 1 bloco; encontrado " + str(ocorrencias))
    _source = _source.replace(antes, depois, 1)

# Nunca mascarar dados ausentes com a impressão de que foram informados.
_av_placeholder = 'or "A PREENCHER NA ENTREGA"'
if _source.count(_av_placeholder) != 3:
    raise RuntimeError("Identificação S.A.: campos complementares não encontrados.")
_source = _source.replace(_av_placeholder, 'or "NÃO INFORMADO · REGULARIZAÇÃO PENDENTE"')

_av_antes_observacao = '                if p.get("observacao_operador"):st.caption("Operador: "+str(p["observacao_operador"]))'
_av_regra = """                # Conferir o dado persistido, nunca o texto substituto exibido.
                _faltantes=[]
                if p.get("finalidade")=="ACERTO_GERENCIAL":
                    if not identificacao_valida(p.get("cr"),1):
                        _faltantes.append("CR")
                    if not identificacao_valida(p.get("aprovador"),2):
                        _faltantes.append("APROVADOR")
                elif p.get("finalidade")=="GARANTIA":
                    if not identificacao_valida(p.get("psys"),2):
                        _faltantes.append("OP(s) DA GARANTIA")
                if _faltantes:
                    st.error("REGULARIZAÇÃO PENDENTE · "+", ".join(_faltantes)+
                             ". A identificação obrigatória não consta na solicitação.")
                    if perfil in {"ADMIN","CONSULTA"} and p.get("estado") in {"PENDENTE","SEPARADA"}:
                        with st.form("regularizar_id_sa_"+str(p["id"]),enter_to_submit=False):
                            st.markdown("**REGULARIZAR DADOS DA "+proto+"**")
                            if p.get("finalidade")=="ACERTO_GERENCIAL":
                                _reg_cr=st.text_input("CR OBRIGATÓRIO",value=str(p.get("cr") or ""),
                                    max_chars=150,key="reg_cr_"+str(p["id"]))
                                _reg_ap=st.text_input("APROVADOR OBRIGATÓRIO",value=str(p.get("aprovador") or ""),
                                    max_chars=180,key="reg_ap_"+str(p["id"]))
                                _reg_psys=""
                            else:
                                _reg_psys=st.text_area("OP(s) DA GARANTIA",value=str(p.get("psys") or ""),
                                    max_chars=1000,key="reg_psys_"+str(p["id"]))
                                _reg_cr=_reg_ap=""
                            _salvar_reg=st.form_submit_button("SALVAR REGULARIZAÇÃO",
                                type="primary",use_container_width=True)
                        if _salvar_reg:
                            if p.get("finalidade")=="ACERTO_GERENCIAL" and (
                                not identificacao_valida(_reg_cr,1) or
                                not identificacao_valida(_reg_ap,2)
                            ):
                                st.error("Informe CR e aprovador reais. Respostas provisórias não são aceitas.")
                            elif p.get("finalidade")=="GARANTIA" and not identificacao_valida(_reg_psys,2):
                                st.error("Informe a identificação válida da(s) OP(s).")
                            else:
                                try:
                                    _mrp_avulsas_call("pedido_regularizar",{
                                        "pedido_id":p["id"],
                                        "cr":_reg_cr.strip(),
                                        "aprovador":_reg_ap.strip(),
                                        "psys":_reg_psys.strip(),
                                    })
                                    st.success("Identificação registrada e vinculada ao histórico.")
                                    st.rerun()
                                except Exception as exc:
                                    st.error("Não foi possível regularizar a solicitação: "+str(exc))
"""
_av_ident_trocar(_av_antes_observacao,_av_regra+_av_antes_observacao,"pendência e formulário de regularização")

_av_ident_trocar(
    'elif finalidade=="GARANTIA" and len(psys.strip())<2:',
    'elif finalidade=="GARANTIA" and not identificacao_valida(psys,2):',
    "validar OP na criação",
)
_av_ident_trocar(
    'elif finalidade=="ACERTO GERENCIAL" and (not cr.strip() or not aprovador.strip()):',
    'elif finalidade=="ACERTO GERENCIAL" and (not identificacao_valida(cr,1) or not identificacao_valida(aprovador,2)):',
    "validar CR e aprovador na criação",
)
_av_ident_trocar(
    'st.error("Informe o CR e o aprovador.")',
    'st.error("Informe CR e aprovador reais. Campos em branco ou respostas provisórias não são aceitos.")',
    "mensagem de criação",
)
_av_ident_trocar(
    '_sep=_a.form_submit_button("CONFIRMAR MATERIAL SEPARADO",\n                            type="primary",use_container_width=True)',
    '_sep=_a.form_submit_button("CONFIRMAR MATERIAL SEPARADO",\n                            type="primary",use_container_width=True,disabled=bool(_faltantes))',
    "bloquear separação incompleta",
)
_av_ident_trocar(
    '_entregar=st.form_submit_button("CONFIRMAR ENTREGA",\n                            type="primary",use_container_width=True)',
    '_entregar=st.form_submit_button("CONFIRMAR ENTREGA",\n                            type="primary",use_container_width=True,disabled=bool(_faltantes))',
    "bloquear entrega de legado pendente",
)
_av_ident_trocar(
    'elif p.get("finalidade")=="ACERTO_GERENCIAL" and (\n                            not _cr.strip() or len(_aprovador.strip())<2\n                        ):',
    'elif p.get("finalidade")=="ACERTO_GERENCIAL" and (\n                            not identificacao_valida(_cr,1) or not identificacao_valida(_aprovador,2)\n                        ):',
    "validar entrega",
)
'''
