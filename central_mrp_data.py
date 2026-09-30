from __future__ import annotations

import gzip
import io
import json
import os
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

DERIVED_INPUTS = [
    "relatorio_geral_tratado",
    "estoque_tratado",
    "compras_tratado",
    "tctp_tratado",
]

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


def _source_status(keys: list[str]) -> dict[str, dict]:
    rows = api_call("source_status", {"keys": keys}, timeout=30).get("data") or []
    return {
        str(row.get("source_key")): row
        for row in rows
        if isinstance(row, dict)
    }


def _derived_status(keys: list[str]) -> dict[str, dict]:
    rows = api_call("derived_status", {"keys": keys}, timeout=30).get("data") or []
    return {
        str(row.get("base_key")): row
        for row in rows
        if isinstance(row, dict)
    }


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


def load_mrp_bundle() -> dict:
    sources = _source_status(["cadastros"])
    derived = _derived_status(DERIVED_INPUTS + ["relatorio_mrp"])

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

    ready = bool(cadastro_meta.get("available")) and all(
        bool(input_meta[key].get("available"))
        for key in DERIVED_INPUTS
    )
    versions = dependency_versions(cadastro_meta, input_meta)
    signature = dependency_signature(versions)

    bundle = {
        "ready": ready,
        "cadastro_meta": cadastro_meta,
        "derived_meta": input_meta,
        "output_meta": output_meta,
        "dependency_versions": versions,
        "signature": signature,
    }
    if not ready:
        return bundle

    tasks: dict[Any, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks[
            executor.submit(
                _download_source_cached,
                "cadastros",
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
                bundle["cadastros_bytes"] = value
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


def _normalized_versions(value: dict | None) -> dict[str, str]:
    return {
        str(key): str(val)
        for key, val in (value or {}).items()
    }


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
