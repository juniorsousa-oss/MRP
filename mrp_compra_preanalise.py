"""Relatorio de pre-analise da Compra MRP por OP.

Exportacao exclusivamente consultiva, ANTES da liberacao da carga Protheus.
Nao altera exclusoes, aprovacoes, snapshots ou quantidades de origem.
"""
from __future__ import annotations

from datetime import datetime
import re
from typing import Iterable, Mapping

import pandas as pd

CAMPOS = {"produto", "qnt", "data", "psy", "cc", "op", "obs", "prioridade"}
OP_NAO_INFORMADA = "SEM OP VINCULADA"


def _texto(valor) -> str:
    if valor is None or (not isinstance(valor, (list, dict)) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _excel_texto(valor) -> str:
    """Evita formula injection ao encaminhar planilhas para terceiros."""
    texto = _texto(valor)
    return "'" + texto if texto and texto[0] in ("=", "+", "-", "@", "\t", "\r") else texto


def op_relatorio(valor) -> str:
    """A OP ausente e identificada, nunca inventada."""
    value = _texto(valor)
    if re.fullmatch(r"\d+\.0+", value):
        value = value.split(".")[0]
    return value if value else OP_NAO_INFORMADA


def construir_relatorio_compra_por_op(
    compra: pd.DataFrame,
    descricoes: Mapping[str, str] | None = None,
    ops: Iterable[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Produz 4 abas com rastreabilidade, sem gerar carga de importacao.

    A 'compra' recebida e a PREVIA APROVAVEL ja filtrada pelas exclusoes.
    Nenhuma agregacao entre OPs; a quantidade por material e somada apenas
    dentro da mesma OP. Preserva linhas individuais e datas no detalhamento.
    """
    faltantes = CAMPOS.difference(compra.columns)
    if faltantes:
        raise ValueError("Pre-analise: colunas de compra ausentes: " + ", ".join(sorted(faltantes)))

    fonte = compra.copy(deep=True)
    fonte["OP"] = fonte["op"].map(op_relatorio)
    fonte["Código"] = fonte["produto"].map(_texto)
    fonte["Descrição"] = fonte["Código"].map(
        lambda c: _excel_texto((descricoes or {}).get(c, ""))
    )
    fonte["Quantidade"] = pd.to_numeric(fonte["qnt"], errors="coerce")
    if fonte["Quantidade"].isna().any() or (fonte["Quantidade"] < 0).any():
        raise ValueError("Pre-analise: quantidade ausente, negativa ou invalida.")
    filtro = {op_relatorio(x) for x in ops} if ops is not None else None
    if filtro is not None:
        fonte = fonte[fonte["OP"].isin(filtro)].copy()
    if fonte.empty:
        raise ValueError("Pre-analise: nenhuma linha de compra nas OPs selecionadas.")

    fonte["Data de necessidade"] = fonte["data"].map(_texto)
    fonte["Prioridade"] = fonte["prioridade"].map(_texto)
    fonte["PSY"] = fonte["psy"].map(_excel_texto)
    fonte["Centro de custo"] = fonte["cc"].map(_excel_texto)
    fonte["Observação MRP"] = fonte["obs"].map(_excel_texto)
    fonte["_data_ordem"] = pd.to_datetime(
        fonte["Data de necessidade"], format="%d/%m/%Y", errors="coerce"
    )
    fonte["_indice_origem"] = range(len(fonte))

    # Preservar as quantidades/OPs de cada linha de origem mesmo quando duas
    # demandas compartilham material e data.
    detalhado = fonte.sort_values(
        ["OP", "Código", "_data_ordem", "_indice_origem"], kind="stable"
    )[[
        "OP", "Código", "Descrição", "Quantidade", "Data de necessidade",
        "Prioridade", "PSY", "Centro de custo", "Observação MRP",
    ]].copy()
    detalhado["Parecer do analista"] = ""
    detalhado["Observações da análise"] = ""

    def _unicos(series: pd.Series) -> str:
        valores = list(dict.fromkeys(
            _texto(x) for x in series if _texto(x)
        ))
        return " | ".join(valores)

    por_material = (
        fonte.groupby(["OP", "Código", "Descrição"], sort=True, dropna=False)
        .agg(
            Quantidade=("Quantidade", "sum"),
            Linhas=("Código", "size"),
            Data_mais_proxima=("_data_ordem", "min"),
            Prioridade=("Prioridade", lambda s: "2" if (s == "2").any()
                        else ("1" if (s == "1").any() else _unicos(s))),
            PSY=("PSY", _unicos),
            Centro_de_custo=("Centro de custo", _unicos),
        )
        .reset_index()
        .rename(columns={
            "Linhas": "Linhas de demanda",
            "Data_mais_proxima": "Primeira necessidade",
            "Centro_de_custo": "Centro de custo",
        })
    )
    por_material["Primeira necessidade"] = por_material[
        "Primeira necessidade"
    ].dt.strftime("%d/%m/%Y").fillna("")
    por_material["Parecer do analista"] = ""
    por_material["Observações da análise"] = ""

    resumo = (
        fonte.groupby("OP", sort=True)
        .agg(
            Linhas_de_demanda=("Código", "size"),
            Materiais_distintos=("Código", "nunique"),
            Prioridades_emergenciais=("Prioridade", lambda s: int((s == "2").sum())),
            Primeira_necessidade=("_data_ordem", "min"),
        )
        .reset_index()
        .rename(columns={
            "Linhas_de_demanda": "Linhas de demanda",
            "Materiais_distintos": "Materiais distintos",
            "Prioridades_emergenciais": "Linhas emergenciais",
            "Primeira_necessidade": "Primeira necessidade",
        })
    )
    resumo["Primeira necessidade"] = resumo[
        "Primeira necessidade"
    ].dt.strftime("%d/%m/%Y").fillna("")
    resumo["Parecer do analista"] = ""
    resumo["Observações da análise"] = ""

    orientacoes = pd.DataFrame([
        ("TIPO", "RELATÓRIO DE PRÉ-ANÁLISE — NÃO É CARGA DO PROTHEUS"),
        ("FINALIDADE", "Revisão da proposta de compra por OP antes da aprovação definitiva."),
        ("SITUAÇÃO", "Documento de consulta; nenhum pedido, SC ou liberação é gerado pelo download."),
        ("ESCOPO", "Somente itens aptos na prévia de compra, após as exclusões vigentes."),
        ("CRITÉRIO", "Cada OP mantém seus materiais e respectivas quantidades; não mistura OPs."),
        ("DETALHAMENTO", "Aba DETALHE OP mantém cada linha e data da prévia."),
        ("CONSOLIDAÇÃO", "Aba MATERIAIS OP soma quantidades somente por OP e produto."),
        ("PRIORIDADE", "2 = emergencial; 1 = normal, conforme cálculo original do MRP."),
        ("SEM OP", "Demandas sem OP de origem são exibidas como SEM OP VINCULADA."),
        ("PARECER", "Preencher as colunas de parecer e observações para devolver a análise."),
        ("IMPORTANTE", "Não utilizar este arquivo na rotina de importação STSUP25 do Protheus."),
        ("GERAÇÃO", datetime.now().strftime("%d/%m/%Y %H:%M")),
    ], columns=["Informação", "Orientação"])

    return {
        "INSTRUÇÕES": orientacoes,
        "RESUMO OP": resumo,
        "MATERIAIS OP": por_material,
        "DETALHE OP": detalhado,
    }
