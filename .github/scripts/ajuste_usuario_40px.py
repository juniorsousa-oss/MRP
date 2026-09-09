from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
old = '''      div[data-testid="stForm"] [data-testid="stTextInput"]:first-of-type input {
        height:40px !important; min-height:40px !important;
      }'''
new = '''      div[data-testid="stForm"] [data-testid="stTextInput"]:first-of-type input {
        height:40px !important; min-height:40px !important;
        transform:translateY(-40px) !important;
      }'''
if old not in s:
    raise SystemExit('Regra atual do campo Usuario nao encontrada; nenhuma alteracao feita.')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('Somente o campo Usuario foi deslocado 40px para cima, mantendo altura de 40px.')
