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
                result.append((node.lineno, node.end_lineno, type(node).__name__, assigned))
            if started and any(
                isinstance(n, ast.Name) and n.id == "fab_det"
                and isinstance(n.ctx, ast.Store)
                for n in ast.walk(node)
            ):
                break
        print("MAPEAMENTO MOTOR AST", result)
        outer = next(n for n in t.body if getattr(n, "lineno", None) == 4121)
        inner = []
        for item in ast.walk(outer):
            if isinstance(item, (ast.If, ast.Try, ast.With, ast.FunctionDef)):
                src = ast.get_source_segment(s, item)
                first = (src or "").splitlines()[0][:140]
                inner.append((item.lineno, item.end_lineno, type(item).__name__, first))
        print("ESTRUTURA INTERNA DO CÁLCULO", inner[:120])
        print("BLOCO_MRP_PART1", "\\n".join(s.splitlines()[4078:4215]))
        print("BLOCO_MRP_PART2", "\\n".join(s.splitlines()[4440:4512]))
        self.assertTrue(any("fab_det" in x[3] for x in result))
        self.assertGreater(len(result), 4)


if __name__ == "__main__":
    unittest.main()
