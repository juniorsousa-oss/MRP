from pathlib import Path
import re

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')

# Remove o titulo central do cabecalho principal, preservando a classe para compatibilidade visual.
s = re.sub(
    r'(?P<open><div class="setta-brand-center"[^>]*>)\s*<div class="setta-brand-title">.*?</div>\s*</div>',
    r'\g<open></div>',
    s,
    count=1,
    flags=re.S,
)

# Faz a area do cabecalho trabalhar com uma unica coluna e centraliza a logo.
s = re.sub(
    r'(\.setta-brand\s*\{.*?)(grid-template-columns\s*:\s*[^;]+;)',
    r'\1grid-template-columns: 1fr;',
    s,
    count=1,
    flags=re.S,
)

# Reforca centralizacao da logo sem alterar tamanho definido pelo usuario.
s = re.sub(
    r'(\.setta-brand-logo\s*\{)(.*?)(\})',
    lambda m: m.group(1) + re.sub(r'justify-content\s*:\s*[^;]+;', 'justify-content:center;', re.sub(r'justify-self\s*:\s*[^;]+;', 'justify-self:center;', m.group(2))) + m.group(3),
    s,
    count=1,
    flags=re.S,
)

p.write_text(s, encoding='utf-8')
print('Cabecalho ajustado: titulo central removido e logo centralizada.')
