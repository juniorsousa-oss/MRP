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
needle='''                desc = f.loc[f["Código"].astype(str) == selecionado, "Descrição"].iloc[0]\n            st.markdown("### Detalhamento do material")'''
repl='''                desc = f.loc[f["Código"].astype(str) == selecionado, "Descrição"].iloc[0]\n                st.markdown("### Detalhamento do material")'''
if needle not in s: raise SystemExit('detail indentation marker not found')
s=s.replace(needle,repl,1)
s=s.replace('''            st.markdown("**Projeção semanal**")''','''                st.markdown("**Projeção semanal**")''',1)
s=s.replace('''            st.dataframe(d_proj, use_container_width=True, hide_index=True, column_order=PROJ_COLS)''','''                st.dataframe(d_proj, use_container_width=True, hide_index=True, column_order=PROJ_COLS)''',1)
s=s.replace('''            st.markdown("**S.A. — projetos que geram a demanda**")''','''                st.markdown("**S.A. — projetos que geram a demanda**")''',1)
s=s.replace('''            st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)''','''                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)''',1)
s=s.replace('''            d_comp = compras[compras["Código"].astype(str) == selecionado].copy()''','''                d_comp = compras[compras["Código"].astype(str) == selecionado].copy()''',1)
s=s.replace('''            if not d_comp.empty:''','''                if not d_comp.empty:''',1)
s=s.replace('''                COMP_COLS = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]''','''                    COMP_COLS = ["Código", "Nº S.C.", "Quantidade S.C.", "Semana S.C.", "Nº P.C.", "Quantidade P.C.", "Semana P.C."]''',1)
s=s.replace('''                d_comp = fix_columns(d_comp, COMP_COLS)''','''                    d_comp = fix_columns(d_comp, COMP_COLS)''',1)
s=s.replace('''                st.markdown("**Compras**")''','''                    st.markdown("**Compras**")''',1)
s=s.replace('''                st.dataframe(d_comp, use_container_width=True, hide_index=True, column_order=COMP_COLS)''','''                    st.dataframe(d_comp, use_container_width=True, hide_index=True, column_order=COMP_COLS)''',1)
s=s.replace('''                st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")''','''                    st.caption("S.C. sem semana permanece no macro, mas não entra no cálculo semanal até possuir previsão definida.")''',1)
# Visual login refinement: reference-like 3.2:1 image header and tighter card.
s=s.replace('"login_image_height": 210', '"login_image_height": 135')
s=s.replace('int(login_cfg.get("login_image_height") or 210)', 'int(login_cfg.get("login_image_height") or 135)')
s=s.replace('max(140, min(300, int(login_cfg.get("login_image_height") or 135)))', 'max(100, min(240, int(login_cfg.get("login_image_height") or 135)))')
s=s.replace('.setta-login-heading {{ text-align:center; padding: 24px 28px 4px; }}', '.setta-login-heading {{ text-align:center; padding: 18px 28px 7px; }}')
s=s.replace('.setta-login-title {{ color:{title_color}; font-size:1.55rem;', '.setta-login-title {{ color:{title_color}; font-size:1.4rem;')
s=s.replace('.setta-login-form-note {{ text-align:center; color:{text}; opacity:.62; font-size:.78rem; margin: 0 0 10px; }}', '.setta-login-form-note {{ text-align:center; color:{text}; opacity:.62; font-size:.78rem; margin: 2px 0 8px; }}')
# Remove duplicate MRP | SETTA title inside the authenticated page; the title already lives in the brand header.
lines=[]
for line in s.splitlines():
    stripped=line.strip()
    if stripped.startswith('st.title(') and ('MRP | SETTA' in stripped or 'app_title' in stripped):
        continue
    if 'st.caption(UI_CONFIG["section_main_description"])' in line:
        indent=line[:len(line)-len(line.lstrip())]
        lines.append(indent+'st.markdown(f\'<div class="setta-main-description">{UI_CONFIG["section_main_description"]}</div>\', unsafe_allow_html=True)')
    else:
        lines.append(line)
s='\n'.join(lines)+'\n'
# Bring the main description closer to the brand header.
anchor='      div.stButton > button[kind="primary"], div.stDownloadButton > button'
if anchor in s and '.setta-main-description' not in s:
    s=s.replace(anchor, '      .setta-main-description { margin-top: -10px; margin-bottom: 12px; color: var(--setta-text); opacity: .78; font-size: .9rem; }\n'+anchor, 1)
# Allow the new login image range in the ADMIN visual settings.
s=s.replace('min_value=140, max_value=300, value=max(140, min(300, int(cfg.get("login_image_height") or 210)))', 'min_value=100, max_value=240, value=max(100, min(240, int(cfg.get("login_image_height") or 135)))')
p.write_text(s,encoding='utf-8')
