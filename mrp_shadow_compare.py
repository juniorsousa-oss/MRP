"""Comparação determinística e SEM GRAVAÇÃO entre MRP calculado e histórico oficial.

O histórico pode ser um registro mrp_snapshots já devolvido pelo Supabase,
inclusive contendo compressed_payload. Nenhum dado é transmitido daqui.
Detecta registros duplicados, ausentes e diferenças de colunas/valores.
"""
from __future__ import annotations

import base64
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import gzip
import io
import json
from numbers import Number
from typing import Any

import pandas as pd


CAMPOS = {
    "macro": "mrp_geral",
    "proj": "projecao_semanal",
    "demanda_projeto": "demanda_projeto",
    "compras_mrp": "compra_mrp",
    "cp": "compras",
    "fab_det": "fabricacao",
}
LIMITE_DESCOMPACTADO = 80_000_000


def _valor(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return "" if pd.isna(value) else value.isoformat()
    try:
        if bool(pd.isna(value)):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, Number) and not isinstance(value, bool):
        try:
            return str(Decimal(str(value)).quantize(Decimal("0.000001")).normalize())
        except InvalidOperation:
            return str(value)
    return str(value).strip()


def _contador(frame: pd.DataFrame, colunas: list[str]) -> Counter:
    return Counter(
        tuple(_valor(x) for x in row)
        for row in frame[colunas].itertuples(index=False, name=None)
    )


def comparar_tabela(
    oficial: pd.DataFrame,
    autonomo: pd.DataFrame,
    *,
    amostras: int = 3,
) -> dict[str, Any]:
    colunas_oficial = {str(c) for c in oficial.columns}
    colunas_autonomo = {str(c) for c in autonomo.columns}
    if any(not isinstance(c, str) for c in oficial.columns) or any(
        not isinstance(c, str) for c in autonomo.columns
    ):
        raise ValueError("Colunas precisam ter nomes textuais únicos.")
    if len(colunas_oficial) != len(oficial.columns) or len(colunas_autonomo) != len(autonomo.columns):
        raise ValueError("Colunas duplicadas impedem uma comparação confiável.")
    comuns = sorted(colunas_oficial & colunas_autonomo)
    antigo = _contador(oficial, comuns)
    novo = _contador(autonomo, comuns)
    removidas = antigo - novo
    adicionadas = novo - antigo
    iguais = (
        colunas_oficial == colunas_autonomo
        and not removidas
        and not adicionadas
    )
    return {
        "identico": iguais,
        "linhas_oficiais": len(oficial),
        "linhas_motor": len(autonomo),
        "colunas_apenas_oficial": sorted(colunas_oficial - colunas_autonomo),
        "colunas_apenas_motor": sorted(colunas_autonomo - colunas_oficial),
        "linhas_ausentes": sum(removidas.values()),
        "linhas_adicionais": sum(adicionadas.values()),
        "amostra_ausentes": [
            dict(zip(comuns, row)) for row in list(removidas.elements())[:amostras]
        ],
        "amostra_adicionais": [
            dict(zip(comuns, row)) for row in list(adicionadas.elements())[:amostras]
        ],
    }


def abrir_snapshot(registro: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(registro, dict):
        raise TypeError("O histórico deve ser um registro JSON.")
    result = dict(registro)
    packed = result.get("compressed_payload")
    if packed:
        if not isinstance(packed, str) or len(packed) > 30_000_000:
            raise ValueError("Histórico compactado inválido ou excessivo.")
        compressed = base64.b64decode(packed, validate=True)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as f:
            raw = f.read(LIMITE_DESCOMPACTADO + 1)
        if len(raw) > LIMITE_DESCOMPACTADO:
            raise ValueError("Histórico descompactado excede o limite de segurança.")
        sections = json.loads(raw)
        if not isinstance(sections, dict):
            raise ValueError("Seções do histórico inválidas.")
        result.update(sections)
    missing = [name for name in CAMPOS.values() if not isinstance(result.get(name), list)]
    if missing:
        raise ValueError(f"Histórico não possui todas as seções: {missing}")
    return result


def confrontar_mrp(
    calculado: dict[str, pd.DataFrame],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    historico = abrir_snapshot(snapshot)
    detalhe = {
        campo: comparar_tabela(
            pd.DataFrame(historico[armazenado]),
            calculado[campo],
        )
        for campo, armazenado in CAMPOS.items()
    }
    return {
        "todos_iguais": all(x["identico"] for x in detalhe.values()),
        "snapshot_id": historico.get("id"),
        "semana_mrp": historico.get("semana_mrp"),
        "resultado": detalhe,
    }
