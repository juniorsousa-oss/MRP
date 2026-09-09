from pathlib import Path
p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
if 'import re\n' not in s:
    s = s.replace('import hashlib\n', 'import hashlib\nimport re\n', 1)
p.write_text(s, encoding='utf-8')
print('visual import fixed')
