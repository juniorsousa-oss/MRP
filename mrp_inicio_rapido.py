"""Decisão de atualização e cálculo em segundo plano, sem ações de interface."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from threading import Lock

from mrp_integridade_compra import descricoes_por_codigo

SNAPSHOT_FORMAT = b"MRP-SNAPSHOT-V9-COMPRA-TCTP-GRUPO-OP-OBS"


def daily_key(refs, projects, products, day):
    def observations(frame, cols):
        return json.dumps(
            frame[[*cols, "OBS"]].sort_values(list(cols)).to_dict("records"),
            ensure_ascii=False, sort_keys=True,
        ).encode("utf-8")
    digest = sha256(SNAPSHOT_FORMAT + b"".join(f.getvalue() for f in refs)
                    + observations(projects, ("Projeto",))
                    + observations(products, ("Projeto", "Produto"))).hexdigest()
    return sha256(f"MRP-DIARIO|{day}|{digest}".encode("utf-8")).hexdigest()


def snapshot_is_usable(snapshot):
    return (isinstance(snapshot, dict) and bool(snapshot.get("id"))
            and bool(snapshot.get("mrp_geral")) and bool(snapshot.get("demanda_projeto")))


def update_needed(state, snapshot_key, candidate_key):
    return bool(state.get("ready") and candidate_key
                and (state.get("output_stale") or snapshot_key != candidate_key))


def calculate_validated(load_bundle, prepare, expected_signature, projects, products):
    # Imports do motor não atravessam a abertura normal da tela.
    from mrp_engine_headless import calcular_mrp
    bundle = load_bundle()
    if not bundle.get("ready") or bundle.get("signature") != expected_signature:
        raise ValueError("As bases mudaram durante a preparação.")
    sources = prepare(bundle, expected_signature)
    result, week = calcular_mrp(*sources, projects, products, incluir_semana=True)
    macro, demanda = result["macro"], result["demanda_projeto"]
    descriptions = descricoes_por_codigo(macro).keys() | descricoes_por_codigo(sources[0]).keys()
    codes = set(result["compras_mrp"]["produto"].map(str).str.zfill(8)) if len(result["compras_mrp"]) else set()
    if macro.empty or demanda.empty or codes - descriptions:
        raise ValueError("Resultado vazio ou descrição obrigatória ausente.")
    return result, week


class SingleCalculation:
    """Um trabalho por processo, compartilhado por sessões Admin do mesmo app."""
    def __init__(self):
        self._lock = Lock()
        self.publish_lock = Lock()
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mrp-calculo")
        self._active = None

    def request(self, key, task):
        with self._lock:
            if self._active:
                existing_key, future = self._active
                if existing_key == key:
                    return future
                if not future.done():
                    return None
            future = self._pool.submit(task)
            self._active = key, future
            return future

    def discard(self, key):
        with self._lock:
            if self._active and self._active[0] == key and self._active[1].done():
                self._active = None
