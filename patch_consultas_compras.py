from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')
old='''def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp):\n    def records(df):\n        if df is None or df.empty: return []\n        return json.loads(df.to_json(orient="records",force_ascii=False,date_format="iso"))\n    payload={"semana_mrp":int(semana) if semana is not None else None,"usuario":usuario or "Não informado","mrp_geral":records(mrp_geral),"projecao_semanal":records(projecao_semanal),"demanda_projeto":records(demanda_projeto),"compra_mrp":records(compra_mrp)}\n    return _sb_post(payload)'''
new='''def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):\n    def records(df):\n        if df is None or df.empty: return []\n        return json.loads(df.to_json(orient="records",force_ascii=False,date_format="iso"))\n    payload={"semana_mrp":int(semana) if semana is not None else None,"usuario":usuario or "Não informado","mrp_geral":records(mrp_geral),"projecao_semanal":records(projecao_semanal),"demanda_projeto":records(demanda_projeto),"compra_mrp":records(compra_mrp),"compras":records(compras)}\n    return _sb_post(payload)'''
if old not in s: raise SystemExit('save_snapshot block not found')
s=s.replace(old,new,1)
old='save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp)'
new='save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp,cp)'
if old not in s: raise SystemExit('save_snapshot call not found')
s=s.replace(old,new,1)
old='''    comp = snapshot_df(snap, "compra_mrp").copy()'''
new='''    comp = snapshot_df(snap, "compra_mrp").copy()\n    compras = snapshot_df(snap, "compras").copy()'''
if old not in s: raise SystemExit('consulta comp block not found')
s=s.replace(old,new,1)
old='''                st.markdown("**S.A. — projetos que geram a demanda**")\n                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)\n\n    with tab_projeto:'''
new='''                st.markdown("**S.A. — projetos que geram a demanda**")\n                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)\n\n                d_comp = compras[(compras["Código"].astype(str) == selecionado)].copy() if "Código" in compras.columns else pd.DataFrame()\n                if not d_comp.empty:\n                    compras_cols = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]\n                    for c in compras_cols:\n                        if c not in d_comp.columns: d_comp[c] = ""\n                    st.markdown("**Compras**")\n                    st.dataframe(d_comp[compras_cols], use_container_width=True, hide_index=True, column_order=compras_cols)\n                    st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")\n\n    with tab_projeto:'''
if old not in s: raise SystemExit('consulta detail insertion point not found')
s=s.replace(old,new,1)
old='''        "Demanda_Projeto": dem,\n        "Compra_MRP": comp,\n    }'''
new='''        "Demanda_Projeto": dem,\n        "Compra_MRP": comp,\n        "Compras": compras,\n    }'''
if old not in s: raise SystemExit('consulta export sheets block not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
