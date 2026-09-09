from pathlib import Path

path = Path("app_mrp.py")
text = path.read_text(encoding="utf-8")
old_css = '''      .setta-login-image {{
        width:100% !important; height:135px !important; transform:translateY(-30px) !important; overflow:hidden !important; background:transparent !important;
        display:flex !important; align-items:flex-end !important; justify-content:center !important;
        padding:20px 18px 8px !important; box-sizing:border-box !important;
      }}'''
new_css = '''      .setta-login-image {{
        position:absolute !important; inset:0 !important; width:100% !important; height:100% !important;
        transform:none !important; overflow:hidden !important; background:transparent !important;
        display:flex !important; align-items:center !important; justify-content:center !important;
        padding:0 !important; box-sizing:border-box !important; z-index:11 !important;
      }}'''
if old_css not in text:
    raise SystemExit("CSS da logo não encontrado; nenhuma alteração foi feita.")
text = text.replace(old_css, new_css, 1)
old_html = '''    <div class="setta-login-wrap">
      {image_html}
      <div class="setta-login-heading">
        <div class="setta-login-title">{app_title}</div>
        <div class="setta-login-subtitle">{objective}</div>
      </div>
    </div>'''
new_html = '''    <div class="setta-login-wrap">
      {image_html}
    </div>'''
if old_html not in text:
    raise SystemExit("HTML do cabeçalho do login não encontrado; nenhuma alteração foi feita.")
text = text.replace(old_html, new_html, 1)
path.write_text(text, encoding="utf-8")
print("Layout do balão corrigido: somente logo centralizada; título e descrição removidos do balão.")
