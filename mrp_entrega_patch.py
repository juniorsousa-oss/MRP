ENTREGA_PATCH = r'''
# =========================================================
# RESUMO — STATUS DE ENTREGA POR OP
# Regra: na MESMA linha do RelatorioGeral_Tratado,
# H Pendência < F Qtd. necessária E K Resp. conferência preenchido.
# Se qualquer linha da OP atender aos dois critérios: POSSUI ENTREGA.
# Caso contrário: NÃO POSSUI ENTREGA.
# =========================================================
_rg_pend_anchor = '        "Pendência":num(gr.iloc[:,7]).fillna(0),\n'
_rg_pend_new = (
    '        "Pendência":num(gr.iloc[:,7]).fillna(0),\n'
    '        "Quantidade Solicitada":num(gr.iloc[:,5]).fillna(0),\n'
    '        "Resp. Conferência":gr.iloc[:,10].fillna("").astype(str).str.strip(),\n'
)
if _rg_pend_anchor not in _source:
    raise RuntimeError("Leitura da Pendência do RelatorioGeral_Tratado não encontrada para status de entrega.")
_source = _source.replace(_rg_pend_anchor, _rg_pend_new, 1)

_entrega_map_anchor = '''ultima_solicitacao=rg.groupby(["Projeto","Código"],as_index=False)["Data Solicitação"].max().rename(columns={"Código":"Produto","Data Solicitação":"Última Solicitação"})
ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)

demanda_projeto_base='''
_entrega_map_new = '''ultima_solicitacao=rg.groupby(["Projeto","Código"],as_index=False)["Data Solicitação"].max().rename(columns={"Código":"Produto","Data Solicitação":"Última Solicitação"})
ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)

# Uma OP é marcada como POSSUI ENTREGA quando pelo menos uma linha dela
# demonstra atendimento parcial/total (Pendência < Quantidade Solicitada)
# e essa mesma linha possui responsável de conferência preenchido.
_rg_entrega=rg.copy()
_rg_entrega["_QtdSolicitada"]=pd.to_numeric(_rg_entrega["Quantidade Solicitada"],errors="coerce").fillna(0.0)
_rg_entrega["_PendenciaEntrega"]=pd.to_numeric(_rg_entrega["Pendência"],errors="coerce").fillna(0.0)
_rg_entrega["_RespConfEntrega"]=_rg_entrega["Resp. Conferência"].fillna("").astype(str).str.strip()
_rg_entrega["_LinhaPossuiEntrega"]=(
    _rg_entrega["_QtdSolicitada"].gt(0)
    & _rg_entrega["_PendenciaEntrega"].lt(_rg_entrega["_QtdSolicitada"])
    & _rg_entrega["_RespConfEntrega"].ne("")
)
entrega_map=(
    _rg_entrega.groupby("Projeto")["_LinhaPossuiEntrega"]
    .any()
    .map({True:"POSSUI ENTREGA",False:"NÃO POSSUI ENTREGA"})
    .to_dict()
)

demanda_projeto_base='''
if _entrega_map_anchor not in _source:
    raise RuntimeError("Ponto de criação da Demanda por Projeto não encontrado para status de entrega.")
_source = _source.replace(_entrega_map_anchor, _entrega_map_new, 1)

_entrega_base_anchor = 'demanda_projeto_base["Pendência Original"]=pd.to_numeric(demanda_projeto_base["Necessidade"],errors="coerce").fillna(0.0)\n'
_entrega_base_new = (
    'demanda_projeto_base["Pendência Original"]=pd.to_numeric(demanda_projeto_base["Necessidade"],errors="coerce").fillna(0.0)\n'
    'demanda_projeto_base["Status Entrega"]=demanda_projeto_base["Projeto"].map(entrega_map).fillna("NÃO POSSUI ENTREGA")\n'
)
if _entrega_base_anchor not in _source:
    raise RuntimeError("Base da Demanda por Projeto não encontrada para vincular status de entrega.")
_source = _source.replace(_entrega_base_anchor, _entrega_base_new, 1)

_resumo_anchor = '''    partes.append(_condicao_resumo(row.get("Condição","")))
    obs=str(row.get("OBS Tratativa","") or "").strip()'''
_resumo_new = '''    partes.append(_condicao_resumo(row.get("Condição","")))
    partes.append(str(row.get("Status Entrega","NÃO POSSUI ENTREGA") or "NÃO POSSUI ENTREGA").strip().upper())
    obs=str(row.get("OBS Tratativa","") or "").strip()'''
if _resumo_anchor not in _source:
    raise RuntimeError("Montagem da coluna Resumo não encontrada para status de entrega.")
_source = _source.replace(_resumo_anchor, _resumo_new, 1)

# Força um novo snapshot para que a informação seja gravada mesmo usando
# as mesmas cinco bases da versão anterior.
_source = _source.replace(
    'MRP-SNAPSHOT-V4-FABRICACAO',
    'MRP-SNAPSHOT-V5-STATUS-ENTREGA',
    1,
)
'''
