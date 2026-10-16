"""Monta a versão exata do código MRP usada pelo Streamlit, sem abrir a interface.

Primeiro passo para isolar o motor de cálculo: a montagem aplica os patches já
validados em produção e interrompe o código ANTES de iniciar o Streamlit.

Este módulo NÃO calcula nem publica MRP. A extração só é aceita se cada
âncora da cadeia atual existir exatamente uma vez. Serve como auditoria de
derivação para a implementação headless, evitando divergências silenciosas.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent

APP_EXEC = 'exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
RUNTIME_EXEC = 'exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'


def _replace_exact(content: str, old: str, new: str, label: str) -> str:
    found = content.count(old)
    if found != 1:
        raise RuntimeError(f"Montagem MRP insegura: {label}, ocorrências={found}.")
    return content.replace(old, new, 1)


def montar_fonte_atual() -> str:
    """Obtém a fonte resultante de todos os patches sem executar a interface."""
    app = ROOT / "app_mrp.py"
    runtime = ROOT / "app_mrp_runtime.py"

    assembly = _replace_exact(
        app.read_text(encoding="utf-8"),
        APP_EXEC, "__mrp_runtime__ = _runtime_source",
        "ponto de execução do app",
    )
    contexto: dict[str, Any] = {
        "__file__": str(app), "__name__": "_setta_mrp_assembly_",
    }
    exec(compile(assembly, str(app), "exec"), contexto)
    resolved_runtime = contexto.get("__mrp_runtime__")
    if not isinstance(resolved_runtime, str):
        raise RuntimeError("O runtime completo não foi produzido.")

    second_pass = _replace_exact(
        resolved_runtime,
        RUNTIME_EXEC, "__mrp_source__ = _source",
        "ponto de execução do runtime",
    )
    environment = dict(contexto)
    environment["__file__"] = str(runtime)
    exec(compile(second_pass, str(runtime), "exec"), environment)
    source = environment.get("__mrp_source__")
    if not isinstance(source, str):
        raise RuntimeError("A fonte MRP não foi produzida.")
    ast.parse(source, filename="mrp_fonte_montada.py")
    return source


def _assigned_names(node: ast.AST) -> set[str]:
    targets = []
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    result: set[str] = set()
    for target in targets:
        result.update(
            n.id for n in ast.walk(target)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
        )
    return result


def identificar_bloco_calculo(source: str) -> dict[str, Any]:
    """Relata as instruções do cálculo para posterior extração controlada.

    Esta função não executa as instruções: evita realizar writes indiretos
    ou chamar APIs a partir de expressões usadas pela interface.
    """
    tree = ast.parse(source)
    starts = [
        i for i, node in enumerate(tree.body)
        if "rg_semanas" in _assigned_names(node)
    ]
    ends = [
        i for i, node in enumerate(tree.body)
        if "fab_det" in _assigned_names(node)
    ]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise RuntimeError(
            "O bloco de cálculo MRP mudou; revisão da montagem necessária: "
            f"início={starts}, fim={ends}"
        )

    block = tree.body[starts[0]:ends[0] + 1]
    st_calls: list[int] = []
    for stmt in block:
        for item in ast.walk(stmt):
            if (
                isinstance(item, ast.Attribute)
                and isinstance(item.value, ast.Name)
                and item.value.id == "st"
            ):
                st_calls.append(item.lineno)
    return {
        "source_lines": len(source.splitlines()),
        "calculation_start_line": block[0].lineno,
        "calculation_end_line": block[-1].end_lineno,
        "statement_count": len(block),
        "streamlit_refs": sorted(set(st_calls)),
        "treatments_referenced": any(
            isinstance(item, ast.Name) and item.id == "_carregar_tratativas_salvas"
            for stmt in block for item in ast.walk(stmt)
        ),
        "final_outputs": [
            name for name in (
                "macro", "proj", "demanda_projeto", "compras_mrp", "cp", "fab_det"
            )
            if any(name in _assigned_names(stmt) for stmt in block)
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(
        identificar_bloco_calculo(montar_fonte_atual()),
        ensure_ascii=False, indent=2,
    ))
