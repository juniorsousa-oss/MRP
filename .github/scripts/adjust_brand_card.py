from pathlib import Path

path = Path("app_mrp.py")
text = path.read_text(encoding="utf-8")
old = '''      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height: 130px; display: grid; grid-template-columns: 1fr 2.2fr 1fr; align-items: center; gap: 12px; }}
      .setta-brand-logo {{ grid-column: 1; justify-self: start; align-self: center; }}
      .setta-brand-logo img {{ display: block; max-width: 100%; height: auto; margin: 0; }}
      .setta-brand-center {{ grid-column: 2; text-align: center; }}'''
new = '''      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height: 130px; display: flex; align-items: center; justify-content: center; }}
      .setta-brand-logo {{ width: 100%; display: flex; align-items: center; justify-content: center; }}
      .setta-brand-logo img {{ display: block; max-width: 100%; height: auto; margin: 0 auto; }}
      .setta-brand-center {{ display: none !important; }}'''
if old not in text:
    raise SystemExit("CSS do cabeçalho da marca não encontrado; nenhuma alteração foi feita.")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Cabeçalho corrigido: textos removidos do cartão e logo centralizada.")
