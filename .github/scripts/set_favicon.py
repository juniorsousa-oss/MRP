from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
old = 'st.set_page_config(page_title="MRP | SETTA", page_icon="https://www.settaenergia.com.br/assets/logofootter2.svg", layout="wide")'
new = 'st.set_page_config(page_title="MRP | SETTA", page_icon="assets/mrp_setta_icon.svg", layout="wide")'
if old not in s:
    raise SystemExit('Configuração atual do favicon não encontrada.')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('Favicon atualizado.')
