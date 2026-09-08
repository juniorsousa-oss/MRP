import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title='MRP | SETTA', page_icon='📦', layout='wide')
st.title('MRP — Planejamento de Necessidades de Materiais')
st.caption('Aplicativo alimentado pelo Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. A projeção é calculada semana a semana.')

with st.sidebar:
    st.header('Bases do MRP')
    cadastro_file = st.file_uploader('1. CADASTROS', type=['xlsx','xlsm','xltx'])
    estoque_file = st.file_uploader('2. Estoque_Tratado', type=['xlsx','xlsm'])
    geral_file = st.file_uploader('3. RelatorioGeral_Tratado', type=['xlsx','xlsm'])
    compras_file = st.file_uploader('4. Compras_Tratado', type=['xlsx','xlsm'])
    mt_file = st.file_uploader('5. MRP_TC_TP_Tratado', type=['xlsx','xlsm'])
    st.divider()
    semana_atual = st.number_input('Semana atual', 1, 53, 36, 1)

if not all([cadastro_file, estoque_file, geral_file, compras_file, mt_file]):
    st.info('Envie as 5 planilhas tratadas + o Cadastro para iniciar o MRP.')
    st.stop()

def num(s):
    return pd.to_numeric(s, errors='coerce')

def col_by_pos(df, pos, name):
    if df.shape[1] <= pos:
        raise ValueError(f'A planilha MRP_TC_TP não possui a coluna esperada {name} (posição {pos+1}).')
    df[name] = num(df.iloc[:, pos])

@st.cache_data(show_spinner=False)
def load_sources(cb, eb, gb, pb, mb):
    # CADASTRO: linha 1 vazia; cabeçalho na linha 2. B/C/D = Código/Descrição/Tipo.
    raw = pd.read_excel(BytesIO(cb), sheet_name='Listagem do Browse', header=None)
    cad = raw.iloc[2:, [1, 2, 3]].copy()
    cad.columns = ['Código', 'Descrição', 'Tipo']
    cad['Código'] = num(cad['Código'])
    cad = cad.dropna(subset=['Código']).copy()
    cad['Código'] = cad['Código'].astype(int)
    cad['Descrição'] = cad['Descrição'].fillna('').astype(str).str.strip()
    cad['Tipo'] = cad['Tipo'].fillna('').astype(str).str.strip()
    cad = cad.drop_duplicates('Código', keep='first')

    # ESTOQUE: A = Código Material; E = Saldo Disponível.
    est = pd.read_excel(BytesIO(eb), sheet_name='EstoqueTratado')
    est['COD_MATERIAL'] = num(est['COD_MATERIAL'])
    est['SALDO_DISPONIVEL'] = num(est['SALDO_DISPONIVEL']).fillna(0)
    est = est.dropna(subset=['COD_MATERIAL']).copy()
    est['COD_MATERIAL'] = est['COD_MATERIAL'].astype(int)

    # RELATÓRIO GERAL: C = Código; G = Pendência; N = Semana de Necessidade.
    rg = pd.read_excel(BytesIO(gb), sheet_name='RelatorioTratado')
    rg['Código'] = num(rg['Código'])
    rg['Semana'] = num(rg['SEMANA DE NECESSIDADE'])
    rg['Pendência'] = num(rg['Pendência']).fillna(0)
    rg['Projeto'] = rg['Projeto'].fillna('').astype(str)
    rg = rg.dropna(subset=['Código']).copy()
    rg['Código'] = rg['Código'].astype(int)
    rg['Semana válida'] = rg['Semana'].notna() & rg['Semana'].between(1, 53)
    rg_mrp = rg[rg['Semana válida']].copy()
    rg_mrp['Semana'] = rg_mrp['Semana'].astype(int)

    # COMPRAS: A = Código; D/F = S.C.; J/L = P.C.
    cp = pd.read_excel(BytesIO(pb), sheet_name='ComprasTratado')
    cp['CÓD'] = num(cp['CÓD'])
    for c in ['QUANTIDADE S.C', 'SEMANA DE ATENDIMENTO S.C', 'QUANTIDADE P.C', 'SEMANA DE ATENDIMENTO P.C']:
        cp[c] = num(cp[c]).fillna(0)
    cp = cp.dropna(subset=['CÓD']).copy()
    cp['CÓD'] = cp['CÓD'].astype(int)

    # MRP TC/TP: usar POSIÇÕES da planilha, conforme especificação do usuário.
    # B = Código Produto, E = Semana Entrega, H = Material, J = Quantidade, L = Semana Necessidade.
    mt = pd.read_excel(BytesIO(mb), sheet_name='MRP_TC_TP')
    col_by_pos(mt, 1, 'CÓDIGO PRODUTO')
    col_by_pos(mt, 4, 'SEMANA DE ENTREGA')
    col_by_pos(mt, 7, 'MATERIAL')
    col_by_pos(mt, 9, 'QUANTIDADE')
    col_by_pos(mt, 11, 'SEMANA DE NECESSIDADE')
    mt['CÓDIGO PRODUTO'] = mt['CÓDIGO PRODUTO'].fillna(0).astype(int)
    mt['MATERIAL'] = mt['MATERIAL'].fillna(0).astype(int)
    mt['SEMANA DE ENTREGA'] = mt['SEMANA DE ENTREGA'].fillna(0).astype(int)
    mt['SEMANA DE NECESSIDADE'] = mt['SEMANA DE NECESSIDADE'].fillna(0).astype(int)
    mt['QUANTIDADE'] = mt['QUANTIDADE'].fillna(0)
    return cad, est, rg, rg_mrp, cp, mt

try:
    cad, est, rg, rg_mrp, cp, mt = load_sources(cadastro_file.getvalue(), estoque_file.getvalue(), geral_file.getvalue(), compras_file.getvalue(), mt_file.getvalue())
except Exception as e:
    st.error(f'Erro ao carregar as bases: {e}')
    st.stop()

# ===================== MOTOR =====================
# S.A.: G somente quando N é numérico.
sa_week = rg_mrp.groupby(['Código', 'Semana'])['Pendência'].sum()

# TC/TP: H = material, J = quantidade, L = semana de necessidade.
tc_rows = mt[(mt['MATERIAL'] > 0) & (mt['SEMANA DE NECESSIDADE'].between(1, 53))]
tc_week = tc_rows.groupby(['MATERIAL', 'SEMANA DE NECESSIDADE'])['QUANTIDADE'].sum()
tc_week.index.names = ['Código', 'Semana']

# P.C.: J por L.
pc_week = cp[(cp['QUANTIDADE P.C'] > 0) & (cp['SEMANA DE ATENDIMENTO P.C'].between(1, 53))].groupby(['CÓD', 'SEMANA DE ATENDIMENTO P.C'])['QUANTIDADE P.C'].sum()
pc_week.index.names = ['Código', 'Semana']
pc_total = cp[cp['QUANTIDADE P.C'] > 0].groupby('CÓD')['QUANTIDADE P.C'].sum()

# S.C.: D entra no total; somente F numérica entra na cobertura da projeção.
sc_all = cp[cp['QUANTIDADE S.C'] > 0].groupby('CÓD')['QUANTIDADE S.C'].sum()
sc_week = cp[(cp['QUANTIDADE S.C'] > 0) & (cp['SEMANA DE ATENDIMENTO S.C'].between(1, 53))].groupby(['CÓD', 'SEMANA DE ATENDIMENTO S.C'])['QUANTIDADE S.C'].sum()
sc_week.index.names = ['Código', 'Semana']

# Fabricação: B + E. Cada OP corresponde a uma peça.
op = mt[(mt['CÓDIGO PRODUTO'] > 0) & (mt['SEMANA DE ENTREGA'].between(1, 53))][['ORDEM DE PRODUÇÃO', 'CÓDIGO PRODUTO', 'SEMANA DE ENTREGA']].drop_duplicates()
fab_week = op.groupby(['CÓDIGO PRODUTO', 'SEMANA DE ENTREGA']).size().astype(float)
fab_week.index.names = ['Código', 'Semana']

keys = set(sa_week.index) | set(tc_week.index) | set(pc_week.index) | set(sc_week.index) | set(fab_week.index)
weeks = sorted({int(w) for _, w in keys if 1 <= int(w) <= 53})
if semana_atual not in weeks:
    weeks = sorted(set(weeks) | {int(semana_atual)})

stock = est.groupby('COD_MATERIAL')['SALDO_DISPONIVEL'].sum()
desc = cad.set_index('Código')['Descrição'].to_dict()
tipo = cad.set_index('Código')['Tipo'].to_dict()

macro_rows = []
week_rows = []
for code in cad['Código']:
    estoque = float(stock.get(code, 0))
    saldo = estoque
    first_short = None
    total_new_sc = 0.0
    total_d = total_pc = total_sc_dated = total_fab = 0.0
    for wk in weeks:
        dsa = float(sa_week.get((code, wk), 0))
        dtc = float(tc_week.get((code, wk), 0))
        demand = dsa + dtc
        pc = float(pc_week.get((code, wk), 0))
        sc = float(sc_week.get((code, wk), 0))
        fab = float(fab_week.get((code, wk), 0))
        saldo_antes = saldo + pc + sc + fab - demand
        new_sc = max(0.0, -saldo_antes)
        saldo_final = saldo_antes + new_sc
        if new_sc > 0 and first_short is None:
            first_short = wk
        total_new_sc += new_sc
        total_d += demand
        total_pc += pc
        total_sc_dated += sc
        total_fab += fab
        week_rows.append([code, desc.get(code, ''), tipo.get(code, ''), wk, saldo, dsa, dtc, demand, pc, sc, fab, saldo_antes, new_sc, saldo_final, 'CRIAR S.C' if new_sc > 0 else 'OK'])
        saldo = saldo_final
    macro_rows.append([code, desc.get(code, ''), tipo.get(code, ''), estoque, total_d, total_pc, total_sc_dated, float(sc_all.get(code, 0)), total_fab, estoque + total_pc + total_sc_dated + total_fab - total_d, total_new_sc, first_short or '', 'CRIAR S.C' if total_new_sc > 0 else 'OK'])

macro = pd.DataFrame(macro_rows, columns=['Código', 'Descrição', 'Tipo', 'Saldo em Estoque', 'Demanda Total', 'Pedido de Compra', 'S.C. com Semana', 'S.C. Aberta Total', 'Fabricação', 'Saldo Macro sem Nova S.C', 'Criar S.C', 'Primeira Falta', 'Status'])
weekly = pd.DataFrame(week_rows, columns=['Código', 'Descrição', 'Tipo', 'Semana', 'Saldo Inicial', 'Demanda S.A.', 'Demanda TC/TP', 'Demanda Total', 'P.C.', 'S.C.', 'Fabricação', 'Saldo antes da Nova S.C', 'Criar S.C', 'Saldo Final', 'Status'])

active = macro[(macro['Saldo em Estoque'] != 0) | (macro['Demanda Total'] != 0) | (macro['Pedido de Compra'] != 0) | (macro['S.C. Aberta Total'] != 0) | (macro['Fabricação'] != 0)].copy()

m = st.columns(5)
m[0].metric('Materiais no cadastro', f'{len(cad):,}')
m[1].metric('Demanda total', f'{macro["Demanda Total"].sum():,.0f}')
m[2].metric('P.C.', f'{macro["Pedido de Compra"].sum():,.0f}')
m[3].metric('S.C. aberta', f'{macro["S.C. Aberta Total"].sum():,.0f}')
m[4].metric('Criar S.C.', f'{macro["Criar S.C"].sum():,.0f}')

tab1, tab2 = st.tabs(['DEMANDA GERAL', 'DEMANDA POR PROJETO'])

with tab1:
    st.subheader('Demanda Geral')
    c1, c2, c3 = st.columns(3)
    with c1:
        busca = st.text_input('Código / descrição')
    with c2:
        status = st.multiselect('Status', ['OK', 'CRIAR S.C'], default=['OK', 'CRIAR S.C'])
    with c3:
        tipos = st.multiselect('Tipo', [x for x in sorted(cad['Tipo'].unique()) if x])
    v = active.copy()
    if busca:
        v = v[v['Código'].astype(str).str.contains(busca, case=False, na=False) | v['Descrição'].str.contains(busca, case=False, na=False)]
    if status:
        v = v[v['Status'].isin(status)]
    if tipos:
        v = v[v['Tipo'].isin(tipos)]
    st.dataframe(v.sort_values(['Status', 'Primeira Falta', 'Código']), use_container_width=True, height=520, hide_index=True)

    if len(v):
        st.divider()
        st.subheader('Projeção do material')
        code = st.selectbox('Material', v['Código'].tolist(), format_func=lambda x: f'{x} — {desc.get(x, "")}')
        w = weekly[weekly['Código'] == code].copy()
        w = w[(w['Semana'] >= semana_atual) | ((w['Demanda Total'] != 0) | (w['P.C.'] != 0) | (w['S.C.'] != 0) | (w['Fabricação'] != 0))]
        st.dataframe(w, use_container_width=True, hide_index=True)

        d = rg_mrp[rg_mrp['Código'] == code][['Código', 'Projeto', 'Pendência', 'Semana']].sort_values(['Semana', 'Projeto'])
        if len(d):
            st.markdown('**Demandas S.A. que compõem o material**')
            st.dataframe(d, use_container_width=True, hide_index=True)

        p = cp[cp['CÓD'] == code][['CÓD', 'DESCRIÇÃO', 'QUANTIDADE P.C', 'DATA DA P.C', 'SEMANA DE ATENDIMENTO P.C']]
        if len(p):
            st.markdown('**Pedidos de compra que compõem o P.C.**')
            st.dataframe(p.sort_values(['SEMANA DE ATENDIMENTO P.C']), use_container_width=True, hide_index=True)

        s = cp[cp['CÓD'] == code][['CÓD', 'DESCRIÇÃO', 'QUANTIDADE S.C', 'DATA DA S.C', 'SEMANA DE ATENDIMENTO S.C']]
        if len(s):
            st.markdown('**Solicitações de compra que compõem a S.C.**')
            st.dataframe(s.sort_values(['SEMANA DE ATENDIMENTO S.C']), use_container_width=True, hide_index=True)
            st.info('S.C. sem semana de atendimento não cobre a projeção; permanece visível como compromisso em aberto.')

        f = op[op['CÓDIGO PRODUTO'] == code][['ORDEM DE PRODUÇÃO', 'CÓDIGO PRODUTO', 'SEMANA DE ENTREGA']].sort_values(['SEMANA DE ENTREGA', 'ORDEM DE PRODUÇÃO'])
        if len(f):
            st.markdown('**OPs que compõem a fabricação (1 OP = 1 peça)**')
            st.dataframe(f, use_container_width=True, hide_index=True)

with tab2:
    st.subheader('Demanda por Projeto')
    st.caption('S.A.: G = Pendência e N = Semana de Necessidade. Sem N numérico, a linha não entra no MRP.')
    codes = sorted(rg_mrp['Código'].unique())
    if codes:
        code2 = st.selectbox('Material', codes, format_func=lambda x: f'{x} — {desc.get(x, "")}', key='project_code')
        d = rg_mrp[rg_mrp['Código'] == code2][['Código', 'Projeto', 'Pendência', 'Semana']].sort_values(['Semana', 'Projeto'])
        st.dataframe(d, use_container_width=True, height=520, hide_index=True)
        st.subheader('Resumo por semana')
        r = d.groupby('Semana', as_index=False).agg(Projetos=('Projeto', 'nunique'), Demanda=('Pendência', 'sum'))
        st.dataframe(r.sort_values('Semana'), use_container_width=True, hide_index=True)

with st.expander('Regras do motor V1'):
    st.markdown('''
- **Cadastro:** B Código, C Descrição, D Tipo; linha 1 vazia e cabeçalho na linha 2.
- **Estoque:** A Código Material + E Saldo Disponível.
- **S.A.:** C Código + G Pendência; só entra quando N Semana de Necessidade for numérica.
- **P.C.:** A Código + J Quantidade; L define a semana de chegada.
- **S.C.:** A Código + D Quantidade; F define a semana. S.C. sem F não entra na cobertura da projeção.
- **Fabricação:** B Código Produto + E Semana de Entrega; cada OP distinta vale 1 peça.
- **Demanda TC/TP:** H Material + J Quantidade + L Semana de Necessidade.
''')
