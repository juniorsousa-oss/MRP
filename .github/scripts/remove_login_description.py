from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
old = '''      .setta-login-heading {{ text-align:center !important; padding:0 20px !important; height:58px !important; transform:translateY(-30px) !important; box-sizing:border-box !important; }}\n      .setta-login-title {{ color:#111 !important; font-size:14px !important; line-height:17px !important; font-weight:800 !important; margin:0 !important; }}\n      .setta-login-subtitle {{ color:#777 !important; opacity:1 !important; font-size:6.5px !important; line-height:9px !important; margin:7px auto 0 !important; max-width:205px !important; }}'''
new = '''      .setta-login-heading {{ text-align:center !important; padding:0 20px !important; height:30px !important; transform:translateY(-30px) !important; box-sizing:border-box !important; }}\n      .setta-login-title {{ color:#111 !important; font-size:14px !important; line-height:17px !important; font-weight:800 !important; margin:0 !important; }}\n      .setta-login-subtitle {{ display:none !important; }}'''
if old not in s:
    raise SystemExit('Trecho visual do subtitulo nao encontrado; nenhuma alteracao aplicada.')
s = s.replace(old, new, 1)
old2 = '''      <div class="setta-login-heading">\n        <div class="setta-login-title">{app_title}</div>\n        <div class="setta-login-subtitle">{objective}</div>\n      </div>'''
new2 = '''      <div class="setta-login-heading">\n        <div class="setta-login-title">{app_title}</div>\n      </div>'''
if old2 not in s:
    raise SystemExit('Markup do cabecalho do login nao encontrado; nenhuma alteracao aplicada.')
s = s.replace(old2, new2, 1)
p.write_text(s, encoding='utf-8')
print('Descricao removida da tela de login; restante do login preservado.')
