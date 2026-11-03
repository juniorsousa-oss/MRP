"""Regressão de dados complementares em Solicitações Avulsas."""
import unittest
from mrp_avulsas_validacao import identificacao_valida


class IdentificacaoSolicitacoesTests(unittest.TestCase):
    def test_bloqueia_campos_vazios_e_promessas(self):
        for valor in (
            "", " ", "A PREENCHER NA ENTREGA", "a preencher depois",
            "NÃO INFORMADO", "PENDENTE DE APROVAÇÃO",
            "N/A", "xxxx", "Teste",
        ):
            with self.subTest(valor=valor):
                self.assertFalse(identificacao_valida(valor, 2))

    def test_aceita_cr_e_aprovador_concretos(self):
        self.assertTrue(identificacao_valida("600307", 1))
        self.assertTrue(identificacao_valida("João da Silva", 2))
        self.assertTrue(identificacao_valida("CR-0102", 1))

    def test_aprovador_com_um_caractere_nao_basta(self):
        self.assertFalse(identificacao_valida("A", 2))


if __name__ == "__main__":
    unittest.main()
