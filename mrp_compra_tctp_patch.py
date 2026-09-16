COMPRA_TCTP_PATCH = r"""
# =========================================================
# COMPRA MRP — COMPLEMENTO DE DEMANDA TC/TP
# + EXIBIÇÃO DE DECIMAIS NO PADRÃO BRASILEIRO
# =========================================================

# 1) Formatação SOMENTE VISUAL. Os DataFrames de cálculo/exportação continuam
# numéricos; apenas as cópias enviadas para st.dataframe usam vírgula decimal.
_fmt_anchor = 'def formatar_data_br(s):\n    dt=pd.to_datetime(s,errors="coerce",dayfirst=True); return "" if pd.isna(dt) else dt.strftime("%d/%m/%Y")\n'
_fmt_insert = '''def formatar_data_br(s):
    dt=pd.to_datetime(s,errors="coerce",dayfirst=True); return "" if pd.isna(dt) else dt.strftime("%d/%m/%Y")

def _numero_exibicao_br(valor):
    if pd.isna(valor):
        return ""
    try:
        n=float(valor)
    except Exception:
        return valor
    if abs(n-round(n))<=1e-9:
        return str(int(round(n)))
    return f"{n:.6f}".rstrip("0").rstrip(".").replace(".",",")

def _df_exibicao_br(df):
    if not isinstance(df,pd.DataFrame):
        return df
    out=df.copy()
    colunas_quantidade={
        "Saldo em Estoque","Demanda","Demanda S.A.","Demanda TC/TP","P.C.","S.C.",
        "Produzindo","DIV","Saldo Inicial","Resumo Final","Necessidade","Estoque",
        "Pré Nota","Fabricação","Quantidade S.C.","Quantidade P.C.","Quantidade","qnt"
    }
    for c in [c for c in out.columns if c in colunas_quantidade]:
        serie_num=pd.to_numeric(out[c],errors="coerce")
        mascara=serie_num.notna()
        if mascara.any():
            out[c]=out[c].astype(object)
            out.loc[mascara,c]=serie_num.loc[mascara].map(_numero_exibicao_br)
    if "Ação" in out.columns:
        out["Ação"]=out["Ação"].fillna("").astype(str).map(
            lambda s: re.sub(r"(?<=\\d)\\.(?=\\d)", ",", s)
        )
    return out
'''
if _fmt_anchor not in _source:
    raise RuntimeError("Função de data não encontrada para formatação decimal brasileira.")
_source=_source.replace(_fmt_anchor,_fmt_insert,1)

# Aplica a cópia formatada nas principais tabelas do ADMIN e CONSULTA.
_display_replacements = [
    ('            f,\n            use_container_width=True,', '            _df_exibicao_br(f),\n            use_container_width=True,'),
    ('st.dataframe(d_proj, use_container_width=True, hide_index=True, column_order=PROJ_COLS)', 'st.dataframe(_df_exibicao_br(d_proj), use_container_width=True, hide_index=True, column_order=PROJ_COLS)'),
    ('st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)', 'st.dataframe(_df_exibicao_br(d_dem), use_container_width=True, hide_index=True, column_order=DEM_COLS)'),
    ('st.dataframe(d_comp[compras_cols], use_container_width=True, hide_index=True, column_order=compras_cols)', 'st.dataframe(_df_exibicao_br(d_comp[compras_cols]), use_container_width=True, hide_index=True, column_order=compras_cols)'),
    ('st.dataframe(f, use_container_width=True, hide_index=True, column_order=DEM_COLS)', 'st.dataframe(_df_exibicao_br(f), use_container_width=True, hide_index=True, column_order=DEM_COLS)'),
    ('st.dataframe(v[macro_cols],use_container_width=True,height=500,hide_index=True,on_select="rerun",selection_mode="single-row",key="demanda_geral_tabela")', 'st.dataframe(_df_exibicao_br(v[macro_cols]),use_container_width=True,height=500,hide_index=True,on_select="rerun",selection_mode="single-row",key="demanda_geral_tabela")'),
    ('st.dataframe(w[["Código","Descrição","Tipo","Semana","Período da Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]],use_container_width=True,hide_index=True)', 'st.dataframe(_df_exibicao_br(w[["Código","Descrição","Tipo","Semana","Período da Semana","Saldo Inicial","Demanda","P.C.","S.C.","Produzindo","Resumo Final"]]),use_container_width=True,hide_index=True)'),
    ('st.dataframe(d,use_container_width=True,hide_index=True)', 'st.dataframe(_df_exibicao_br(d),use_container_width=True,hide_index=True)'),
    ('st.dataframe(compras[["Código","Nº S.C.","Quantidade S.C.","Semana S.C.","Nº P.C.","Quantidade P.C.","Semana P.C."]],use_container_width=True,hide_index=True)', 'st.dataframe(_df_exibicao_br(compras[["Código","Nº S.C.","Quantidade S.C.","Semana S.C.","Nº P.C.","Quantidade P.C.","Semana P.C."]]),use_container_width=True,hide_index=True)'),
    ('st.dataframe(f,use_container_width=True,hide_index=True)', 'st.dataframe(_df_exibicao_br(f),use_container_width=True,hide_index=True)'),
    ('st.dataframe(d,use_container_width=True,height=600,hide_index=True)', 'st.dataframe(_df_exibicao_br(d),use_container_width=True,height=600,hide_index=True)'),
    ('st.dataframe(d_fab[fab_cols], use_container_width=True, hide_index=True, column_order=fab_cols)', 'st.dataframe(_df_exibicao_br(d_fab[fab_cols]), use_container_width=True, hide_index=True, column_order=fab_cols)'),
]
for _old_display,_new_display in _display_replacements:
    if _old_display in _source:
        _source=_source.replace(_old_display,_new_display,1)

# 2) A Compra MRP original cobre a falta encontrada na Demanda por Projeto (S.A.).
# O saldo faltante global que ainda não foi representado nessas linhas e possui
# Demanda TC/TP é alocado às OPs TC/TP por semana de necessidade.
_fab_anchor = 'fab_det=op[["ORDEM DE PRODUÇÃO","Código Produto","Semana Entrega"]].sort_values(["Código Produto","Semana Entrega","ORDEM DE PRODUÇÃO"]).copy(); fab_det["Quantidade"]=1\n'
_tc_purchase_code = '''# Complemento da Compra MRP para demandas originadas do MRP TC/TP.
if len(tc_rows) and len(macro):
    _compra_sa_tmp=compras_mrp.copy()
    if len(_compra_sa_tmp):
        _compra_sa_tmp["_Código"]=pd.to_numeric(_compra_sa_tmp["produto"],errors="coerce")
        _compra_sa_tmp["_Qtd"]=pd.to_numeric(_compra_sa_tmp["qnt"],errors="coerce").fillna(0.0)
        _compra_sa_por_codigo=_compra_sa_tmp.dropna(subset=["_Código"]).groupby("_Código")["_Qtd"].sum().to_dict()
    else:
        _compra_sa_por_codigo={}

    _tc_detalhe=tc_rows[["Material","Semana Necessidade","ORDEM DE PRODUÇÃO","Quantidade"]].copy()
    _tc_detalhe["Quantidade"]=pd.to_numeric(_tc_detalhe["Quantidade"],errors="coerce").fillna(0.0)
    _tc_detalhe["ORDEM DE PRODUÇÃO"]=_tc_detalhe["ORDEM DE PRODUÇÃO"].fillna("").astype(str).str.replace(r"\\.0$","",regex=True).str.strip()
    _tc_detalhe=_tc_detalhe[_tc_detalhe["Quantidade"]>1e-9]
    if len(_tc_detalhe):
        _tc_detalhe=(
            _tc_detalhe.groupby(["Material","Semana Necessidade","ORDEM DE PRODUÇÃO"],as_index=False,dropna=False)["Quantidade"]
            .sum()
            .sort_values(["Material","Semana Necessidade","ORDEM DE PRODUÇÃO"],na_position="last")
        )
        _tc_compras=[]
        for _,_macro_row in macro.iterrows():
            _codigo=int(_macro_row["Código"])
            _demanda_tc=float(pd.to_numeric(_macro_row.get("Demanda TC/TP",0),errors="coerce") or 0)
            _falta_total=max(0.0,-float(pd.to_numeric(_macro_row.get("DIV",0),errors="coerce") or 0))
            _ja_compra=float(_compra_sa_por_codigo.get(float(_codigo),_compra_sa_por_codigo.get(_codigo,0.0)) or 0.0)
            _falta_tc=min(_demanda_tc,max(0.0,_falta_total-_ja_compra))
            if _falta_tc<=1e-9:
                continue
            _linhas_tc=_tc_detalhe[_tc_detalhe["Material"].astype(int)==_codigo]
            _restante_tc=_falta_tc
            for _,_tc_row in _linhas_tc.iterrows():
                if _restante_tc<=1e-9:
                    break
                _qtd_linha=float(_tc_row["Quantidade"])
                if _qtd_linha<=1e-9:
                    continue
                _usar=min(_restante_tc,_qtd_linha)
                _semana_tc=int(_tc_row["Semana Necessidade"])
                _op_tc=str(_tc_row["ORDEM DE PRODUÇÃO"] or "TC/TP").strip()
                _tc_compras.append({
                    "produto":_codigo,
                    "qnt":_usar,
                    "data":ultimo_dia_util_semana(_semana_tc),
                    "psy":"",
                    "cc":"600307",
                    "op":_op_tc,
                    "obs":"MRP",
                    "prioridade":"",
                })
                _restante_tc-=_usar
        if _tc_compras:
            compras_mrp=pd.concat([compras_mrp,pd.DataFrame(_tc_compras)],ignore_index=True)
            compras_mrp["qnt"]=pd.to_numeric(compras_mrp["qnt"],errors="coerce").fillna(0.0).map(
                lambda x:int(x) if float(x).is_integer() else float(x)
            )

fab_det=op[["ORDEM DE PRODUÇÃO","Código Produto","Semana Entrega"]].sort_values(["Código Produto","Semana Entrega","ORDEM DE PRODUÇÃO"]).copy(); fab_det["Quantidade"]=1
'''
if _fab_anchor not in _source:
    raise RuntimeError("Ponto de geração da fabricação não encontrado para incluir compras TC/TP.")
_source=_source.replace(_fab_anchor,_tc_purchase_code,1)

# Texto de exportação agora representa as duas origens de demanda.
_source=_source.replace(
    'if len(compras_mrp): st.caption(f"Arquivo de compra gerado com {len(compras_mrp)} item(ns) que não normalizam na Demanda por Projeto e exigem nova S.C.")',
    'if len(compras_mrp): st.caption(f"Arquivo de compra gerado com {len(compras_mrp)} item(ns) que exigem nova S.C., considerando demandas S.A. e TC/TP.")',
    1,
)
_source=_source.replace(
    'else: st.caption("Nenhum item da Demanda por Projeto exige nova S.C. no momento.")',
    'else: st.caption("Nenhum item das demandas S.A. ou TC/TP exige nova S.C. no momento.")',
    1,
)

# Força novo snapshot para registrar a Compra MRP com complemento TC/TP.
_source=_source.replace(
    'MRP-SNAPSHOT-V6-STATUS-SEPARACAO',
    'MRP-SNAPSHOT-V7-COMPRA-TCTP',
    1,
)
"""
