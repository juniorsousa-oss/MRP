from __future__ import annotations

import base64
import gzip
import io
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd
import requests
import streamlit as st
from supabase import create_client

DEFAULT_SUPABASE_URL = "https://cuixazpxkvniqldmmnth.supabase.co"
DEFAULT_SUPABASE_ANON_KEY = (
    os.getenv("SETTA_SUPABASE_ANON_KEY", "").strip()
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1aXhhenB4a3ZuaXFsZG1tbnRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1MTYwNTMsImV4cCI6MjEwMzA5MjA1M30.jNFaIG1FcDYnMAoVaI23UYMuRL1BpZmuqu_LPEYb88E"
)
BUCKET = "setta-data"
TZ = ZoneInfo("America/Sao_Paulo")

DERIVED_INPUTS = [
    "relatorio_geral_tratado",
    "estoque_tratado",
    "compras_tratado",
    "tctp_tratado",
]

# Mesmas dependências usadas pelo Conversor MRP para decidir se uma base
# tratada precisa ser reprocessada.
DERIVED_SOURCE_DEPENDENCIES = {
    "relatorio_geral_tratado": ("relatorio_geral", "for001", "for022"),
    "estoque_tratado": ("analitico", "endereco"),
    "compras_tratado": ("sc", "pc", "pre_nota"),
    "tctp_tratado": ("pmp", "h001"),
}
RAW_INPUTS = tuple(
    sorted(
        {
            source_key
            for dependencies in DERIVED_SOURCE_DEPENDENCIES.values()
            for source_key in dependencies
        }
    )
)

SESSION = requests.Session()
SESSION.headers.update({"Connection": "keep-alive"})


def _secret(*names: str) -> str:
    values: list[Any] = []
    try:
        for name in names:
            values.append(st.secrets.get(name))
    except Exception:
        pass
    for name in names:
        values.append(os.getenv(name))
    return next((str(value).strip() for value in values if value), "")


def supabase_url() -> str:
    return _secret("SUPABASE_URL") or DEFAULT_SUPABASE_URL


def supabase_key() -> str:
    return (
        _secret("SUPABASE_ANON_KEY", "SUPABASE_KEY", "SUPABASE_PUBLISHABLE_KEY")
        or DEFAULT_SUPABASE_ANON_KEY
    )


def api_url() -> str:
    return f"{supabase_url().rstrip('/')}/functions/v1/setta-data-api"


def _headers() -> dict[str, str]:
    key = supabase_key()
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": "application/json",
    }


def api_call(action: str, payload: dict | None = None, timeout: int = 60) -> dict:
    response = SESSION.post(
        api_url(),
        headers=_headers(),
        json={"action": action, "payload": payload or {}},
        timeout=timeout,
    )
    try:
        data = response.json()
    except Exception:
        data = {"ok": False, "error": response.text or f"HTTP {response.status_code}"}
    if not response.ok or not data.get("ok"):
        raise RuntimeError(data.get("error") or f"HTTP {response.status_code}")
    return data


@st.cache_data(show_spinner=False, ttl=15, max_entries=8)
def _bundle_state_cached(
    source_keys: tuple[str, ...],
    derived_keys: tuple[str, ...],
) -> tuple[dict[str, dict], dict[str, dict]]:
    payload = api_call(
        "bundle_state",
        {
            "source_keys": list(source_keys),
            "derived_keys": list(derived_keys),
        },
        timeout=30,
    ).get("data") or {}

    source_rows = payload.get("sources") or []
    derived_rows = payload.get("derived") or []

    sources = {
        str(row.get("source_key")): row
        for row in source_rows
        if isinstance(row, dict)
    }
    derived = {
        str(row.get("base_key")): row
        for row in derived_rows
        if isinstance(row, dict)
    }
    return sources, derived


def clear_state_cache() -> None:
    _bundle_state_cached.clear()


@st.cache_data(show_spinner=False, ttl=60, max_entries=2)
def load_visual_config() -> dict:
    row = api_call(
        "visual_get",
        {"app_key": "setta_global"},
        timeout=30,
    ).get("data") or {}
    return {
        "logo_data": row.get("logo_data") or "",
        "logo_mime": row.get("logo_mime") or "image/png",
        "favicon_data": row.get("favicon_data") or "",
        "favicon_mime": row.get("favicon_mime") or "image/png",
    }


def format_dt(value: Any) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


def logo_data_uri(config: dict | None = None) -> str:
    cfg = config or load_visual_config()
    data = str(cfg.get("logo_data") or "").strip()
    if not data:
        return ""
    mime = str(cfg.get("logo_mime") or "image/png")
    return f"data:{mime};base64,{data}"


def favicon_bytes(config: dict | None = None) -> bytes:
    cfg = config or load_visual_config()
    data = str(cfg.get("favicon_data") or "").strip()
    if not data:
        return b""
    try:
        return base64.b64decode(data, validate=True)
    except Exception:
        return b""


@st.cache_data(show_spinner=False, ttl=3600, max_entries=8)
def _download_source_cached(
    source_key: str,
    version: int,
    updated_at: str,
) -> bytes:
    del version, updated_at
    meta = api_call("source_download", {"source_key": source_key}, timeout=30).get("data") or {}
    signed_url = str(meta.get("signed_url") or "")
    if not signed_url:
        raise RuntimeError(f"Fonte {source_key} sem URL de leitura.")
    response = SESSION.get(signed_url, timeout=120)
    response.raise_for_status()
    return response.content


@st.cache_data(show_spinner=False, ttl=3600, max_entries=8)
def _download_cadastros_frame_cached(
    version: int,
    updated_at: str,
) -> pd.DataFrame:
    """Consome CADASTROS normalizado; Excel fica apenas como contingência legada."""
    try:
        meta = api_call(
            "source_normalized_download",
            {"source_key": "cadastros"},
            timeout=30,
        ).get("data") or {}
        signed_url = str(meta.get("signed_url") or "")
        if not signed_url:
            raise RuntimeError("CADASTROS normalizado sem URL.")
        response = SESSION.get(signed_url, timeout=120)
        response.raise_for_status()
        pack = json.loads(
            gzip.decompress(response.content).decode("utf-8")
        )
        if str(pack.get("format") or "") != "SETTA_SOURCE_V1":
            raise RuntimeError("Formato normalizado do CADASTROS inválido.")
        sheets = [
            item for item in (pack.get("sheets") or [])
            if isinstance(item, dict)
        ]
        if not sheets:
            raise RuntimeError("CADASTROS normalizado sem planilha.")
        raw = pd.DataFrame(sheets[0].get("rows") or [])
        if len(raw) < 2:
            return pd.DataFrame()
        headers = []
        used: dict[str, int] = {}
        for idx, value in enumerate(raw.iloc[1].tolist()):
            base = (
                f"Unnamed: {idx}"
                if value is None or str(value).strip() == ""
                else str(value)
            )
            count = used.get(base, 0)
            used[base] = count + 1
            headers.append(base if count == 0 else f"{base}.{count}")
        frame = raw.iloc[2:].reset_index(drop=True).copy()
        frame.columns = headers
        return frame
    except Exception:
        raw = _download_source_cached(
            "cadastros",
            version,
            updated_at,
        )
        return pd.read_excel(
            io.BytesIO(raw),
            sheet_name=0,
            header=1,
        )


@st.cache_data(show_spinner=False, ttl=3600, max_entries=16)
def _download_derived_cached(
    base_key: str,
    processed_at: str,
    source_versions_token: str,
) -> pd.DataFrame:
    del processed_at, source_versions_token
    meta = api_call("derived_download", {"base_key": base_key}, timeout=30).get("data") or {}
    signed_url = str(meta.get("signed_url") or "")
    if not signed_url:
        raise RuntimeError(f"Base {base_key} sem URL de leitura.")
    response = SESSION.get(signed_url, timeout=120)
    response.raise_for_status()
    raw = gzip.decompress(response.content)
    return pd.read_json(io.BytesIO(raw), orient="table")


def _derived_token(meta: dict) -> str:
    return json.dumps(
        meta.get("source_versions") or {},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )


def _int_version(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def derived_freshness(
    sources: dict[str, dict],
    derived: dict[str, dict],
) -> dict[str, dict]:
    """Compara versões atuais das fontes com as versões usadas nas bases tratadas."""
    stale: dict[str, dict] = {}
    for base_key, dependencies in DERIVED_SOURCE_DEPENDENCIES.items():
        meta = derived.get(base_key) or {}
        registered = {
            str(key): _int_version(value)
            for key, value in (meta.get("source_versions") or {}).items()
        }

        differences = []
        for source_key in dependencies:
            source_meta = sources.get(source_key) or {}
            current_version = _int_version(source_meta.get("version"))
            base_version = _int_version(registered.get(source_key))
            if not bool(source_meta.get("available")):
                differences.append(
                    {
                        "source_key": source_key,
                        "current_version": current_version,
                        "base_version": base_version,
                        "reason": "FONTE INDISPONÍVEL",
                    }
                )
            elif current_version != base_version:
                differences.append(
                    {
                        "source_key": source_key,
                        "current_version": current_version,
                        "base_version": base_version,
                        "reason": "VERSÃO DIVERGENTE",
                    }
                )

        if not bool(meta.get("available")):
            stale[base_key] = {
                "reason": "BASE INDISPONÍVEL",
                "differences": differences,
            }
        elif differences:
            stale[base_key] = {
                "reason": "BASE DESATUALIZADA",
                "differences": differences,
            }
    return stale


def _normalized_versions(value: dict | None) -> dict[str, str]:
    return {
        str(key): str(val)
        for key, val in (value or {}).items()
    }


def dependency_versions(
    cadastro_meta: dict,
    derived_meta: dict[str, dict],
) -> dict[str, str]:
    result = {
        "cadastros": f"v{int(cadastro_meta.get('version') or 0)}",
    }
    for key in DERIVED_INPUTS:
        meta = derived_meta.get(key) or {}
        result[key] = str(meta.get("processed_at") or "")
    return result


def dependency_signature(versions: dict[str, str]) -> str:
    return json.dumps(
        versions,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def load_mrp_bundle(force_check: bool = False) -> dict:
    # Na primeira abertura da sessão, ignora qualquer estado em cache e consulta
    # a Central imediatamente, reproduzindo a checagem de versões do Conversor.
    if force_check:
        clear_state_cache()

    sources, derived = _bundle_state_cached(
        tuple(["cadastros", *RAW_INPUTS]),
        tuple(DERIVED_INPUTS + ["relatorio_mrp"]),
    )

    cadastro_meta = sources.get("cadastros") or {
        "source_key": "cadastros",
        "available": False,
    }
    input_meta = {
        key: derived.get(key) or {"base_key": key, "available": False}
        for key in DERIVED_INPUTS
    }
    output_meta = derived.get("relatorio_mrp") or {
        "base_key": "relatorio_mrp",
        "available": False,
    }

    stale_inputs = derived_freshness(sources, input_meta)
    ready = (
        bool(cadastro_meta.get("available"))
        and all(bool(input_meta[key].get("available")) for key in DERIVED_INPUTS)
        and not stale_inputs
    )
    versions = dependency_versions(cadastro_meta, input_meta)
    signature = dependency_signature(versions)

    output_stale = (
        not bool(output_meta.get("available"))
        or _normalized_versions(output_meta.get("source_versions"))
        != _normalized_versions(versions)
    )

    bundle = {
        "ready": ready,
        "cadastro_meta": cadastro_meta,
        "source_meta": {
            key: sources.get(key) or {"source_key": key, "available": False}
            for key in RAW_INPUTS
        },
        "derived_meta": input_meta,
        "output_meta": output_meta,
        "stale_inputs": stale_inputs,
        "output_stale": output_stale,
        "dependency_versions": versions,
        "signature": signature,
    }
    if not ready:
        return bundle

    tasks: dict[Any, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks[
            executor.submit(
                _download_cadastros_frame_cached,
                int(cadastro_meta.get("version") or 0),
                str(cadastro_meta.get("last_update_at") or ""),
            )
        ] = ("source", "cadastros")

        for key in DERIVED_INPUTS:
            meta = input_meta[key]
            tasks[
                executor.submit(
                    _download_derived_cached,
                    key,
                    str(meta.get("processed_at") or ""),
                    _derived_token(meta),
                )
            ] = ("derived", key)

        for future in as_completed(tasks):
            kind, key = tasks[future]
            value = future.result()
            if kind == "source":
                bundle["cadastros_frame"] = value
            else:
                bundle[key] = value

    return bundle


class CentralRef:
    def __init__(self, label: str, signature: str):
        self.name = label
        self._payload = f"{label}|{signature}".encode("utf-8")

    def getvalue(self) -> bytes:
        return self._payload

    def __bool__(self) -> bool:
        return True


def make_refs(bundle: dict) -> tuple[CentralRef, CentralRef, CentralRef, CentralRef, CentralRef]:
    sig = str(bundle.get("signature") or "")
    return (
        CentralRef("CADASTROS", sig),
        CentralRef("ESTOQUE_TRATADO", sig),
        CentralRef("RELATORIO_GERAL_TRATADO", sig),
        CentralRef("COMPRAS_TRATADO", sig),
        CentralRef("TCTP_TRATADO", sig),
    )


def _payload(frame: pd.DataFrame) -> bytes:
    text = frame.to_json(
        orient="table",
        date_format="iso",
        force_ascii=False,
        index=False,
    )
    return gzip.compress(text.encode("utf-8"), compresslevel=6)


def publish_relatorio_mrp_if_changed(
    frame: pd.DataFrame,
    versions: dict[str, str],
    current_meta: dict | None = None,
) -> dict:
    current = current_meta or {}
    if (
        bool(current.get("available"))
        and _normalized_versions(current.get("source_versions"))
        == _normalized_versions(versions)
    ):
        return {"changed": False, "meta": current}

    raw = _payload(frame)
    prepared = api_call(
        "derived_upload_prepare",
        {"base_key": "relatorio_mrp"},
        timeout=30,
    )
    path = str(prepared.get("path") or "")
    token = str(prepared.get("token") or "")
    if not path or not token:
        raise RuntimeError("A Central não retornou autorização para publicar o Relatório MRP.")

    client = create_client(supabase_url(), supabase_key())
    client.storage.from_(BUCKET).upload_to_signed_url(
        path=path,
        token=token,
        file=raw,
    )

    meta = api_call(
        "derived_commit",
        {
            "base_key": "relatorio_mrp",
            "rows_count": int(len(frame)),
            "source_versions": versions,
        },
        timeout=30,
    ).get("data") or {}
    return {"changed": True, "meta": meta}
