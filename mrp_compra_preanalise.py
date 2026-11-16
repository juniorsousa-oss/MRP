"""Relatorio de pre-analise da Compra MRP por OP.

Exportacao exclusivamente consultiva, ANTES da liberacao da carga Protheus.
Nao altera exclusoes, aprovacoes, snapshots ou quantidades de origem.
"""
from __future__ import annotations

from datetime import date, datetime
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


def _codigo_material(valor) -> str:
    """Chave de material com oito dígitos, compatível com CADASTROS e MRP."""
    texto = _texto(valor)
    if re.fullmatch(r"\\d+(?:\\.0+)?", texto):
        texto = texto.split(".")[0]
    return texto.zfill(8) if texto.isdigit() and len(texto) <= 8 else texto


def _data_solicitacao(valor) -> pd.Timestamp:
    """Interpreta datas da base tratada/snapshot; não usa data de necessidade."""
    if isinstance(valor, (datetime, date, pd.Timestamp)):
        result = pd.Timestamp(valor)
        return result.tz_localize(None).normalize() if pd.notna(result) else pd.NaT
    texto = _texto(valor)
    if texto.upper() in {"", "NI", "N/A", "NAN", "NAT", "NONE"}:
        return pd.NaT
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return pd.Timestamp(datetime.strptime(texto, formato))
        except ValueError:
            pass
    resultado = pd.to_datetime(texto, errors="coerce", dayfirst=True)
    if pd.isna(resultado):
        return pd.NaT
    resultado = pd.Timestamp(resultado)
    return resultado.tz_localize(None).normalize()


def _mapa_ultimas_solicitacoes(
    solicitacoes: pd.DataFrame | None,
) -> dict[tuple[str, str], str]:
    """Relaciona a data pelo par OP+material; nunca pega data de outra OP.

    ADMIN: rg oriundo do Relatório Geral Tratado.
    CONSULTA: demanda_projeto do snapshot, que já inclui Última Solicitação
    derivada da mesma fonte tratada na execução original.
    """
    if solicitacoes is None or solicitacoes.empty:
        return {}
    if "Projeto" not in solicitacoes.columns:
        raise ValueError("Relatório tratado sem coluna Projeto para última solicitação.")
    col_codigo = next(
        (c for c in ("Código", "Produto") if c in solicitacoes.columns), None
    )
    col_data = next(
        (c for c in ("Data Solicitação", "Última solicitação", "Última Solicitação")
         if c in solicitacoes.columns), None
    )
    if col_codigo is None or col_data is None:
        raise ValueError(
            "Relatório tratado/snapshot sem código e data da última solicitação."
        )

    frame = solicitacoes[["Projeto", col_codigo, col_data]].copy()
    frame["_op"] = frame["Projeto"].map(op_relatorio)
    frame["_codigo"] = frame[col_codigo].map(_codigo_material)
    frame["_data"] = frame[col_data].map(_data_solicitacao)
    frame = frame[
        frame["_op"].ne(OP_NAO_INFORMADA)
        & frame["_codigo"].ne("")
        & frame["_data"].notna()
    ]
    if frame.empty:
        return {}
    ultimas = frame.groupby(["_op", "_codigo"], sort=False)["_data"].max()
    return {chave: data.strftime("%d/%m/%Y") for chave, data in ultimas.items()}


def construir_relatorio_compra_por_op(
    compra: pd.DataFrame,
    descricoes: Mapping[str, str] | None = None,
    ops: Iterable[str] | None = None,
    solicitacoes: pd.DataFrame | None = None,
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
    # A fonte da última solicitação é EXCLUSIVAMENTE o Relatório Tratado
    # ou seu snapshot correspondente. A data da compra ("data") é a data
    # de necessidade e NÃO deve substituir a data da solicitação.
    mapa_solicitacoes = _mapa_ultimas_solicitacoes(solicitacoes)
    fonte["Última solicitação"] = [
        mapa_solicitacoes.get((op, _codigo_material(codigo)), "NI")
        for op, codigo in zip(fonte["OP"], fonte["Código"])
    ]
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
        "OP", "Código", "Descrição", "Quantidade", "Última solicitação",
        "Data de necessidade", "Prioridade", "PSY", "Centro de custo", "Observação MRP",
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
            Última_solicitação=("Última solicitação", "first"),
            Linhas=("Código", "size"),
            Data_mais_proxima=("_data_ordem", "min"),
            Prioridade=("Prioridade", lambda s: "2" if (s == "2").any()
                        else ("1" if (s == "1").any() else _unicos(s))),
            PSY=("PSY", _unicos),
            Centro_de_custo=("Centro de custo", _unicos),
        )
        .reset_index()
        .rename(columns={
            "Última_solicitação": "Última solicitação",
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
        ("ÚLTIMA SOLICITAÇÃO", "Data máxima registrada no Relatório Geral Tratado por OP + código de material; NI indica ausência de correspondência."),
        ("DATAS DISTINTAS", "Última solicitação é a data de pedido do material; data de necessidade é a previsão de atendimento e não é usada como substituta."),
        ("DETALHAMENTO", "Aba DETALHE OP mantém cada linha, a última solicitação da origem e a data de necessidade da compra."),
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
