from pathlib import Path
from mrp_runtime_patch import patch_runtime_source

_runtime_path = Path(__file__).with_name("app_mrp_runtime.py")
_runtime_source = _runtime_path.read_text(encoding="utf-8")
_runtime_source = patch_runtime_source(_runtime_source)

exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())
