from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
start = s.index('def _require_login(login_cfg):')
end = s.index('\nPUBLIC_LOGIN_CONFIG = _public_login_config()', start)
block = s[start:end]
bs = block.index('    <style>')
be = block.index('    </style>', bs) + len('    </style>')

new_css = '''    <style>
      .stApp {{ background:#ffffff !important; color:{text} !important; }}
      [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"] {{ display:none !important; }}
      .block-container {{ max-width:100% !important; min-height:100vh !important; height:100vh !important; padding:0 !important; margin:0 !important; position:relative !important; overflow:hidden !important; }}
      .setta-login-wrap {{
        position:fixed !important; left:50% !important; top:50% !important; transform:translate(-50%,-50%) !important;
        width:286px !important; height:418px !important; margin:0 !important; padding:0 !important;
        box-sizing:border-box !important; background:#fff !important; border:1px solid rgba(0,0,0,.13) !important;
        border-radius:28px !important; box-shadow:0 16px 42px rgba(0,0,0,.16) !important;
        overflow:hidden !important; z-index:10 !important;
      }}
      .setta-login-image {{
        width:100% !important; height:145px !important; overflow:hidden !important; background:transparent !important;
        display:flex !important; align-items:flex-end !important; justify-content:center !important;
        padding:20px 18px 8px !important; box-sizing:border-box !important;
      }}
      .setta-login-image img {{
        width:auto !important; height:auto !important; max-width:175px !important; max-height:82px !important;
        object-fit:contain !important; object-position:center !important; display:block !important;
      }}
      .setta-login-image-empty {{ display:flex !important; flex-direction:column !important; align-items:center !important; justify-content:center !important; }}
      .setta-login-image-empty div {{ font-size:3.4rem !important; font-weight:800 !important; font-style:italic !important; line-height:1 !important; color:#111 !important; }}
      .setta-login-heading {{ text-align:center !important; padding:0 22px !important; height:62px !important; box-sizing:border-box !important; }}
      .setta-login-title {{ color:#111 !important; font-size:14px !important; line-height:17px !important; font-weight:800 !important; margin:0 !important; }}
      .setta-login-subtitle {{ color:#777 !important; opacity:1 !important; font-size:6.5px !important; line-height:9px !important; margin:7px auto 0 !important; max-width:205px !important; }}
      .setta-login-form-note {{ display:none !important; }}
      div[data-testid="stForm"] {{
        position:fixed !important; left:50% !important; top:calc(50% + 2px) !important; transform:translateX(-50%) !important;
        width:286px !important; height:175px !important; margin:0 !important; padding:0 22px 18px !important;
        box-sizing:border-box !important; background:transparent !important; border:0 !important;
        border-radius:0 !important; box-shadow:none !important; z-index:20 !important;
      }}
      div[data-testid="stForm"] label {{ color:#202020 !important; font-size:9px !important; line-height:12px !important; font-weight:600 !important; margin-bottom:2px !important; }}
      div[data-testid="stForm"] [data-testid="stTextInput"] {{ margin-bottom:7px !important; }}
      div[data-testid="stForm"] input {{
        height:29px !important; min-height:29px !important; box-sizing:border-box !important; padding:0 10px !important;
        border-radius:6px !important; border:1px solid #d8dde5 !important; background:#f0f2f6 !important;
        color:#202020 !important; font-size:8px !important;
      }}
      div[data-testid="stForm"] input::placeholder {{ color:#a6adb8 !important; opacity:1 !important; }}
      div[data-testid="stForm"] input:focus {{ border-color:#b8bec8 !important; box-shadow:none !important; }}
      div[data-testid="stForm"] button {{
        height:29px !important; min-height:29px !important; margin-top:3px !important; border-radius:7px !important;
        background:#050505 !important; border:1px solid #050505 !important; color:#fff !important;
        font-size:8px !important; font-weight:700 !important;
      }}
      div[data-testid="stForm"] button:hover {{ background:#171717 !important; border-color:#171717 !important; }}
      @media (max-width:480px) {{
        .setta-login-wrap, div[data-testid="stForm"] {{ width:286px !important; }}
      }}
    </style>'''

block = block[:bs] + new_css + block[be:]
s = s[:start] + block + s[end:]
p.write_text(s, encoding='utf-8')
print('Posicionamento do login corrigido.')
