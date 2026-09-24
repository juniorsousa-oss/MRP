import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date, timedelta
from io import BytesIO

def semana_atual_operacional():
    """Retorna AAAA-SS para semanas iniciadas aos domingos."""
    hoje = date.today()
    domingo = hoje - timedelta(days=(hoje.weekday() + 1) % 7)
    primeiro = date(domingo.year, 1, 1)
    primeiro += timedelta(days=(6 - primeiro.weekday()) % 7)
    return f"{domingo.year}-{((domingo - primeiro).days // 7) + 1:02d}"


def chave_semana(valor, periodo="", data_original=""):
    """Aceita AAAA-SS; converte planilhas antigas pelo início do período."""
    texto = str(valor).strip()
    nova = re.fullmatch(r"(\d{4})[-/](\d{1,2})", texto)
    if nova:
        ano, numero = int(nova.group(1)), int(nova.group(2))
        return f"{ano}-{numero:02d}" if 1 <= numero <= 53 else ""
    antiga = re.fullmatch(r"(\d{1,2})(?:\.0)?", texto)
    if not antiga or not 1 <= int(antiga.group(1)) <= 53:
        return ""
    inicio = re.search(r"\d{2}/\d{2}/\d{4}", str(periodo))
    referencia = pd.to_datetime(inicio.group(0), format="%d/%m/%Y", errors="coerce") if inicio else pd.NaT
    if pd.isna(referencia):
        referencia = pd.to_datetime(data_original, dayfirst=True, errors="coerce")
        if pd.notna(referencia) and referencia.date() < date.today():
            referencia = pd.NaT  # Data vencida pode ter sido enquadrada na semana atual.
    if pd.notna(referencia):
        dia = referencia.date()
        ano = (dia - timedelta(days=(dia.weekday() + 1) % 7)).year
    else:
        ano = date.today().year
    return f"{ano}-{int(antiga.group(1)):02d}"


def semanas_da_base(df, coluna, periodo=None, data=None):
    periodos = df[periodo] if periodo in df.columns else pd.Series("", index=df.index)
    datas = df[data] if data in df.columns else pd.Series("", index=df.index)
    return pd.Series([chave_semana(w, p, d) for w, p, d in zip(df[coluna], periodos, datas)],
                     index=df.index, dtype=str)


st.set_page_config(page_title='MRP | SETTA', page_icon='📦', layout='wide')
st.markdown('''<style>.block-container{padding-top:1rem}.small{font-size:.8rem;color:#666}</style>''', unsafe_allow_html=True)

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
    semana_atual = st.text_input('Semana atual (AAAA-SS)', value=semana_atual_operacional())

if not all([cadastro_file, estoque_file, geral_file, compras_file, mt_file]):
    st.info('Envie as 5 planilhas tratadas + o Cadastro para iniciar o MRP.')
    st.stop()

if not re.fullmatch(r'\d{4}-\d{2}', semana_atual):
    st.error('Informe a semana atual no formato AAAA-SS (por exemplo, 2027-02).')
    st.stop()


def num(s):
    return pd.to_numeric(s, errors='coerce')

@st.cache_data(show_spinner=False)
def load_sources(cb, eb, gb, pb, mb):
    # CADASTRO: linha 1 vazia; cabeçalho na linha 2 do Excel => header=None e dados a partir do índice 2.
    raw = pd.read_excel(BytesIO(cb), sheet_name='Listagem do Browse', header=None)
    cad = raw.iloc[2:, [1,2,3]].copy()
    cad.columns = ['Código','Descrição','Tipo']
    cad['Código'] = num(cad['Código'])
    cad = cad.dropna(subset=['Código']).copy()
    cad['Código'] = cad['Código'].astype(int)
    cad['Descrição'] = cad['Descrição'].fillna('').astype(str).str.strip()
    cad['Tipo'] = cad['Tipo'].fillna('').astype(str).str.strip()
    cad = cad.drop_duplicates('Código', keep='first')

    est = pd.read_excel(BytesIO(eb), sheet_name='EstoqueTratado')
    est['COD_MATERIAL'] = num(est['COD_MATERIAL'])
    est['SALDO_DISPONIVEL'] = num(est['SALDO_DISPONIVEL']).fillna(0)
    est = est.dropna(subset=['COD_MATERIAL']).copy()
    est['COD_MATERIAL'] = est['COD_MATERIAL'].astype(int)

    rg = pd.read_excel(BytesIO(gb), sheet_name='RelatorioTratado')
    rg['Código'] = num(rg['Código'])
    rg['Semana'] = semanas_da_base(rg, 'SEMANA DE NECESSIDADE', 'PERIODO DA SEMANA', 'DATA MRP')
    rg['Pendência'] = num(rg['Pendência']).fillna(0)
    rg['Projeto'] = rg['Projeto'].fillna('').astype(str)
    rg = rg.dropna(subset=['Código']).copy()
    rg['Código'] = rg['Código'].astype(int)
    rg['Semana válida'] = rg['Semana'].str.match(r'^\d{4}-\d{2}$', na=False)
    rg_mrp = rg[rg['Semana válida']].copy()
    rg_mrp['Semana'] = rg_mrp['Semana'].astype(str)

    cp = pd.read_excel(BytesIO(pb), sheet_name='ComprasTratado')
    cp['CÓD'] = num(cp['CÓD'])
    for c in ['QUANTIDADE S.C','QUANTIDADE P.C']:
        cp[c] = num(cp[c]).fillna(0)
    cp = cp.dropna(subset=['CÓD']).copy()
    cp['CÓD'] = cp['CÓD'].astype(int)
    cp['SEMANA DE ATENDIMENTO S.C'] = semanas_da_base(cp, 'SEMANA DE ATENDIMENTO S.C', 'PERIODO DA SEMANA S.C', 'DATA DA S.C')
    cp['SEMANA DE ATENDIMENTO P.C'] = semanas_da_base(cp, 'SEMANA DE ATENDIMENTO P.C', 'PERIODO DA SEMANA P.C', 'DATA DA P.C')

    mt = pd.read_excel(BytesIO(mb), sheet_name='MRP_TC_TP')
    for c in ['CÓDIGO PRODUTO','MATERIAL','QUANTIDADE POR OF','QUANTIDADE TOTAL PREVISTA ENTREGA NA SEMANA','NECESSIDADE TOTAL DA SEMANA']:
        if c in mt.columns: mt[c] = num(mt[c])
    mt['CÓDIGO PRODUTO'] = mt['CÓDIGO PRODUTO'].fillna(0).astype(int)
    mt['MATERIAL'] = mt['MATERIAL'].fillna(0).astype(int)
    mt['SEMANA DE ENTREGA'] = semanas_da_base(mt, 'SEMANA DE ENTREGA', 'PERIODO DA SEMANA DE ENTREGA', 'DATA DE ENTREGA')
    mt['SEMANA DE NECESSIDADE'] = semanas_da_base(mt, 'SEMANA DE NECESSIDADE', 'PERIODO DA SEMANA DE NECESSIDADE', 'DATA DE NECESSIDADE')
    mt['QUANTIDADE POR OF'] = mt['QUANTIDADE POR OF'].fillna(0)
    mt['QUANTIDADE TOTAL PREVISTA ENTREGA NA SEMANA'] = mt['QUANTIDADE TOTAL PREVISTA ENTREGA NA SEMANA'].fillna(0)
    mt['NECESSIDADE TOTAL DA SEMANA'] = mt['NECESSIDADE TOTAL DA SEMANA'].fillna(0)
    return cad, est, rg, rg_mrp, cp, mt

cad, est, rg, rg_mrp, cp, mt = load_sources(cadastro_file.getvalue(), estoque_file.getvalue(), geral_file.getvalue(), compras_file.getvalue(), mt_file.getvalue())

# ===================== MOTOR =====================
# DEMANDA S.A.: G somente quando N é número; semanal = G agrupado por código + N.
sa_total = rg_mrp.groupby('Código')['Pendência'].sum()
sa_week = rg_mrp.groupby(['Código','Semana'])['Pendência'].sum()

# DEMANDA TC/TP: H + J + L. Soma da quantidade J por material e semana.
tc_rows = mt[(mt['MATERIAL'] > 0) & (mt['SEMANA DE NECESSIDADE'].str.match(r'^\d{4}-\d{2}$', na=False))].copy()
tc_week = tc_rows.groupby(['MATERIAL','SEMANA DE NECESSIDADE'])['QUANTIDADE POR OF'].sum()
tc_week.index.names = ['Código','Semana']
tc_total = tc_week.groupby(level=0).sum()

# P.C.: macro soma J; projeção só considera a quantidade na semana L.
pc_week = cp[(cp['QUANTIDADE P.C'] > 0) & (cp['SEMANA DE ATENDIMENTO P.C'].str.match(r'^\d{4}-\d{2}$', na=False))].groupby(['CÓD','SEMANA DE ATENDIMENTO P.C'])['QUANTIDADE P.C'].sum()
pc_week.index.names = ['Código','Semana']
pc_total = cp[cp['QUANTIDADE P.C'] > 0].groupby('CÓD')['QUANTIDADE P.C'].sum()

# S.C.: macro soma D; projeção somente S.C. com semana F.
sc_all = cp[cp['QUANTIDADE S.C'] > 0].groupby('CÓD')['QUANTIDADE S.C'].sum()
sc_week = cp[(cp['QUANTIDADE S.C'] > 0) & (cp['SEMANA DE ATENDIMENTO S.C'].str.match(r'^\d{4}-\d{2}$', na=False))].groupby(['CÓD','SEMANA DE ATENDIMENTO S.C'])['QUANTIDADE S.C'].sum()
sc_week.index.names = ['Código','Semana']
sc_dated = sc_week.groupby(level=0).sum()

# FABRICAÇÃO: B + E; cada OP distinta = 1 peça.
op = mt[(mt['CÓDIGO PRODUTO'] > 0) & (mt['SEMANA DE ENTREGA'].str.match(r'^\d{4}-\d{2}$', na=False))][['ORDEM DE PRODUÇÃO','CÓDIGO PRODUTO','SEMANA DE ENTREGA']].drop_duplicates()
fab_week = op.groupby(['CÓDIGO PRODUTO','SEMANA DE ENTREGA']).size().astype(float)
fab_week.index.names = ['Código','Semana']
fab_total = fab_week.groupby(level=0).sum()

# Índice de semanas por material: não cria linhas para semanas sem movimentação.
# Semanas futuras (inclusive 2028–2030) permanecem em ordem cronológica.
from collections import defaultdict
keys = set(sa_week.index)|set(tc_week.index)|set(pc_week.index)|set(sc_week.index)|set(fab_week.index)
weeks = sorted({str(w) for _, w in keys if re.fullmatch(r'\d{4}-\d{2}', str(w))} | {semana_atual})
semanas_por_material = defaultdict(set)
for codigo_material, semana_movimento in keys:
    if re.fullmatch(r'\d{4}-\d{2}', str(semana_movimento)):
        semanas_por_material[codigo_material].add(str(semana_movimento))

stock = est.groupby('COD_MATERIAL')['SALDO_DISPONIVEL'].sum()
desc = cad.set_index('Código')['Descrição'].to_dict()
tipo = cad.set_index('Código')['Tipo'].to_dict()

macro_rows=[]; week_rows=[]
for code in cad['Código']:
    estoque = float(stock.get(code,0))
    saldo = estoque
    first_short = None
    total_new_sc = 0.0
    total_d = total_pc = total_sc_dated = total_fab = 0.0
    # Considera apenas as semanas em que este material tem movimento.
    # Se o estoque inicial está negativo, preserva a criação de S.C. na primeira
    # semana do horizonte, mesmo sem movimento (regra anterior do motor).
    semanas_material = set(semanas_por_material.get(code, ()))
    if saldo < 0 and weeks:
        semanas_material.add(weeks[0])
    for wk in sorted(semanas_material):
        dsa = float(sa_week.get((code,wk),0))
        dtc = float(tc_week.get((code,wk),0))
        demand = dsa + dtc
        pc = float(pc_week.get((code,wk),0))
        sc = float(sc_week.get((code,wk),0))
        fab = float(fab_week.get((code,wk),0))
        saldo_antes = saldo + pc + sc + fab - demand
        new_sc = max(0.0, -saldo_antes)
        saldo_final = saldo_antes + new_sc
        if new_sc > 0 and first_short is None: first_short = wk
        total_new_sc += new_sc
        total_d += demand; total_pc += pc; total_sc_dated += sc; total_fab += fab
        # Mesmo com saldo final igual ao anterior, exibe movimentações de
        # entrada/saída; oculta somente semanas sem qualquer alteração.
        if any(v != 0 for v in (dsa,dtc,pc,sc,fab,new_sc)):
            week_rows.append([code,desc.get(code,''),tipo.get(code,''),wk,saldo,dsa,dtc,demand,pc,sc,fab,saldo_antes,new_sc,saldo_final,'CRIAR S.C' if new_sc>0 else 'OK'])
        saldo = saldo_final
    macro_rows.append([code,desc.get(code,''),tipo.get(code,''),estoque,total_d,total_pc,total_sc_dated,float(sc_all.get(code,0)),total_fab,
                       estoque+total_pc+total_sc_dated+total_fab-total_d,total_new_sc,first_short if first_short else '', 'CRIAR S.C' if total_new_sc>0 else 'OK'])

macro = pd.DataFrame(macro_rows,columns=['Código','Descrição','Tipo','Saldo em Estoque','Demanda Total','Pedido de Compra','S.C. com Semana','S.C. Aberta Total','Fabricação','Saldo Macro sem Nova S.C','Criar S.C','Primeira Falta','Status'])
weekly = pd.DataFrame(week_rows,columns=['Código','Descrição','Tipo','Semana','Saldo Inicial','Demanda S.A.','Demanda TC/TP','Demanda Total','P.C.','S.C.','Fabricação','Saldo antes da Nova S.C','Criar S.C','Saldo Final','Status'])

# ===================== UI =====================
active = macro[(macro['Saldo em Estoque']!=0)|(macro['Demanda Total']!=0)|(macro['Pedido de Compra']!=0)|(macro['S.C. Aberta Total']!=0)|(macro['Fabricação']!=0)].copy()

m=st.columns(5)
m[0].metric('Materiais no cadastro',f'{len(cad):,}')
m[1].metric('Demanda total',f'{macro["Demanda Total"].sum():,.0f}')
m[2].metric('P.C.',f'{macro["Pedido de Compra"].sum():,.0f}')
m[3].metric('S.C. aberta',f'{macro["S.C. Aberta Total"].sum():,.0f}')
m[4].metric('Criar S.C.',f'{macro["Criar S.C"].sum():,.0f}')

tab1, tab2 = st.tabs(['DEMANDA GERAL','DEMANDA POR PROJETO'])

with tab1:
    st.subheader('Demanda Geral')
    c1,c2,c3=st.columns(3)
    with c1: busca=st.text_input('Código / descrição')
    with c2: status=st.multiselect('Status',['OK','CRIAR S.C'],default=['OK','CRIAR S.C'])
    with c3: tipos=st.multiselect('Tipo',[x for x in sorted(cad['Tipo'].unique()) if x])
    v=active.copy()
    if busca:
        v=v[v['Código'].astype(str).str.contains(busca,case=False,na=False)|v['Descrição'].str.contains(busca,case=False,na=False)]
    if status: v=v[v['Status'].isin(status)]
    if tipos: v=v[v['Tipo'].isin(tipos)]
    st.dataframe(v.sort_values(['Status','Primeira Falta','Código']),use_container_width=True,height=520,hide_index=True)

    if len(v):
        st.divider(); st.subheader('Projeção do material')
        code=st.selectbox('Material',v['Código'].tolist(),format_func=lambda x:f'{x} — {desc.get(x,"")}')
        w=weekly[weekly['Código']==code].copy()
        w=w[(w['Semana']>=semana_atual)|((w['Demanda Total']!=0)|(w['P.C.']!=0)|(w['S.C.']!=0)|(w['Fabricação']!=0))]
        if w.empty:
            st.info('Este material não possui movimentação semanal no horizonte carregado.')
        else:
            st.dataframe(w,use_container_width=True,hide_index=True)

        d=rg_mrp[rg_mrp['Código']==code][['Código','Projeto','Pendência','Semana']].sort_values(['Semana','Projeto'])
        if len(d):
            st.markdown('**Demandas S.A. que compõem o material**')
            st.dataframe(d,use_container_width=True,hide_index=True)

        p=cp[cp['CÓD']==code][['CÓD','DESCRIÇÃO','QUANTIDADE P.C','DATA DA P.C','SEMANA DE ATENDIMENTO P.C']]
        if len(p):
            st.markdown('**Pedidos de compra que compõem o P.C.**')
            st.dataframe(p.sort_values(['SEMANA DE ATENDIMENTO P.C']),use_container_width=True,hide_index=True)

        s=cp[cp['CÓD']==code][['CÓD','DESCRIÇÃO','QUANTIDADE S.C','DATA DA S.C','SEMANA DE ATENDIMENTO S.C']]
        if len(s):
            st.markdown('**Solicitações de compra que compõem a S.C.**')
            st.dataframe(s.sort_values(['SEMANA DE ATENDIMENTO S.C']),use_container_width=True,hide_index=True)

        f=op[op['CÓDIGO PRODUTO']==code][['ORDEM DE PRODUÇÃO','CÓDIGO PRODUTO','SEMANA DE ENTREGA']].sort_values(['SEMANA DE ENTREGA','ORDEM DE PRODUÇÃO'])
        if len(f):
            st.markdown('**OPs que compõem a fabricação (1 OP = 1 peça)**')
            st.dataframe(f,use_container_width=True,hide_index=True)

        open_sc=s[s['QUANTIDADE S.C']>0]
        if len(open_sc): st.info('S.C. aberta sem semana de atendimento não cobre a projeção; ela permanece visível como compromisso em aberto.')

with tab2:
    st.subheader('Demanda por Projeto')
    st.caption('A demanda S.A. usa G (Pendência) e N (Semana de Necessidade). Sem ano-semana válido, a linha não entra no MRP.')
    codes=sorted(rg_mrp['Código'].unique())
    if codes:
        code2=st.selectbox('Material',codes,format_func=lambda x:f'{x} — {desc.get(x,"")}',key='project_code')
        d=rg_mrp[rg_mrp['Código']==code2][['Código','Projeto','Pendência','Semana']].copy().sort_values(['Semana','Projeto'])
        st.dataframe(d,use_container_width=True,height=520,hide_index=True)
        st.subheader('Resumo por semana')
        r=d.groupby('Semana',as_index=False).agg(Projetos=('Projeto','nunique'),Demanda=('Pendência','sum'))
        st.dataframe(r.sort_values('Semana'),use_container_width=True,hide_index=True)

st.divider()
with st.expander('Regras do motor V1'):
    st.markdown('''
- **Cadastro:** B Código, C Descrição, D Tipo; linha 1 vazia e cabeçalho na linha 2.
- **Estoque:** A Código Material + E Saldo Disponível.
- **S.A.:** C Código + G Pendência; só entra com ano-semana válido.
- **P.C.:** A Código + J Quantidade; L define a semana de chegada.
- **S.C.:** A Código + D Quantidade; F define a semana. S.C. sem F não entra na cobertura da projeção.
- **Fabricação:** B Código do Produto + E Semana de Entrega; cada OP distinta vale 1 peça.
- **Demanda TC/TP:** H Material + J Quantidade + L Semana de Necessidade.
- **Projeção:** apenas semanas com movimento ou criação de S.C.; saldo anterior + P.C. + S.C. datada + fabricação − demanda. Semanas sem movimento mantêm o mesmo saldo e não geram linha.
- **Primeira falta:** quando o saldo fica negativo, o app cria S.C. exatamente para cobrir o déficit daquela primeira semana e normaliza o saldo para zero.
- **S.C. aberta:** continua visível no macro, mas não é considerada cobertura enquanto não houver semana definida.
''')

# Exportação
bio=BytesIO()
with pd.ExcelWriter(bio,engine='openpyxl') as xw:
    macro.to_excel(xw,index=False,sheet_name='MRP_MACRO')
    weekly.to_excel(xw,index=False,sheet_name='MRP_SEMANAL')
    rg_mrp[['Código','Projeto','Pendência','Semana']].sort_values(['Código','Semana','Projeto']).to_excel(xw,index=False,sheet_name='DEMANDA_PROJETOS')
    cp.to_excel(xw,index=False,sheet_name='COMPRAS_BASE')
    op.to_excel(xw,index=False,sheet_name='FABRICACAO_OPS')
    tc_rows[['MATERIAL','QUANTIDADE POR OF','SEMANA DE NECESSIDADE']].to_excel(xw,index=False,sheet_name='DEMANDA_TC_TP')
bio.seek(0)
st.download_button('Exportar conferência do MRP (.xlsx)',bio.getvalue(),'MRP_Conferencia.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
