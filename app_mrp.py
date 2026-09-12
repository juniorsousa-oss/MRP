from pathlib import Path
import re

# Mantém o aplicativo original intacto e aplica apenas otimizações de leitura
# antes de executá-lo. O objetivo é reduzir o egress do Supabase sem alterar
# regras, telas ou cálculos do MRP.
_original = Path(__file__).with_name("app_mrp_original.py")
_source = _original.read_text(encoding="utf-8")

# 1) Configuração pública do login muda raramente: evita buscar imagem/config
# novamente a cada rerun do Streamlit.
_source = _source.replace(
    "def _public_login_config():\n",
    "@st.cache_data(ttl=1800, show_spinner=False)\ndef _public_login_config():\n",
    1,
)

# 2) Snapshots: consulta frequente somente os metadados (poucos bytes).
# O JSON completo (~5 MB por snapshot) só é baixado quando o ID muda e fica
# cacheado por 1 hora. Ao salvar novo snapshot, os caches são invalidados.
_pattern = re.compile(
    r"def load_latest_snapshot\(\):\n"
    r".*?"
    r"def save_snapshot\(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None\):\n"
    r".*?"
    r"    return _sb_post\(payload\)",
    re.S,
)

_replacement = '''@st.cache_data(ttl=60, show_spinner=False)
def load_latest_snapshot_meta():
    rows=_sb_get({"select":"id,created_at,semana_mrp,usuario","order":"created_at.desc","limit":"1"})
    return rows[0] if rows else None

@st.cache_data(ttl=120, show_spinner=False)
def load_snapshot_history(limit=50):
    return _sb_get({"select":"id,created_at,semana_mrp,usuario","order":"created_at.desc","limit":str(limit)})

@st.cache_data(ttl=3600, show_spinner=False)
def load_snapshot(snapshot_id):
    rows=_sb_get({"select":"*","id":f"eq.{int(snapshot_id)}","limit":"1"})
    return rows[0] if rows else None

def load_latest_snapshot():
    meta=load_latest_snapshot_meta()
    if not meta:
        return None
    return load_snapshot(meta["id"])

def save_snapshot(semana,usuario,mrp_geral,projecao_semanal,demanda_projeto,compra_mrp,compras=None):
    def records(df):
        if df is None or df.empty: return []
        return json.loads(df.to_json(orient="records",force_ascii=False,date_format="iso"))
    payload={"semana_mrp":int(semana) if semana is not None else None,"usuario":usuario or "Não informado","mrp_geral":records(mrp_geral),"projecao_semanal":records(projecao_semanal),"demanda_projeto":records(demanda_projeto),"compra_mrp":records(compra_mrp),"compras":records(compras)}
    result=_sb_post(payload)
    load_latest_snapshot_meta.clear()
    load_snapshot_history.clear()
    load_snapshot.clear()
    return result'''

_source, _count = _pattern.subn(_replacement, _source, count=1)
if _count != 1:
    raise RuntimeError("Bloco de snapshots do MRP não encontrado para otimização.")

exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())
