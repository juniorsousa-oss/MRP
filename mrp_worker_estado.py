"""Diagnóstico autônomo da atualização do MRP, SEM publicar resultados.

Esta primeira etapa é deliberadamente somente leitura: valida a sequência
Central -> Conversor -> MRP antes de liberar um executor de cálculos.
A lógica de versões permanece definida em central_mrp_data.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def avaliar_estado(estado: dict[str, Any]) -> dict[str, Any]:
    """Classifica um instantâneo do MRP sem consultar banco ou alterar dados."""
    fontes = estado.get("source_meta") or {}
    tratadas = estado.get("derived_meta") or {}
    cadastro = estado.get("cadastro_meta") or {}
    pendencias = estado.get("stale_inputs") or {}
    versoes = estado.get("dependency_versions") or {}
    atual = estado.get("output_meta") or {}

    ausentes: list[str] = []
    if not cadastro.get("available"):
        ausentes.append("cadastros")
    ausentes.extend(
        key for key, item in tratadas.items()
        if not item.get("available")
    )
    if pendencias:
        situacao = "AGUARDANDO_CONVERSOR"
    elif ausentes or not estado.get("ready"):
        situacao = "AGUARDANDO_FONTES"
    elif estado.get("output_stale"):
        situacao = "REPROCESSAMENTO_NECESSARIO"
    else:
        situacao = "ATUALIZADO"

    return {
        "status": situacao,
        "pronto_para_calcular": bool(estado.get("ready")),
        "mrp_desatualizado": bool(estado.get("output_stale")),
        "fontes_ausentes": sorted(set(ausentes)),
        "bases_tratadas_pendentes": sorted(pendencias.keys()),
        "versoes_das_dependencias": {str(k): str(v) for k, v in versoes.items()},
        "ultimo_mrp_processado_em": str(atual.get("processed_at") or ""),
        "registros_do_ultimo_mrp": int(atual.get("rows_count") or 0),
        "base_mrp_disponivel": bool(atual.get("available")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica se o MRP SETTA precisa ser recalculado (não publica)."
    )
    parser.add_argument(
        "--check-only", action="store_true", required=True,
        help="Obrigatório na fase inicial; impede publicação inadvertida."
    )
    parser.parse_args()

    try:
        from central_mrp_data import inspect_mrp_state
        report = avaliar_estado(inspect_mrp_state(force_check=True))
    except Exception as exc:
        print(
            json.dumps({
                "status": "ERRO_CONSULTA",
                "tipo": type(exc).__name__,
                "erro": "Não foi possível verificar as fontes na Central SETTA.",
            }, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
