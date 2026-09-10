from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')
old='''      .setta-login-subtitle {{ color:#777 !important; opacity:1 !important; font-size:6.5px !important; line-height:9px !important; margin:7px auto 0 !important; max-width:205px !important; }}
      .setta-login-form-note {{ display:none !important; }}'''
new='''      .setta-login-subtitle {{ display:none !important; }}
      .setta-login-form-note {{ display:none !important; }}
      div[data-testid="InputInstructions"],
      div[data-testid="stTextInput"] div[data-testid="InputInstructions"] {{ display:none !important; }}'''
if old not in s: raise SystemExit('Bloco de subtitulo não encontrado')
s=s.replace(old,new,1)
old='''      div[data-testid="stForm"] input {{
        height:29px !important; min-height:29px !important; box-sizing:border-box !important; padding:0 10px !important;
        border-radius:6px !important; border:1px solid #d8dde5 !important; background:#f0f2f6 !important;
        color:#202020 !important; font-size:8px !important;
      }}'''
new='''      div[data-testid="stForm"] input {{
        height:29px !important; min-height:29px !important; box-sizing:border-box !important; padding:0 10px !important;
        border-radius:6px !important; border:2px solid #050505 !important; background:#f0f2f6 !important;
        color:#202020 !important; font-size:8px !important;
      }}
      div[data-testid="stForm"] [data-baseweb="input"] {{
        border:2px solid #050505 !important; border-radius:8px !important; box-shadow:none !important;
      }}'''
if old not in s: raise SystemExit('Bloco dos inputs não encontrado')
s=s.replace(old,new,1)
old='''      <div class="setta-login-heading">
        <div class="setta-login-title">{app_title}</div>
        <div class="setta-login-subtitle">{objective}</div>
      </div>'''
new='''      <div class="setta-login-heading">
        <div class="setta-login-title">{app_title}</div>
      </div>'''
if old not in s: raise SystemExit('HTML do cabecalho de login não encontrado')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Patch aplicado com sucesso.')
