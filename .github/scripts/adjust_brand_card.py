from pathlib import Path

path = Path("app_mrp.py")
text = path.read_text(encoding="utf-8")

old_css = '      .setta-brand background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height:130px; display:flex; align-items:center !important; justify-content:center !important;}}'
new_css = '      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height:130px; display:flex; align-items:center; justify-content:center; }}'
if old_css not in text:
    raise SystemExit("CSS atual do cabeçalho não encontrado; nenhuma alteração foi feita.")
text = text.replace(old_css, new_css, 1)

old_logo = '      .setta-brand-logo {{ justify-self:center !important; align-self:center !important;}}'
new_logo = '      .setta-brand-logo {{ width:100%; display:flex; align-items:center; justify-content:center; }}'
if old_logo not in text:
    raise SystemExit("CSS atual da logo não encontrado; nenhuma alteração foi feita.")
text = text.replace(old_logo, new_logo, 1)

old_header = '    st.markdown(f\'<div class="setta-brand">{logo_html}<div class="setta-brand-center"><div class="setta-brand-title">{title}</div><div class="setta-brand-objective">{objective}</div></div><div></div></div>\', unsafe_allow_html=True)'
new_header = '    st.markdown(f\'<div class="setta-brand">{logo_html}</div>\', unsafe_allow_html=True)'
if old_header not in text:
    raise SystemExit("HTML atual do cabeçalho não encontrado; nenhuma alteração foi feita.")
text = text.replace(old_header, new_header, 1)

path.write_text(text, encoding="utf-8")
print("Cabeçalho corrigido: balão restaurado, logo centralizada e título removido do balão.")