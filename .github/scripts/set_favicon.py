from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')

# Corrige a data de última solicitação na DEMANDA DE PROJETOS:
# o vínculo deve ser por Projeto + Produto, e não somente por Projeto.
old = 'ultima_solicitacao=rg.groupby("Projeto",as_index=False)["Data Solicitação"].max().rename(columns={"Data Solicitação":"Última Solicitação"}); ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)'
new = 'ultima_solicitacao=rg.groupby(["Projeto","Código"],as_index=False)["Data Solicitação"].max().rename(columns={"Código":"Produto","Data Solicitação":"Última Solicitação"}); ultima_solicitacao["Última Solicitação"]=ultima_solicitacao["Última Solicitação"].apply(formatar_data_br)'
if old not in s:
    raise SystemExit('Trecho da Última Solicitação não encontrado.')
s = s.replace(old, new, 1)

# O mesmo critério é aplicado à Data CM para manter a linha do projeto/material coerente.
old2 = 'data_cm_projeto=rg.groupby("Projeto",as_index=False)["Data CM"].max().rename(columns={"Data CM":"Data CM"}); data_cm_projeto["Data CM"]=data_cm_projeto["Data CM"].apply(lambda x:formatar_data_br(x) if pd.notna(pd.to_datetime(x,errors="coerce")) else "NI")'
new2 = 'data_cm_projeto=rg.groupby(["Projeto","Código"],as_index=False)["Data CM"].max().rename(columns={"Código":"Produto","Data CM":"Data CM"}); data_cm_projeto["Data CM"]=data_cm_projeto["Data CM"].apply(lambda x:formatar_data_br(x) if pd.notna(pd.to_datetime(x,errors="coerce")) else "NI")'
if old2 not in s:
    raise SystemExit('Trecho da Data CM não encontrado.')
s = s.replace(old2, new2, 1)

p.write_text(s, encoding='utf-8')
print('Data de solicitação corrigida para Projeto + Produto.')
