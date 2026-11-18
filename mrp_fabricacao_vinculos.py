"""Preserva OPs programadas no PMP mesmo quando a BOM H001 não existe.

O Conversor TCTP conserva cada OP PROGRAMADA/ATRASADA sem BOM como uma
linha com MATERIAL=0 e QUANTIDADE POR OF=0. Esses marcadores servem SOMENTE
para contabilizar a oferta de produto acabado (uma unidade por OP); nunca
geram demanda de componentes. A filtragem anterior exigia MATERIAL cadastrado
e apagava a OP inteira do MRP.
"""
from __future__ import annotations

import pandas as pd


def filtrar_tctp_para_mrp(
    tctp: pd.DataFrame,
    codigos_validos: set[int],
) -> pd.DataFrame:
    """Mantém BOM válida e marcador sem BOM, sempre com produto válido.

    - MATERIAL positivo e cadastrado: componente real, permite demanda TC/TP.
    - MATERIAL zero e QUANTIDADE zero: marcador de OP sem BOM, permite apenas
      contabilizar o produto programado em 'Produzindo'.
    - Material inválido com quantidade positiva: não é silenciosamente
      convertido em produção sem BOM.
    """
    obrigatorias = {
        "ORDEM DE PRODUÇÃO", "Código Produto", "Material", "Quantidade",
    }
    ausentes = obrigatorias.difference(tctp.columns)
    if ausentes:
        raise ValueError(
            "TCTP sem colunas obrigatórias para fabricação: "
            + ", ".join(sorted(ausentes))
        )
    if tctp.empty:
        return tctp.copy()

    op = tctp["ORDEM DE PRODUÇÃO"].fillna("").astype(str).str.strip()
    produto = pd.to_numeric(tctp["Código Produto"], errors="coerce")
    material = pd.to_numeric(tctp["Material"], errors="coerce")
    quantidade = pd.to_numeric(tctp["Quantidade"], errors="coerce")

    produto_valido = produto.isin(codigos_validos)
    material_bom_valido = material.gt(0) & material.isin(codigos_validos)
    marcador_sem_bom = (
        material.eq(0)
        & quantidade.eq(0)
        & op.ne("")
    )
    return tctp.loc[
        produto_valido & op.ne("") & (material_bom_valido | marcador_sem_bom)
    ].copy()
