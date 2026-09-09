from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
needle = '''      div[data-testid="stForm"] [data-testid="stTextInput"]:first-of-type input {
        height:40px !important; min-height:40px !important;
      }'''
replacement = needle + '''
      div[data-testid="stForm"] [data-testid="stTextInput"]:first-of-type {
        transform:translateY(40px) !important;
      }'''
if needle not in s:
    raise SystemExit('Regra do campo Usuario nao encontrada.')
if 'first-of-type {\n        transform:translateY(40px)' in s:
    raise SystemExit('Campo Usuario ja esta deslocado 40px para baixo.')
p.write_text(s.replace(needle, replacement, 1), encoding='utf-8')
print('Somente o campo Usuario foi deslocado 40px para baixo.')
