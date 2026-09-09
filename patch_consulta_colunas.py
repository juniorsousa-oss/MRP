from pathlib import Path
import re

path = Path('app_mrp.py')
text = path.read_text(encoding='utf-8')
new = Path('new_render_consulta.txt').read_text(encoding='utf-8')
pattern = r'def render_consulta_view\(\):.*?(?=\ndef load_sources\()'
updated, count = re.subn(pattern, new.rstrip() + '\n\n', text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('Não foi possível localizar exatamente uma render_consulta_view para substituir.')
path.write_text(updated, encoding='utf-8')
print('render_consulta_view substituída com sucesso')
