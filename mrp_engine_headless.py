"""Motor MRP sem Streamlit, extraído diretamente do runtime validado.

Atenção: NÃO busca fontes, NÃO busca tratativas e NÃO publica dados.
Todas as entradas (incluindo tratativas autorizadas) devem ser fornecidas.
A extração falha quando as âncoras do código oficial mudam.
"""
from __future__ import annotations

import ast
from datetime import date, datetime, timedelta
import hashlib
import json
import re
from typing import Any

import pandas as pd

from mrp_engine_extract import montar_fonte_atual, _assigned_names


HELPERS = (
    "num", "semana_id", "_inicio_semana", "periodo_semana", "ultimo_dia_util_semana",
    "formatar_data_br", "normalizar_compra_mrp", "_texto_normalizado", "_projeto_key",
    "_produto_key", "_preparar_compra_prioridades",
)
OUTPUTS = ("macro", "proj", "demanda_projeto", "compras_mrp", "cp", "fab_det")


class _HeadlessTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name):
            replacements = {
                "_carregar_tratativas_salvas": "tratativas_projeto_injetadas",
                "_carregar_tratativas_produto_salvas": "tratativas_produto_injetadas",
            }
            name = replacements.get(node.func.id)
            if name:
                if node.args or node.keywords:
                    raise RuntimeError("Assinatura da leitura de tratativas mudou.")
                return ast.copy_location(
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=name, ctx=ast.Load()),
                            attr="copy", ctx=ast.Load(),
                        ),
                        args=[], keywords=[],
                    ),
                    node,
                )
        return node

    def visit_Try(self, node):
        # A interface apenas exibe a falha e chama st.stop(). No motor puro,
        # a exceção deve propagar ao job sem mascarar um cálculo incompleto.
        for handler in node.handlers:
            if any(
                isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == "st"
                for n in ast.walk(handler)
            ):
                return [self.visit(n) for n in node.body]
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if any(
            isinstance(x, ast.Name) and x.id == "st"
            for target in node.targets for x in ast.walk(target)
        ):
            return None  # Cache Streamlit, nunca gravar em session_state.
        return self.generic_visit(node)


def construir_motor():
    source = montar_fonte_atual()
    tree = ast.parse(source)
    helpers = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in HELPERS:
            if node.name in helpers:
                raise RuntimeError(f"Função duplicada no motor: {node.name}")
            helpers[node.name] = node
    missing = set(HELPERS) - set(helpers)
    if missing:
        raise RuntimeError(f"Funções de negócio ausentes: {sorted(missing)}")

    inicio = [
        i for i, node in enumerate(tree.body)
        if "rg_semanas" in _assigned_names(node)
    ]
    cache_nodes = [
        node for node in tree.body
        if isinstance(node, ast.If)
        and "_mrp_cached" in (ast.get_source_segment(source, node) or "").splitlines()[0]
        and node.orelse
    ]
    if len(inicio) != 2 or inicio[1] != inicio[0] + 1 or len(cache_nodes) != 1:
        raise RuntimeError("Âncoras do cálculo MRP não correspondem ao runtime oficial.")

    # No original, as duas primeiras atribuições de semana são seguidas
    # pelo if que escolhe a semana vigente ou um fallback nas outras fontes.
    semanal = tree.body[inicio[0]:inicio[0] + 3]
    if not isinstance(semanal[-1], ast.If):
        raise RuntimeError("Regra de seleção da semana foi modificada.")

    # Elimina apenas as chamadas de interface no caso de semana inválida.
    fallback = semanal[-1]
    for node in ast.walk(fallback):
        if isinstance(node, ast.If) and isinstance(node.test, ast.UnaryOp):
            pass
    # Se o cálculo não puder determinar semana, o antigo Streamlit usa
    # st.error + st.stop; substituímos os dois por ValueError.
    for node in ast.walk(fallback):
        if not isinstance(node, ast.If):
            continue
        condition = ast.unparse(node.test)
        if "semanas_base" in condition and "not " in condition:
            node.body = [ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id="ValueError", ctx=ast.Load()),
                    args=[ast.Constant(value="Sem semana operacional válida nas bases MRP.")],
                    keywords=[],
                ),
                cause=None,
            )]

    body = [*semanal, *cache_nodes[0].orelse]
    converted = _HeadlessTransformer().visit(ast.Module(body=body, type_ignores=[]))
    body = converted.body
    if any(
        isinstance(x, ast.Name) and x.id == "st"
        for statement in body for x in ast.walk(statement)
    ):
        raise RuntimeError("O núcleo de cálculo ainda contém chamadas à interface Streamlit.")

    body.append(ast.Return(
        value=ast.Dict(
            keys=[ast.Constant(value=name) for name in OUTPUTS],
            values=[ast.Name(id=name, ctx=ast.Load()) for name in OUTPUTS],
        )
    ))
    args = ast.arguments(
        posonlyargs=[], args=[
            ast.arg(arg=name) for name in (
                "cad", "est", "rg", "rg_mrp", "cp", "mt",
                "tratativas_projeto_injetadas", "tratativas_produto_injetadas",
            )
        ], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[],
    )
    function = ast.FunctionDef(
        name="_calcular", args=args, body=body,
        decorator_list=[], returns=None, type_comment=None,
    )
    # Captura apenas funções auxiliares e instruções de negócio.
    code = ast.Module(body=[*helpers.values(), function], type_ignores=[])
    code = ast.fix_missing_locations(code)
    namespace: dict[str, Any] = {
        "__builtins__": __builtins__, "pd": pd, "date": date,
        "datetime": datetime, "timedelta": timedelta,
        "hashlib": hashlib, "json": json, "re": re,
    }
    exec(compile(code, "<mrp_core_extraido>", "exec"), namespace)
    return namespace["_calcular"]


def calcular_mrp(
    cad: pd.DataFrame, est: pd.DataFrame, rg: pd.DataFrame,
    rg_mrp: pd.DataFrame, cp: pd.DataFrame, mt: pd.DataFrame,
    tratativas_projeto: pd.DataFrame, tratativas_produto: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    if tratativas_projeto is None or tratativas_produto is None:
        raise ValueError("Tratativas autorizadas são obrigatórias; não assumir vazias.")
    calculator = construir_motor()
    result = calculator(cad.copy(), est.copy(), rg.copy(), rg_mrp.copy(),
                        cp.copy(), mt.copy(),
                        tratativas_projeto.copy(), tratativas_produto.copy())
    for name in OUTPUTS:
        if name not in result or not isinstance(result[name], pd.DataFrame):
            raise RuntimeError(f"Resultado obrigatório ausente: {name}")
    return result
