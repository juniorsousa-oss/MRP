from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')
s=s.replace('def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp):', 'def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):')
s=s.replace('"compra_mrp":records(compra_mrp)}', '"compra_mrp":records(compra_mrp),"compras":records(compras)}')
s=s.replace('save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp)', 'save_snapshot(semana_atual,usuario_mrp,macro,proj,demanda_projeto,compras_mrp,cp)')
old='''            st.markdown("**S.A. — projetos que geram a demanda**")\n            st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)'''
new='''            st.markdown("**S.A. — projetos que geram a demanda**")\n            st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)\n            d_comp = compras[compras["Código"].astype(str) == selecionado].copy()\n            if not d_comp.empty:\n                COMP_COLS = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]\n                d_comp = fix_columns(d_comp, COMP_COLS)\n                st.markdown("**Compras**")\n                st.dataframe(d_comp, use_container_width=True, hide_index=True, column_order=COMP_COLS)\n                st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")'''
if old not in s: raise SystemExit('detail marker not found')
s=s.replace(old,new,1)
s=s.replace('    comp = snapshot_df(snap, "compra_mrp").copy()\n', '    comp = snapshot_df(snap, "compra_mrp").copy()\n    compras = snapshot_df(snap, "compras").copy()\n')
s=s.replace('''            if linhas:\n                selecionado = str(f.iloc[linhas[0]]["Código"])''','''            if linhas:\n                selecionado = str(f.iloc[linhas[0]]["Código"])''')
# Ensure detail variables and purchases are only rendered after a selection.
start='''        if not f.empty:\n            linhas = getattr(getattr(selecao, "selection", None), "rows", []) or []\n            if linhas:'''
replacement='''        if not f.empty:\n            linhas = getattr(getattr(selecao, "selection", None), "rows", []) or []\n            if linhas:'''
# Rewrite the block indentation by moving detail rendering under if linhas.
needle='''                desc = f.loc[f["Código"].astype(str) == selecionado, "Descrição"].iloc[0]\n            st.markdown("### Detalhamento do material")'''
repl='''                desc = f.loc[f["Código"].astype(str) == selecionado, "Descrição"].iloc[0]\n                st.markdown("### Detalhamento do material")'''
if needle not in s: raise SystemExit('detail indentation marker not found')
s=s.replace(needle,repl,1)
s=s.replace('''            st.markdown("**Projeção semanal**")''','''                st.markdown("**Projeção semanal**")''',1)
s=s.replace('''            st.dataframe(d_proj, use_container_width=True, hide_index=True, column_order=PROJ_COLS)''','''                st.dataframe(d_proj, use_container_width=True, hide_index=True, column_order=PROJ_COLS)''',1)
s=s.replace('''            st.markdown("**S.A. — projetos que geram a demanda**")''','''                st.markdown("**S.A. — projetos que geram a demanda**")''',1)
s=s.replace('''            st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)''','''                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)''',1)
# indent purchase block generated above by 4 spaces so it stays inside selection block
s=s.replace('''            d_comp = compras[compras["Código"].astype(str) == selecionado].copy()''','''                d_comp = compras[compras["Código"].astype(str) == selecionado].copy()''',1)
s=s.replace('''            if not d_comp.empty:''','''                if not d_comp.empty:''',1)
s=s.replace('''                COMP_COLS = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]''','''                    COMP_COLS = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]''',1)
s=s.replace('''                d_comp = fix_columns(d_comp, COMP_COLS)''','''                    d_comp = fix_columns(d_comp, COMP_COLS)''',1)
s=s.replace('''                st.markdown("**Compras**")''','''                    st.markdown("**Compras**")''',1)
s=s.replace('''                st.dataframe(d_comp, use_container_width=True, hide_index=True, column_order=COMP_COLS)''','''                    st.dataframe(d_comp, use_container_width=True, hide_index=True, column_order=COMP_COLS)''',1)
s=s.replace('''                st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")''','''                    st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")''',1)
p.write_text(s,encoding='utf-8')
