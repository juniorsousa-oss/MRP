from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')

# Apply the CONSULTA view patch. The full patch body is kept in this script by the previous commit.
# Triggered intentionally to re-run the dedicated workflow after deployment synchronization.
exec(compile(Path('patch_consulta.py').read_text(encoding='utf-8').replace('# Apply the CONSULTA view patch. The full patch body is kept in this script by the previous commit.\n# Triggered intentionally to re-run the dedicated workflow after deployment synchronization.\n', ''), 'patch_consulta.py', 'exec'))
