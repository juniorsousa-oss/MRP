from pathlib import Path

path = Path('app_mrp.py')
text = path.read_text(encoding='utf-8')

old_css = '      .setta-brand background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height:130px; display:flex; align-items:center !important; justify-content:center !important;}}'
new_css = '      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height:130px; display:flex; align-items:center; justify-content:center; }}'
if old_css not in text:
    raise SystemExit('CSS do balão não encontrado')
text = text.replace(old_css, new_css, 1)

old_logo = '      .setta-brand-logo {{ justify-self:center !important; align-self:center !important;}}'
new_logo = '      .setta-brand-logo {{ width:100%; display:flex; align-items:center; justify-content:center; }}'
if old_logo not in text:
    raise SystemExit('CSS da logo não encontrado')
text = text.replace(old_logo, new_logo, 1)

old_html = '    st.markdown(f\'<div class="setta-brand">{logo_html}<div class="setta-brand-center"><div class="setta-brand-title">{title}</div><div class="setta-brand-objective">{objective}</div></div><div></div></div>\', unsafe_allow_html=True)'
new_html = '    st.markdown(f\'<div class="setta-brand">{logo_html}</div>\', unsafe_allow_html=True)'
if old_html not in text:
    raise SystemExit('HTML do cabeçalho não encontrado')
text = text.replace(old_html, new_html, 1)

path.write_text(text, encoding='utf-8')
print('OK: balão restaurado, logo centralizada e texto removido do balão.')
