from pathlib import Path
import re

path = Path('app_mrp.py')
text = path.read_text(encoding='utf-8')

# Corrige a regra quebrada do cartão sem tocar nas demais regras.
text, n = re.subn(
    r'(?m)^      \.setta-brand background:.*$',
    '      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height:130px; display:flex; align-items:center; justify-content:center; }}',
    text,
    count=1,
)
if n != 1:
    raise SystemExit('Regra .setta-brand quebrada não encontrada')

# Centraliza a logo no cartão.
text, n = re.subn(
    r'(?m)^      \.setta-brand-logo \{\{.*?\}\}$',
    '      .setta-brand-logo {{ width:100%; display:flex; align-items:center; justify-content:center; }}',
    text,
    count=1,
)
if n != 1:
    raise SystemExit('Regra .setta-brand-logo não encontrada')

# O título/objetivo não devem mais existir dentro do cartão.
pattern = r'(?m)^    st\.markdown\(f\'<div class="setta-brand">\{logo_html\}.*?unsafe_allow_html=True\)\)$'
replacement = "    st.markdown(f'<div class=\"setta-brand\">{logo_html}</div>', unsafe_allow_html=True)"
text, n = re.subn(pattern, replacement, text, count=1)
if n != 1:
    raise SystemExit('Renderização do cabeçalho não encontrada')

path.write_text(text, encoding='utf-8')
print('OK: balão restaurado, logo centralizada e texto removido do balão.')