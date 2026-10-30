"""Proteção contra desaparecimento silencioso de descrições na Compra MRP.

A descrição pertence à fotografia de origem: CADASTROS (ADMIN) ou MRP Geral
da mesma fotografia salva (CONSULTA). Nunca dependa de dados em processamento.
"""
from __future__ import annotations
import re
import pandas as pd

def codigo_canonico(value):
    raw=str(value).strip()
    if not raw or raw.lower() in {"nan","none","nat"}:
        return ""
    if re.fullmatch(r"\d+(?:\.0+)?",raw):
        raw=raw.split(".")[0]
    return raw.zfill(8) if raw.isdigit() and len(raw)<=8 else raw

def descricoes_por_codigo(frame:pd.DataFrame|None)->dict[str,str]:
    if frame is None or frame.empty or not {"Código","Descrição"}.issubset(frame.columns):
        return {}
    lookup={}
    for codigo,descricao in zip(frame["Código"],frame["Descrição"]):
        key=codigo_canonico(codigo)
        if pd.isna(descricao):
            continue
        value=str(descricao).strip()
        if key and value and value.lower() not in {"nan","none","null"}:
            lookup.setdefault(key,value)
    return lookup

def preencher_descricoes_compra(compra:pd.DataFrame, fonte:pd.DataFrame|None):
    """Mantém todas as linhas; nunca substitui informação ausente por string vazia."""
    out=compra.copy()
    if "produto" not in out.columns:
        raise ValueError("Compra MRP sem coluna de código do produto.")
    lookup=descricoes_por_codigo(fonte)
    descricoes=out["produto"].map(lambda c:lookup.get(codigo_canonico(c)))
    sem=out.loc[descricoes.isna(),"produto"].map(codigo_canonico).unique().tolist()
    # Exibir estado verificável, não célula aparentemente em branco.
    out["Descrição"]=descricoes.fillna("DESCRIÇÃO NÃO LOCALIZADA — CONFERIR CADASTRO")
    return out,sem
