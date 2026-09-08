import streamlit as st
import pandas as pd
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

st.set_page_config(page_title="MRP | SETTA", page_icon="📦", layout="wide")

def num(s):
    return pd.to_numeric(s, errors="coerce")

def col_by_pos(df, pos, name):
    if df.shape[1] <= pos:
        raise ValueError(f"A base MRP_TC_TP não possui a coluna {name} na posição esperada.")
    df[name] = num(df.iloc[:, pos])

def excel_bytes(sheets):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    bio.seek(0)
    return bio.getvalue()

def csv_bytes(df):
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

def zip_bytes(files):
    bio = BytesIO()
    with ZipFile(bio, "w", ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    bio.seek(0)
    return bio.getvalue()

@st.cache_data(show_spinner=False)
def load_sources(cb, eb, gb, pb, mb):
    raw = pd.read_excel(BytesIO(cb), sheet_name="Listagem do Browse", header=None)
    cad = raw.iloc[2:, [1, 2, 3]].copy()
    cad.columns = ["Código", "Descrição", "Tipo"]
    cad["Código"] = num(cad["Código"])
    cad = cad.dropna(subset=["Código"]).copy()
    cad["Código"] = cad["Código"].astype("int64")
    cad["Descrição"] = cad["Descrição"].fillna("").astype(str).str.strip()
    cad["Tipo"] = cad["Tipo"].fillna("").astype(str).str.strip()
    cad = cad.drop_duplicates("Código", keep="first").reset_index(drop=True)

    er = pd.read_excel(BytesIO(eb), sheet_name="EstoqueTratado")
    est = pd.DataFrame({"Código": num(er.iloc[:, 0]), "Saldo em Estoque": num(er.iloc[:, 4]).fillna(0)}).dropna(subset=["Código"])
    est["Código"] = est["Código"].astype("int64")
    est = est.groupby("Código", as_index=False)["Saldo em Estoque"].sum()

    gr = pd.read_excel(BytesIO(gb), sheet_name="RelatorioTratado")
    rg = pd.DataFrame({
        "Código": num(gr.iloc[:, 2]),
        "Pendência": num(gr.iloc[:, 6]).fillna(0),
        "Data Solicitação": pd.to_datetime(gr.iloc[:, 3], errors="coerce", dayfirst=True),
        "Semana": num(gr.iloc[:, 13]),
        "Projeto": gr.iloc[:, 1].fillna("").astype(str)
    }).dropna(subset=["Código"])
    rg["Código"] = rg["Código"].astype("int64")
    rg_mrp = rg[rg["Semana"].notna() & rg["Semana"].between(1, 53)].copy()
    rg_mrp["Semana"] = rg_mrp["Semana"].astype("int64")

    cr = pd.read_excel(BytesIO(pb), sheet_name="ComprasTratado")
    cp = pd.DataFrame({"Código": num(cr.iloc[:, 0]), "Quantidade S.C.": num(cr.iloc[:, 3]).fillna(0), "Semana S.C.": num(cr.iloc[:, 5]), "Quantidade P.C.": num(cr.iloc[:, 9]).fillna(0), "Semana P.C.": num(cr.iloc[:, 11])}).dropna(subset=["Código"])
    cp["Código"] = cp["Código"].astype("int64")

    mt = pd.read_excel(BytesIO(mb), sheet_name="MRP_TC_TP")
    col_by_pos(mt, 1, "Código Produto")
    col_by_pos(mt, 4, "Semana Entrega")
    col_by_pos(mt, 7, "Material")
    col_by_pos(mt, 9, "Quantidade")
    col_by_pos(mt, 11, "Semana Necessidade")
    mt["Código Produto"] = mt["Código Produto"].fillna(0).astype("int64")
    mt["Semana Entrega"] = mt["Semana Entrega"].fillna(0).astype("int64")
    mt["Material"] = mt["Material"].fillna(0).astype("int64")
    mt["Semana Necessidade"] = mt["Semana Necessidade"].fillna(0).astype("int64")
    mt["Quantidade"] = mt["Quantidade"].fillna(0.0)
    if "ORDEM DE PRODUÇÃO" not in mt.columns:
        mt["ORDEM DE PRODUÇÃO"] = mt.index + 1
    return cad, est, rg, rg_mrp, cp, mt

st.title("MRP — Planejamento de Necessidades de Materiais")
st.caption("Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. Projeção calculada semana a semana.")
with st.sidebar:
    st.header("Bases do MRP")
    cadastro_file = st.file_uploader("1. CADASTROS", type=["xlsx", "xlsm", "xltx"])
    estoque_file = st.file_uploader("2. Estoque_Tratado", type=["xlsx", "xlsm"])
    geral_file = st.file_uploader("3. RelatorioGeral_Tratado", type=["xlsx", "xlsm"])
    compras_file = st.file_uploader("4. Compras_Tratado", type=["xlsx", "xlsm"])
    mt_file = st.file_uploader("5. MRP_TC_TP_Tratado", type=["xlsx", "xlsm"])
if not all([cadastro_file, estoque_file, geral_file, compras_file, mt_file]):
    st.info("Envie as 5 planilhas tratadas + o Cadastro para iniciar o MRP.")
    st.stop()
try:
    cad, est, rg, rg_mrp, cp, mt = load_sources(cadastro_file.getvalue(), estoque_file.getvalue(), geral_file.getvalue(), compras_file.getvalue(), mt_file.getvalue())
except Exception as e:
    st.error(f"Erro ao carregar as bases: {e}")
    st.stop()

rg_semanas = num(rg_mrp["Semana"]).dropna()
rg_semanas = rg_semanas[(rg_semanas >= 1) & (rg_semanas <= 53)]
if len(rg_semanas):
    semana_atual = int(rg_semanas.min())
    fonte_semana = "RelatorioGeral_Tratado — coluna N"
else:
    semanas_base = []
    for s in [cp["Semana P.C."], cp["Semana S.C."], mt["Semana Entrega"], mt["Semana Necessidade"]]:
        v = num(s).dropna(); v = v[(v >= 1) & (v <= 53)]
        if len(v): semanas_base.append(v.astype(int))
    if not semanas_base:
        st.error("Não foi possível identificar a semana atual nas planilhas carregadas."); st.stop()
    semana_atual = min(int(s.min()) for s in semanas_base)
    fonte_semana = "demais bases — fallback"
with st.sidebar:
    st.divider(); st.markdown("**Semana atual identificada nas bases**")
    st.number_input("Semana atual", min_value=1, max_value=53, value=semana_atual, disabled=True)
    st.caption(f"Fonte: {fonte_semana}")

codigos_ii = set(cad.loc[cad["Tipo"].str.upper().eq("II"), "Código"])
sa_week = rg_mrp.groupby(["Código", "Semana"], as_index=False)["Pendência"].sum().rename(columns={"Pendência": "Demanda S.A."})
tc_rows = mt[(mt["Material"] > 0) & mt["Semana Necessidade"].between(1, 53)].copy()
tc_week = tc_rows.groupby(["Material", "Semana Necessidade"], as_index=False)["Quantidade"].sum(); tc_week.columns = ["Código", "Semana", "Demanda TC/TP"]
pc_week = cp[(cp["Quantidade P.C."] > 0) & cp["Semana P.C."].between(1, 53)].groupby(["Código", "Semana P.C."], as_index=False)["Quantidade P.C."].sum(); pc_week.columns = ["Código", "Semana", "P.C."]
sc_all = cp[cp["Quantidade S.C."] > 0].groupby("Código", as_index=False)["Quantidade S.C."].sum().rename(columns={"Quantidade S.C.": "S.C."})
sc_week = cp[(cp["Quantidade S.C."] > 0) & cp["Semana S.C."].between(1, 53)].groupby(["Código", "Semana S.C."], as_index=False)["Quantidade S.C."].sum(); sc_week.columns = ["Código", "Semana", "S.C."]
op = mt[(mt["Código Produto"] > 0) & mt["Semana Entrega"].between(1, 53)].copy()
fab_week = op.groupby(["Código Produto", "Semana Entrega"]).size().reset_index(name="Produzindo"); fab_week.columns = ["Código", "Semana", "Produzindo"]

macro = cad.merge(est, on="Código", how="left")
for df in [sa_week.groupby("Código", as_index=False)["Demanda S.A."].sum(), tc_week.groupby("Código", as_index=False)["Demanda TC/TP"].sum(), pc_week.groupby("Código", as_index=False)["P.C."].sum(), sc_all, fab_week.groupby("Código", as_index=False)["Produzindo"].sum()]:
    macro = macro.merge(df, on="Código", how="left")
for c in ["Saldo em Estoque", "Demanda S.A.", "Demanda TC/TP", "P.C.", "S.C.", "Produzindo"]: macro[c] = macro[c].fillna(0.0)
macro["Demanda"] = macro["Demanda S.A."] + macro["Demanda TC/TP"]
macro.loc[macro["Tipo"].str.upper().eq("II"), "Demanda"] = 0.0
macro["DIV"] = macro["Saldo em Estoque"] + macro["P.C."] + macro["S.C."] + macro["Produzindo"] - macro["Demanda"]
macro["Status"] = macro["DIV"].apply(lambda x: "CRIAR S.C." if x < -1e-9 else "OK")
atividade = ["Saldo em Estoque", "Demanda", "P.C.", "S.C.", "Produzindo"]
macro = macro[macro[atividade].abs().sum(axis=1) > 1e-9].copy()

events = pd.concat([
    sa_week.assign(Demanda=sa_week["Demanda S.A."], Supply=0.0)[["Código", "Semana", "Demanda", "Supply"]],
    tc_week.assign(Demanda=tc_week["Demanda TC/TP"], Supply=0.0)[["Código", "Semana", "Demanda", "Supply"]],
    pc_week.assign(Demanda=0.0, Supply=pc_week["P.C."])[["Código", "Semana", "Demanda", "Supply"]],
    sc_week.assign(Demanda=0.0, Supply=sc_week["S.C."])[["Código", "Semana", "Demanda", "Supply"]],
    fab_week.assign(Demanda=0.0, Supply=fab_week["Produzindo"])[["Código", "Semana", "Demanda", "Supply"]],
], ignore_index=True)
events = events[events["Semana"] >= semana_atual].copy()
events.loc[events["Código"].isin(codigos_ii), "Demanda"] = 0.0
events = events.groupby(["Código", "Semana"], as_index=False)[["Demanda", "Supply"]].sum()
pc_idx = pc_week.set_index(["Código", "Semana"])["P.C."]; sc_idx = sc_week.set_index(["Código", "Semana"])["S.C."]; fab_idx = fab_week.set_index(["Código", "Semana"])["Produzindo"]
stock_map = est.set_index("Código")["Saldo em Estoque"].to_dict(); proj_parts = []
for code, g0 in events.groupby("Código", sort=False):
    g0 = g0.sort_values("Semana"); ultima_semana = int(g0["Semana"].max()); semanas = pd.DataFrame({"Semana": range(semana_atual, ultima_semana + 1)})
    g = semanas.merge(g0, on="Semana", how="left"); g["Código"] = int(code); g["Demanda"] = g["Demanda"].fillna(0.0); g["Supply"] = g["Supply"].fillna(0.0)
    saldo_inicial = float(stock_map.get(code, 0.0)); saldos=[]; finais=[]
    for _, row in g.iterrows():
        saldos.append(saldo_inicial); saldo_final = saldo_inicial + float(row["Supply"]) - float(row["Demanda"]); finais.append(saldo_final); saldo_inicial = saldo_final
    g["Saldo Inicial"] = saldos; g["Resumo Final"] = finais; proj_parts.append(g[["Código", "Semana", "Saldo Inicial", "Demanda", "Resumo Final"]])
proj = pd.concat(proj_parts, ignore_index=True) if proj_parts else pd.DataFrame(columns=["Código", "Semana", "Saldo Inicial", "Demanda", "Resumo Final"])
if len(proj):
    keys = pd.MultiIndex.from_frame(proj[["Código", "Semana"]]); proj["P.C."] = pc_idx.reindex(keys).fillna(0.0).to_numpy(); proj["S.C."] = sc_idx.reindex(keys).fillna(0.0).to_numpy(); proj["Produzindo"] = fab_idx.reindex(keys).fillna(0.0).to_numpy()
    proj["Descrição"] = proj["Código"].map(cad.set_index("Código")["Descrição"].to_dict()); proj["Tipo"] = proj["Código"].map(cad.set_index("Código")["Tipo"].to_dict())

# SEMANA DE ATENDIMENTO / NORMALIZAÇÃO
if len(proj):
    atendimento_map = {}
    for code, g in proj.groupby("Código", sort=False):
        g = g.sort_values("Semana")
        if float(g.iloc[-1]["Resumo Final"]) < -1e-9:
            atendimento_map[int(code)] = "NN"
        else:
            normalizados = g[g["Resumo Final"] >= -1e-9]
            atendimento_map[int(code)] = int(normalizados.iloc[-1]["Semana"]) if len(normalizados) else "NN"
else:
    atendimento_map = {}
macro["Semana de Atendimento"] = macro["Código"].map(atendimento_map).fillna("")

# DETALHAMENTOS
# S.A.: somente projetos com demanda diferente de zero. A descrição vem do Cadastro.
# A última solicitação é a maior data da coluna D para cada projeto no RelatorioGeral_Tratado.
descricao_map = cad.set_index("Código")["Descrição"].to_dict()
ultima_solicitacao = rg.groupby("Projeto", as_index=False)["Data Solicitação"].max().rename(columns={"Data Solicitação": "Última Solicitação"})
demanda_projeto = rg_mrp[~rg_mrp["Código"].isin(codigos_ii) & rg_mrp["Pendência"].ne(0)][["Código", "Projeto", "Pendência", "Semana"]].rename(columns={"Pendência": "Quantidade"})
demanda_projeto["Descrição"] = demanda_projeto["Código"].map(descricao_map).fillna("")
demanda_projeto = demanda_projeto.merge(ultima_solicitacao, on="Projeto", how="left")
demanda_projeto = demanda_projeto[["Código", "Descrição", "Projeto", "Quantidade", "Semana", "Última Solicitação"]].sort_values(["Código", "Semana", "Projeto"])
pc_det = cp[cp["Quantidade P.C."] > 0].sort_values(["Código", "Semana P.C."]).copy()
sc_det = cp[cp["Quantidade S.C."] > 0].sort_values(["Código", "Semana S.C."]).copy()
fab_det = op[["ORDEM DE PRODUÇÃO", "Código Produto", "Semana Entrega"]].sort_values(["Código Produto", "Semana Entrega", "ORDEM DE PRODUÇÃO"]).copy(); fab_det["Quantidade"] = 1

m=st.columns(5); m[0].metric("Materiais no MRP", f"{len(macro):,}"); m[1].metric("Demanda total", f"{macro['Demanda'].sum():,.0f}"); m[2].metric("P.C.", f"{macro['P.C.'].sum():,.0f}"); m[3].metric("S.C.", f"{macro['S.C.'].sum():,.0f}"); criar_sc_total=(-macro.loc[macro["DIV"]<0,"DIV"]).sum(); m[4].metric("Criar S.C.", f"{criar_sc_total:,.0f}")
tab1,tab2=st.tabs(["DEMANDA GERAL","DEMANDA POR PROJETO"])
macro_cols=["Código","Descrição","Tipo","Saldo em Estoque","Demanda","P.C.","S.C.","Produzindo","DIV","Status","Semana de Atendimento"]
with tab1:
    st.subheader("Demanda Geral"); c1,c2,c3=st.columns(3)
    with c1: busca=st.text_input("Código / descrição")
    with c2: status=st.multiselect("Status",["OK","CRIAR S.C."],default=["OK","CRIAR S.C."])
    with c3: tipos=st.multiselect("Tipo",sorted([x for x in cad["Tipo"].unique() if x]))
    v=macro.copy()
    if busca:
        b=busca.strip(); v=v[v["Código"].astype(str).str.contains(b,na=False)|v["Descrição"].str.contains(b,case=False,na=False)]
    if status: v=v[v["Status"].isin(status)]
    if tipos: v=v[v["Tipo"].isin(tipos)]
    v["_ord_status"]=v["Status"].map({"CRIAR S.C.":0,"OK":1}).fillna(2); v=v.sort_values(["_ord_status","Código"]).drop(columns="_ord_status")
    st.markdown("**Clique em uma linha para abrir o detalhamento do material.**")
    selecao=st.dataframe(v[macro_cols],use_container_width=True,height=500,hide_index=True,on_select="rerun",selection_mode="single-row",key="demanda_geral_tabela")
    linhas_selecionadas=selecao.selection.rows if selecao is not None else []; code=None
    if linhas_selecionadas: code=int(v.iloc[linhas_selecionadas[0]]["Código"])
    if code is not None:
        st.divider(); st.subheader("Detalhamento do material"); st.markdown(f"**Material selecionado:** `{code}` — {descricao_map.get(code,'')}")
        w=proj[proj["Código"]==code].copy()
        if len(w): st.markdown("**Projeção semanal**"); st.dataframe(w[["Código","Descrição","Tipo","Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]],use_container_width=True,hide_index=True)
        d=demanda_projeto[demanda_projeto["Código"]==code]
        if len(d): st.markdown("**S.A. — projetos que geram a demanda**"); st.dataframe(d,use_container_width=True,hide_index=True)
        p=pc_det[pc_det["Código"]==code]
        if len(p): st.markdown("**P.C. — pedidos que compõem o total**"); st.dataframe(p,use_container_width=True,hide_index=True)
        s=sc_det[sc_det["Código"]==code]
        if len(s): st.markdown("**S.C. — solicitações que compõem o total**"); st.dataframe(s,use_container_width=True,hide_index=True); st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")
        f=fab_det[fab_det["Código Produto"]==code]
        if len(f): st.markdown("**Produzindo — OPs (1 OP = 1 peça)**"); st.dataframe(f,use_container_width=True,hide_index=True)
with tab2:
    st.subheader("Demanda por Projeto"); c1,c2=st.columns(2)
    with c1: busca2=st.text_input("Código / projeto")
    with c2: semana_filtro=st.multiselect("Semanas",sorted(demanda_projeto["Semana"].unique().tolist()))
    d=demanda_projeto
    if busca2:
        b2=busca2.strip(); d=d[d["Código"].astype(str).str.contains(b2,na=False)|d["Projeto"].str.contains(b2,case=False,na=False)]
    if semana_filtro: d=d[d["Semana"].isin(semana_filtro)]
    st.dataframe(d,use_container_width=True,height=600,hide_index=True)

st.divider(); st.subheader("Exportação de relatórios"); st.caption("Os relatórios são exportados com os mesmos dados calculados na tela.")
export_macro=macro[macro_cols].sort_values(["Status","Código"],key=lambda s:s.map({"CRIAR S.C.":0,"OK":1}).fillna(2) if s.name=="Status" else s).copy(); export_proj=proj[["Código","Descrição","Tipo","Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]].sort_values(["Código","Semana"]).copy()
sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"PC_Detalhe":pc_det,"SC_Detalhe":sc_det,"Fabricacao":fab_det,"Cadastro_Base":cad}
excel_data=excel_bytes(sheets); zip_data=zip_bytes({name+".csv":csv_bytes(df) for name,df in sheets.items()})
b1,b2,b3=st.columns(3)
with b1: st.download_button("BAIXAR TODOS — EXCEL",excel_data,"MRP_Relatorios_Completos.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
with b2: st.download_button("BAIXAR TODOS — ZIP/CSV",zip_data,"MRP_Relatorios_Completos.zip","application/zip",use_container_width=True)
with b3: st.download_button("BAIXAR MRP GERAL — CSV",csv_bytes(export_macro),"MRP_Geral.csv","text/csv",use_container_width=True)