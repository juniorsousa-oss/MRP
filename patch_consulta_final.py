from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')
old='''    proj = snapshot_df(snap, "projecao_semanal").copy()\n    dem = snapshot_df(snap, "demanda_projeto").copy()\n    comp = snapshot_df(snap, "compra_mrp").copy()\n    compras = snapshot_df(snap, "compras").copy()'''
new='''    proj = snapshot_df(snap, "projecao_semanal").copy()\n    dem = snapshot_df(snap, "demanda_projeto").copy()\n    comp = snapshot_df(snap, "compra_mrp").copy()\n    compras = snapshot_df(snap, "compras").copy()\n\n    # Espelho do ADMIN: snapshots antigos podem não ter o campo Período da Semana.\n    # Nesse caso, reconstruímos exatamente pela mesma regra de semana usada no ADMIN.\n    if "Semana" in proj.columns:\n        if "Período da Semana" not in proj.columns:\n            proj["Período da Semana"] = proj["Semana"].apply(periodo_semana)\n        else:\n            faltantes = proj["Período da Semana"].isna() | proj["Período da Semana"].astype(str).str.strip().eq("")\n            proj.loc[faltantes, "Período da Semana"] = proj.loc[faltantes, "Semana"].apply(periodo_semana)'''
if old not in s: raise SystemExit('consulta data block not found')
s=s.replace(old,new,1)
old='''        _mrp_sig=hashlib.sha256(b"".join([f.getvalue() for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]])).hexdigest()'''
new='''        _mrp_sig=hashlib.sha256(b"MRP-SNAPSHOT-V3-COMPRAS-PERIODO"+b"".join([f.getvalue() for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]])).hexdigest()'''
if old not in s: raise SystemExit('signature block not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
# force workflow rerun
p.write_text(p.read_text(encoding='utf-8')+'\n# trigger-final-2\n',encoding='utf-8')
