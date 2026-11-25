import ast
import unittest
from unittest.mock import patch

import pandas as pd

from mrp_engine_extract import montar_fonte_atual
from mrp_operacao_ui import operacao_tabela_detalhe


class DetalheTests(unittest.TestCase):
    @patch("mrp_operacao_ui.st.dataframe")
    def test_oculta_identidade_e_vazios_sem_remover_zeros_ou_alterar_origem(self, dataframe):
        original = pd.DataFrame({
            "Código Produto":[42,42,42,42], "Descrição":["Material"]*4, "Tipo":["MP"]*4,
            "ORDEM DE PRODUÇÃO":["OP-1","  ","OP-2",None],
            "Quantidade":[0,None,None,None]
        })
        before = original.copy()
        self.assertTrue(operacao_tabela_detalhe(original, column_order=list(original)))
        shown = dataframe.call_args.args[0]
        self.assertEqual(list(shown), ["ORDEM DE PRODUÇÃO", "Quantidade"])
        self.assertEqual(shown["ORDEM DE PRODUÇÃO"].tolist(), ["OP-1", "OP-2"])
        self.assertEqual(shown["Quantidade"].iloc[0], 0)
        self.assertEqual(dataframe.call_args.kwargs["height"], "auto")
        pd.testing.assert_frame_equal(original,before)

    @patch("mrp_operacao_ui.st.dataframe")
    def test_sem_registros_nao_monta_grade(self, dataframe):
        self.assertFalse(operacao_tabela_detalhe(pd.DataFrame({"Código":[42], "Projeto":[" "]})))
        dataframe.assert_not_called()

    def test_consulta_e_admin_usam_a_mesma_regra_nas_quatro_abas(self):
        source = ast.parse(montar_fonte_atual())
        details = {n.name:n for n in ast.walk(source) if isinstance(n,ast.FunctionDef)
                   and n.name in {"_render_detalhe_admin","_render_detalhe_consulta"}}
        self.assertEqual(len(details),2)
        for node in details.values():
            self.assertEqual(sum(isinstance(c,ast.Call) and ast.unparse(c.func)=="operacao_tabela_detalhe"
                                 for c in ast.walk(node)),4)
