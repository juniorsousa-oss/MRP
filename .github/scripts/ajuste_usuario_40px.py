from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
old = '''      div[data-testid="stForm"] input {\n        height:29px !important; min-height:29px !important; box-sizing:border-box !important; padding:0 10px !important;\n        border-radius:6px !important; border:1px solid #d8dde5 !important; background:#f0f2f6 !important;\n        color:#202020 !important; font-size:8px !important;\n      }'''
new = '''      div[data-testid="stForm"] input {\n        height:29px !important; min-height:29px !important; box-sizing:border-box !important; padding:0 10px !important;\n        border-radius:6px !important; border:1px solid #d8dde5 !important; background:#f0f2f6 !important;\n        color:#202020 !important; font-size:8px !important;\n      }\n      div[data-testid="stForm"] [data-testid="stTextInput"]:first-of-type input {\n        height:40px !important; min-height:40px !important;\n      }'''
if old not in s:
    raise SystemExit('Bloco alvo do input nao encontrado; nenhuma alteracao feita.')
if 'stTextInput"]:first-of-type input' in s:
    raise SystemExit('Regra de 40px ja existe; nenhuma alteracao feita.')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('Somente o campo Usuario foi definido para 40px.')
