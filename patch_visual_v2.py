from pathlib import Path

p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')

old='''      [data-testid="stSidebar"] {{ border-right: 1px solid rgba(0,0,0,.08); }}\n      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 22px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); }}\n'''
new='''      [data-testid="stSidebar"] {{ border-right: 1px solid rgba(31,78,120,.12); background: var(--setta-header) !important; }}\n      [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: var(--setta-title) !important; }}\n      [data-testid="stSidebar"] hr {{ margin: 0.65rem 0; border-color: rgba(31,78,120,.12); }}\n      [data-testid="stFileUploader"] {{ border: 1px solid rgba(31,78,120,.14); border-radius: 10px; padding: 4px; background: rgba(31,78,120,.025); }}\n      [data-testid="stFileUploaderDropzone"] {{ border-radius: 8px; }}\n      [data-testid="stAlert"] {{ border-radius: 10px; }}\n      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(31,78,120,.12); border-radius: 14px; padding: 18px 22px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(31,78,120,.06); }}\n'''
if old not in s: raise SystemExit('CSS anchor not found')
s=s.replace(old,new,1)

old2='''st.title("MRP — Planejamento de Necessidades de Materiais"); st.caption("Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. Projeção calculada semana a semana.")\n'''
if old2 not in s: raise SystemExit('duplicate title anchor not found')
s=s.replace(old2,'',1)

p.write_text(s,encoding='utf-8')
print('visual v2 applied')
