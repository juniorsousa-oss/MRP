ENTREGA_PATCH = r"""
# =========================================================
# RESUMO — STATUS DE SEPARAÇÃO POR OP
# Regra: considerar somente se houve separação.
# Se em qualquer linha da OP a Pendência (H) for menor que a
# Quantidade necessária/demanda (F), a OP recebe POSSUI SEPARAÇÃO.
# Caso contrário: NÃO POSSUI SEPARAÇÃO.
# =========================================================
_rg_pend_anchor = '        "Pendência":num(gr.iloc[:,7]).fillna(0),\n'
_rg_pend_new = (
    '        "Pendência":num(gr.iloc[:,7]).fillna(0),\n'
    '        "Quantidade Solicitada":num(gr.iloc[:,5]).fillna(0),\n'
)
if _rg_pend_anchor not in _source:
    raise RuntimeError("Leitura da Pendência do RelatorioGeral_Tratado não encontrada para status de separação.")
_source = _source.replace(_rg_pend_anchor, _rg_pend_new, 1)

_separacao_map_anchor = '''ultima_solicitacao=rg.groupby(["Projeto","Código"],as_index=False)["Data Solicitação"].max().rename(columns={"Código":"Produto","Data Solicitação":"Última Solicitação"})
ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)

demanda_projeto_base='''
_separacao_map_new = '''ultima_solicitacao=rg.groupby(["Projeto","Código"],as_index=False)["Data Solicitação"].max().rename(columns={"Código":"Produto","Data Solicitação":"Última Solicitação"})
ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)

# Uma OP é marcada como POSSUI SEPARAÇÃO quando pelo menos uma linha dela
# apresenta Pendência menor que a Quantidade Solicitada/demanda.
_rg_separacao=rg.copy()
_rg_separacao["_QtdSolicitada"]=pd.to_numeric(_rg_separacao["Quantidade Solicitada"],errors="coerce").fillna(0.0)
_rg_separacao["_PendenciaSeparacao"]=pd.to_numeric(_rg_separacao["Pendência"],errors="coerce").fillna(0.0)
_rg_separacao["_LinhaPossuiSeparacao"]=(
    _rg_separacao["_QtdSolicitada"].gt(0)
    & _rg_separacao["_PendenciaSeparacao"].lt(_rg_separacao["_QtdSolicitada"])
)
separacao_map=(
    _rg_separacao.groupby("Projeto")["_LinhaPossuiSeparacao"]
    .any()
    .map({True:"POSSUI SEPARAÇÃO",False:"NÃO POSSUI SEPARAÇÃO"})
    .to_dict()
)

demanda_projeto_base='''
if _separacao_map_anchor not in _source:
    raise RuntimeError("Ponto de criação da Demanda por Projeto não encontrado para status de separação.")
_source = _source.replace(_separacao_map_anchor, _separacao_map_new, 1)

_separacao_base_anchor = 'demanda_projeto_base["Pendência Original"]=pd.to_numeric(demanda_projeto_base["Necessidade"],errors="coerce").fillna(0.0)\n'
_separacao_base_new = (
    'demanda_projeto_base["Pendência Original"]=pd.to_numeric(demanda_projeto_base["Necessidade"],errors="coerce").fillna(0.0)\n'
    'demanda_projeto_base["Status Separação"]=demanda_projeto_base["Projeto"].map(separacao_map).fillna("NÃO POSSUI SEPARAÇÃO")\n'
)
if _separacao_base_anchor not in _source:
    raise RuntimeError("Base da Demanda por Projeto não encontrada para vincular status de separação.")
_source = _source.replace(_separacao_base_anchor, _separacao_base_new, 1)

_resumo_anchor = '''    partes.append(_condicao_resumo(row.get("Condição","")))
    obs=str(row.get("OBS Tratativa","") or "").strip()'''
_resumo_new = '''    partes.append(_condicao_resumo(row.get("Condição","")))
    partes.append(str(row.get("Status Separação","NÃO POSSUI SEPARAÇÃO") or "NÃO POSSUI SEPARAÇÃO").strip().upper())
    obs=str(row.get("OBS Tratativa","") or "").strip()'''
if _resumo_anchor not in _source:
    raise RuntimeError("Montagem da coluna Resumo não encontrada para status de separação.")
_source = _source.replace(_resumo_anchor, _resumo_new, 1)

# Força um novo snapshot para que a informação seja gravada mesmo usando
# as mesmas cinco bases da versão anterior.
_source = _source.replace(
    'MRP-SNAPSHOT-V4-FABRICACAO',
    'MRP-SNAPSHOT-V6-STATUS-SEPARACAO',
    1,
)
"""
