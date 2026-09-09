from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')
old='''        f = fix_columns(f, MRP_COLS)\n        st.dataframe(f, use_container_width=True, hide_index=True, column_order=MRP_COLS)\n\n        if not f.empty:\n            opcoes = f["Código"].astype(str).drop_duplicates().tolist()\n            selecionado = st.selectbox("Material selecionado", opcoes, key="consulta_material")\n            d_proj = fix_columns(proj[proj["Código"].astype(str) == str(selecionado)], PROJ_COLS)\n            d_dem = fix_columns(dem[dem["Produto"].astype(str) == str(selecionado)], DEM_COLS)\n            desc = f.loc[f["Código"].astype(str) == str(selecionado), "Descrição"].iloc[0]\n'''
new='''        f = fix_columns(f, MRP_COLS)\n        # Seleção por checkbox/linha: mantém o visualizador igual ao ADMIN e evita\n        # um segundo seletor separado para escolher o material.\n        selecao = st.dataframe(\n            f,\n            use_container_width=True,\n            hide_index=True,\n            column_order=MRP_COLS,\n            on_select="rerun",\n            selection_mode="single-row",\n            key="consulta_mrp_table",\n        )\n\n        if not f.empty:\n            linhas = getattr(getattr(selecao, "selection", None), "rows", []) or []\n            if linhas:\n                selecionado = str(f.iloc[linhas[0]]["Código"])\n                d_proj = fix_columns(proj[proj["Código"].astype(str) == selecionado], PROJ_COLS)\n                d_dem = fix_columns(dem[dem["Produto"].astype(str) == selecionado], DEM_COLS)\n                desc = f.loc[f["Código"].astype(str) == selecionado, "Descrição"].iloc[0]\n'''
if old not in s:
    raise SystemExit('trecho alvo não encontrado')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
