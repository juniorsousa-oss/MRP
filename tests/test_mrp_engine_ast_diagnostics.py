"""Inspeção de estrutura do cálculo real para extração sem divergência."""
from __future__ import annotations

import ast
import unittest

from mrp_engine_extract import _assigned_names, montar_fonte_atual


class MotorASTTests(unittest.TestCase):
    def test_mapear_evidencias(self):
        s = montar_fonte_atual()
        t = ast.parse(s)
        started = False
        result = []
        for node in t.body:
            names = _assigned_names(node)
            if "rg_semanas" in names:
                started = True
            if started:
                assigned = sorted({
                    n.id for n in ast.walk(node)
                    if isinstance(n, ast.Name)
                    and isinstance(n.ctx, ast.Store)
                })
                result.append((node.lineno, node.end_lineno, type(node).__name__, assigned[:17]))
            if started and any(
                isinstance(n, ast.Name) and n.id == "fab_det"
                and isinstance(n.ctx, ast.Store)
                for n in ast.walk(node)
            ):
                break
        print("MAPEAMENTO MOTOR AST", result)
        self.assertTrue(any("fab_det" in x[3] for x in result))
        self.assertGreater(len(result), 4)


if __name__ == "__main__":
    unittest.main()
