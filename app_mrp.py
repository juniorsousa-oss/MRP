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
    est = pd.DataFrame({
        "Código": num(er.iloc[:, 0]),
        "Saldo em Estoque": num(er.iloc[:, 4]).fillna(0)
    }).dropna(subset=["Código"])
    est["Código"] = est["Código"].astype("int64")
    est = est.groupby("Código", as_index=False)["Saldo em Estoque"].sum()

    gr = pd.read_excel(BytesIO(gb), sheet_name="RelatorioTratado")
    rg = pd.DataFrame({
        "Código": num(gr.iloc[:, 2]),
        "Pendência": num(gr.iloc[:, 6]).fillna(0),
        "Semana": num(gr.iloc[:, 13]),
        "Projeto": gr.iloc[:, 1].fillna("").astype(str)
    }).dropna(subset=["Código"])
    rg["Código"] = rg["Código"].astype("int64")
    rg_mrp = rg[rg["Semana"].notna() & rg["Semana"].between(1, 53)].copy()
    rg_mrp["Semana"] = rg_mrp["Semana"].astype("int64")

    cr = pd.read_excel(BytesIO(pb), sheet_name="ComprasTratado")
    cp = pd.DataFrame({
        "Código": num(cr.iloc[:, 0]),
        "Quantidade S.C.": num(cr.iloc[:, 3]).fillna(0),
        "Semana S.C.": num(cr.iloc[:, 5]),
        "Quantidade P.C.": num(cr.iloc[:, 9]).fillna(0),
        "Semana P.C.": num(cr.iloc[:, 11])
    }).dropna(subset=["Código"])
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
    mt["Quantidade"] = mt["Quantidade"].fillna(0)
    return cad, est, rg, rg_mrp, cp, mt


st.title("MRP — Planejamento de Necessidades de Materiais")
st.caption("Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. A projeção é calculada semana a semana.")

with st.sidebar:
    st.header("Bases do MRP")
    cadastro_file = st.file_uploader("1. CADASTROS", type=["xlsx", "xlsm", "xltx"])
    estoque_file = st.file_uploader("2. Estoque_Tratado", type=["xlsx", "xlsm"])
    geral_file = st.file_uploader("3. RelatorioGeral_Tratado", type=["xlsx", "xlsm"])
    compras_file = st.file_uploader("4. Compras_Tratado", type=["xlsx", "xlsm"])
    mt_file = st.file_uploader("5. MRP_TC_TP_Tratado", type=["xlsx", "xlsm"])
    st.divider()
    semana_atual = st.number_input("Semana atual", 1, 53, 36, 1)

if not all([cadastro_file, estoque_file, geral_file, compras_file, mt_file]):
    st.info("Envie as 5 planilhas tratadas + o Cadastro para iniciar o MRP.")
    st.stop()

try:
    cad, est, rg, rg_mrp, cp, mt = load_sources(
        cadastro_file.getvalue(), estoque_file.getvalue(), geral_file.getvalue(),
        compras_file.getvalue(), mt_file.getvalue()
    )
except Exception as e:
    st.error(f"Erro ao carregar as bases: {e}")
    st.stop()

# DEMANDA
sa_week = rg_mrp.groupby(["Código", "Semana"], as_index=False)["Pendência"].sum()
sa_week = sa_week.rename(columns={"Pendência": "Demanda S.A."})

tc_rows = mt[(mt["Material"] > 0) & mt["Semana Necessidade"].between(1, 53)]
tc_week = tc_rows.groupby(["Material", "Semana Necessidade"], as_index=False)["Quantidade"].sum()
tc_week.columns = ["Código", "Semana", "Demanda TC/TP"]

# ENTRADAS
pc_week = cp[(cp["Quantidade P.C."] > 0) & cp["Semana P.C."].between(1, 53)].groupby(
    ["Código", "Semana P.C."], as_index=False
)["Quantidade P.C."].sum()
pc_week.columns = ["Código", "Semana", "P.C."]

sc_all = cp[cp["Quantidade S.C."] > 0].groupby("Código", as_index=False)["Quantidade S.C."].sum()
sc_all = sc_all.rename(columns={"Quantidade S.C.": "S.C."})

sc_week = cp[(cp["Quantidade S.C."] > 0) & cp["Semana S.C."].between(1, 53)].groupby(
    ["Código", "Semana S.C."], as_index=False
)["Quantidade S.C."].sum()
sc_week.columns = ["Código", "Semana", "S.C. com Semana"]

# PRODUZINDO: cada OP corresponde a 1 peça do PA/produto.
op = mt[(mt["Código Produto"] > 0) & mt["Semana Entrega"].between(1, 53)].copy()
op = op.drop_duplicates(subset=["ORDEM DE PRODUÇÃO", "Código Produto", "Semana Entrega"])
fab_week = op.groupby(["Código Produto", "Semana Entrega"]).size().reset_index(name="Produzindo")
fab_week.columns = ["Código", "Semana", "Produzindo"]

# MRP MACRO
macro = cad.merge(est, on="Código", how="left")
for df in [
    sa_week.groupby("Código", as_index=False)["Demanda S.A."].sum(),
    tc_week.groupby("Código", as_index=False)["Demanda TC/TP"].sum(),
    pc_week.groupby("Código", as_index=False)["P.C."].sum(),
    sc_all,
    fab_week.groupby("Código", as_index=False)["Produzindo"].sum(),
]:
    macro = macro.merge(df, on="Código", how="left")

for c in ["Saldo em Estoque", "Demanda S.A.", "Demanda TC/TP", "P.C.", "S.C.", "Produzindo"]:
    macro[c] = macro[c].fillna(0.0)

macro["Demanda"] = macro["Demanda S.A."] + macro["Demanda TC/TP"]
macro["DIV"] = macro["Saldo em Estoque"] + macro["P.C."] + macro["S.C."] + macro["Produzindo"] - macro["Demanda"]
macro["Status"] = macro["DIV"].apply(lambda x: "CRIAR S.C." if x < -1e-9 else "OK")

# PROJEÇÃO SEMANAL
events = pd.concat([
    sa_week.assign(Demanda=sa_week["Demanda S.A."], Supply=0)[["Código", "Semana", "Demanda", "Supply"]],
    tc_week.assign(Demanda=tc_week["Demanda TC/TP"], Supply=0)[["Código", "Semana", "Demanda", "Supply"]],
    pc_week.assign(Demanda=0, Supply=pc_week["P.C."])[["Código", "Semana", "Demanda", "Supply"]],
    sc_week.assign(Demanda=0, Supply=sc_week["S.C. com Semana"])[["Código", "Semana", "Demanda", "Supply"]],
    fab_week.assign(Demanda=0, Supply=fab_week["Produzindo"])[["Código", "Semana", "Demanda", "Supply"]],
], ignore_index=True)

events = events[events["Semana"] >= int(semana_atual)]
events = events.groupby(["Código", "Semana"], as_index=False)[["Demanda", "Supply"]].sum()

stock_map = est.set_index("Código")["Saldo em Estoque"].to_dict()
proj_parts = []

for code, g in events.groupby("Código", sort=False):
    g = g.sort_values("Semana").copy()
    stock0 = float(stock_map.get(code, 0))
    g["Saldo Inicial"] = stock0
    g["Saldo Projetado"] = stock0 + (g["Supply"] - g["Demanda"]).cumsum()
    g["Nova S.C."] = 0.0
    g["Status Projeção"] = "OK"
    # Int64 evita conflito do pandas/pyarrow entre texto e número.
    g["Semana Normalização"] = pd.Series(pd.NA, index=g.index, dtype="Int64")

    neg = g["Saldo Projetado"] < -1e-9
    if neg.any():
        first_pos = g.index[neg][0]
        first_week = int(g.loc[first_pos, "Semana"])
        recovery = g[(g["Semana"] > first_week) & (g["Saldo Projetado"] >= -1e-9)]

        if len(recovery):
            recovery_week = int(recovery.iloc[0]["Semana"])
            g.loc[neg, "Status Projeção"] = f"AGUARDAR ENTRADA — NORMALIZA S{recovery_week}"
            g.loc[g["Semana"] == recovery_week, "Status Projeção"] = "NORMALIZA"
            g["Semana Normalização"] = recovery_week
        else:
            buy = max(0.0, -float(g["Saldo Projetado"].min()))
            g.loc[first_pos, "Nova S.C."] = buy
            g["Saldo Final"] = g["Saldo Projetado"] + buy
            g.loc[g["Nova S.C."] > 0, "Status Projeção"] = "CRIAR S.C."
    else:
        g["Saldo Final"] = g["Saldo Projetado"]

    proj_parts.append(g)

proj = pd.concat(proj_parts, ignore_index=True) if proj_parts else pd.DataFrame(
    columns=["Código", "Semana", "Demanda", "Supply", "Saldo Inicial", "Saldo Projetado", "Nova S.C.", "Saldo Final", "Status Projeção", "Semana Normalização"]
)

if len(proj):
    keys = pd.MultiIndex.from_frame(proj[["Código", "Semana"]])
    for src, name in [
        (sa_week.set_index(["Código", "Semana"])["Demanda S.A."], "Demanda S.A."),
        (tc_week.set_index(["Código", "Semana"])["Demanda TC/TP"], "Demanda TC/TP"),
        (pc_week.set_index(["Código", "Semana"])["P.C."], "P.C."),
        (sc_week.set_index(["Código", "Semana"])["S.C. com Semana"], "S.C. com Semana"),
        (fab_week.set_index(["Código", "Semana"])["Produzindo"], "Produzindo"),
    ]:
        proj[name] = src.reindex(keys).fillna(0).to_numpy()
    proj = proj.merge(cad, on="Código", how="left")

if len(proj):
    faltas = proj[proj["Nova S.C."] > 0].groupby("Código").agg(
        **{"Primeira Falta": ("Semana", "min"), "Criar S.C.": ("Nova S.C.", "sum")}
    ).reset_index()
else:
    faltas = pd.DataFrame(columns=["Código", "Primeira Falta", "Criar S.C."])

macro = macro.merge(faltas, on="Código", how="left")
macro["Primeira Falta"] = macro["Primeira Falta"].fillna("")
macro["Criar S.C."] = macro["Criar S.C."].fillna(0.0)

# DETALHAMENTOS
demanda_projeto = rg_mrp[["Código", "Projeto", "Pendência", "Semana"]].rename(columns={"Pendência": "Quantidade"}).sort_values(["Código", "Semana", "Projeto"])
pc_det = cp[cp["Quantidade P.C."] > 0].sort_values(["Código", "Semana P.C."]).copy()
sc_det = cp[cp["Quantidade S.C."] > 0].sort_values(["Código", "Semana S.C."]).copy()
fab_det = op[["ORDEM DE PRODUÇÃO", "Código Produto", "Semana Entrega"]].sort_values(["Código Produto", "Semana Entrega", "ORDEM DE PRODUÇÃO"]).copy()
fab_det["Quantidade"] = 1

# TELA
m = st.columns(5)
m[0].metric("Materiais no cadastro", f"{len(cad):,}")
m[1].metric("Demanda total", f"{macro['Demanda'].sum():,.0f}")
m[2].metric("P.C.", f"{macro['P.C.'].sum():,.0f}")
m[3].metric("S.C. aberta", f"{macro['S.C.'].sum():,.0f}")
m[4].metric("Criar S.C.", f"{macro['Criar S.C.'].sum():,.0f}")

tab1, tab2 = st.tabs(["DEMANDA GERAL", "DEMANDA POR PROJETO"])

macro_cols = ["Código", "Descrição", "Tipo", "Saldo em Estoque", "Demanda", "P.C.", "S.C.", "Produzindo", "DIV", "Status"]

with tab1:
    st.subheader("Demanda Geral")
    c1, c2, c3 = st.columns(3)
    with c1:
        busca = st.text_input("Código / descrição")
    with c2:
        status_opts = ["OK", "CRIAR S.C."]
        status = st.multiselect("Status", status_opts, default=status_opts)
    with c3:
        tipos = st.multiselect("Tipo", sorted([x for x in cad["Tipo"].unique() if x]))

    v = macro.copy()
    if busca:
        b = busca.strip()
        v = v[v["Código"].astype(str).str.contains(b, na=False) | v["Descrição"].str.contains(b, case=False, na=False)]
    if status:
        v = v[v["Status"].isin(status)]
    if tipos:
        v = v[v["Tipo"].isin(tipos)]

    v = v.sort_values(["Status", "Código"], key=lambda s: s.map({"CRIAR S.C.": 0, "OK": 1}).fillna(2) if s.name == "Status" else s)
    st.dataframe(v[macro_cols], use_container_width=True, height=500, hide_index=True)

    if len(v):
        st.divider()
        st.subheader("Detalhamento do material")
        desc_map = cad.set_index("Código")["Descrição"].to_dict()
        code = st.selectbox("Material", v["Código"].tolist(), format_func=lambda x: f"{x} — {desc_map.get(x, '')}")

        w = proj[proj["Código"] == code].copy()
        if len(w):
            wcols = ["Código", "Descrição", "Tipo", "Semana", "Saldo Inicial", "Demanda S.A.", "Demanda TC/TP", "Demanda", "P.C.", "S.C. com Semana", "Produzindo", "Saldo Projetado", "Nova S.C.", "Saldo Final", "Status Projeção"]
            st.markdown("**Projeção semanal**")
            st.dataframe(w[wcols], use_container_width=True, hide_index=True)

        d = demanda_projeto[demanda_projeto["Código"] == code]
        if len(d):
            st.markdown("**S.A. — projetos que geram a demanda**")
            st.dataframe(d, use_container_width=True, hide_index=True)

        p = pc_det[pc_det["Código"] == code]
        if len(p):
            st.markdown("**P.C. — pedidos que compõem o total**")
            st.dataframe(p, use_container_width=True, hide_index=True)

        s = sc_det[sc_det["Código"] == code]
        if len(s):
            st.markdown("**S.C. — solicitações que compõem o total**")
            st.dataframe(s, use_container_width=True, hide_index=True)
            st.caption("S.C. sem semana permanece no macro, mas não cobre a projeção até possuir previsão definida.")

        f = fab_det[fab_det["Código Produto"] == code]
        if len(f):
            st.markdown("**Produzindo — OPs (1 OP = 1 peça)**")
            st.dataframe(f, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Demanda por Projeto")
    c1, c2 = st.columns(2)
    with c1:
        busca2 = st.text_input("Código / projeto")
    with c2:
        semana_filtro = st.multiselect("Semanas", sorted(demanda_projeto["Semana"].unique().tolist()))

    d = demanda_projeto
    if busca2:
        b2 = busca2.strip()
        d = d[d["Código"].astype(str).str.contains(b2, na=False) | d["Projeto"].str.contains(b2, case=False, na=False)]
    if semana_filtro:
        d = d[d["Semana"].isin(semana_filtro)]
    st.dataframe(d, use_container_width=True, height=600, hide_index=True)

# EXPORTAÇÕES
st.divider()
st.subheader("Exportação de relatórios")
st.caption("Os relatórios são exportados com os mesmos dados calculados na tela.")

export_macro = macro[macro_cols].sort_values(["Status", "Código"], key=lambda s: s.map({"CRIAR S.C.": 0, "OK": 1}).fillna(2) if s.name == "Status" else s).copy()

export_proj = proj[["Código", "Descrição", "Tipo", "Semana", "Saldo Inicial", "Demanda.S.A." if "Demanda.S.A." in proj.columns else "Demanda S.A.", "Demanda TC/TP", "Demanda", "P.C.", "S.C. com Semana", "Produzindo", "Saldo Projetado", "Nova S.C.", "Saldo Final", "Status Projeção"]].sort_values(["Código", "Semana"]).copy()
if "Demanda.S.A." in export_proj.columns:
    export_proj = export_proj.rename(columns={"Demanda.S.A.": "Demanda S.A."})

sheets = {
    "MRP_Geral": export_macro,
    "Projecao_Semanal": export_proj,
    "Demanda_Projeto": demanda_projeto,
    "PC_Detalhe": pc_det,
    "SC_Detalhe": sc_det,
    "Fabricacao": fab_det,
    "Cadastro_Base": cad,
}

excel_data = excel_bytes(sheets)
zip_data = zip_bytes({name + ".csv": csv_bytes(df) for name, df in sheets.items()})

b1, b2, b3 = st.columns(3)
with b1:
    st.download_button("BAIXAR TODOS — EXCEL", excel_data, "MRP_Relatorios_Completos.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with b2:
    st.download_button("BAIXAR TODOS — ZIP/CSV", zip_data, "MRP_Relatorios_Completos.zip", "application/zip", use_container_width=True)
with b3:
    st.download_button("BAIXAR MRP GERAL — CSV", csv_bytes(export_macro), "MRP_Geral.csv", "text/csv", use_container_width=True)
