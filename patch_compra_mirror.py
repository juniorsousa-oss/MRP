from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')

# 1) Canonicaliza a estrutura/formatacao da Compra MRP para que ADMIN e CONSULTA
# usem exatamente o mesmo conjunto de colunas e o mesmo tratamento de codigo.
needle='def zip_bytes(files):\n'
helper='''def normalizar_compra_mrp(df):\n    """Formato oficial da Compra MRP, identico no ADMIN e no CONSULTA."""\n    cols=["produto","qnt","data","psy","cc","op","obs","prioridade"]\n    out=df.copy() if df is not None else pd.DataFrame()\n    for c in cols:\n        if c not in out.columns: out[c]=""\n    if "produto" in out.columns:\n        def fmt_produto(x):\n            if pd.isna(x) or str(x).strip()=="": return ""\n            txt=str(x).strip()\n            try:\n                txt=str(int(float(txt)))\n            except Exception:\n                pass\n            return txt.zfill(8)\n        out["produto"]=out["produto"].apply(fmt_produto)\n    if "qnt" in out.columns:\n        out["qnt"]=pd.to_numeric(out["qnt"],errors="coerce").fillna(0)\n        out["qnt"]=out["qnt"].apply(lambda x:int(x) if float(x).is_integer() else float(x))\n    if "data" in out.columns:\n        out["data"]=out["data"].apply(formatar_data_br)\n    for c in ["psy","cc","op","obs","prioridade"]:\n        out[c]=out[c].fillna("").astype(str).str.replace(r"\\.0$","",regex=True).str.strip()\n    return out[cols].reset_index(drop=True)\n\n'''
if needle not in s: raise SystemExit('zip_bytes marker not found')
s=s.replace(needle,helper+needle,1)

# 2) CONSULTA: normaliza o snapshot antes de qualquer exibicao/exportacao.
old='''    comp = snapshot_df(snap, "compra_mrp").copy()\n    compras = snapshot_df(snap, "compras").copy()'''
new='''    comp = normalizar_compra_mrp(snapshot_df(snap, "compra_mrp"))\n    compras = snapshot_df(snap, "compras").copy()'''
if old not in s: raise SystemExit('consulta comp marker not found')
s=s.replace(old,new,1)

# 3) CONSULTA: o botao Compra MRP passa a usar o MESMO XLSX do ADMIN,
# e nao uma serializacao CSV diferente.
old='''    c4.download_button("BAIXAR COMPRA MRP", data=csv_bytes(comp), file_name="Compra_MRP.csv", mime="text/csv", use_container_width=True)'''
new='''    compra_excel_consulta = excel_bytes({"Compra_MRP": comp})\n    c4.download_button("BAIXAR COMPRA MRP", data=compra_excel_consulta, file_name="Compra_MRP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)'''
if old not in s: raise SystemExit('consulta download marker not found')
s=s.replace(old,new,1)

# 4) ADMIN: usa a mesma funcao canonica no Excel/ZIP e no botao individual.
old='''export_macro=macro[macro_cols].sort_values(["Status","Código"],key=lambda s:s.map({"CRIAR S.C.":0,"OK":1}).fillna(2) if s.name=="Status" else s).copy(); export_proj=proj.copy()'''
new='''compras_mrp_export=normalizar_compra_mrp(compras_mrp)\nexport_macro=macro[macro_cols].sort_values(["Status","Código"],key=lambda s:s.map({"CRIAR S.C.":0,"OK":1}).fillna(2) if s.name=="Status" else s).copy(); export_proj=proj.copy()'''
if old not in s: raise SystemExit('admin export marker not found')
s=s.replace(old,new,1)
old='''sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"Compra_MRP":compras_mrp,"Compras":cp,"Fabricacao":fab_det,"Cadastro_Base":cad}'''
new='''sheets={"MRP_Geral":export_macro,"Projecao_Semanal":export_proj,"Demanda_Projeto":demanda_projeto,"Compra_MRP":compras_mrp_export,"Compras":cp,"Fabricacao":fab_det,"Cadastro_Base":cad}'''
if old not in s: raise SystemExit('admin sheets marker not found')
s=s.replace(old,new,1)
old='''compra_excel_data=excel_bytes({"Compra_MRP":compras_mrp})'''
new='''compra_excel_data=excel_bytes({"Compra_MRP":compras_mrp_export})'''
if old not in s: raise SystemExit('admin individual export marker not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('patch applied')
