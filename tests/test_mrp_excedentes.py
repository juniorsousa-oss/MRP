import unittest
from datetime import date

import pandas as pd

from mrp_excedentes import calcular_excedentes


HOJE = date(2026, 11, 6)


def base(*, codigo=50172, estoque=0, demanda=0, pc=0, sc=0, produzindo=0, tipo="MP"):
    sf = estoque + pc + sc + produzindo - demanda
    return pd.DataFrame([{
        "Código": codigo, "Descrição": "MATERIAL DE TESTE", "Tipo": tipo,
        "Saldo em Estoque": estoque, "Demanda": demanda,
        "P.C.": pc, "S.C.": sc, "Produzindo": produzindo, "DIV": sf,
    }])


def compra(*, codigo=50172, pc=0, sem_pc=202646, sc=0, sem_sc=202646,
           num_pc="PC100", num_sc="SC100"):
    return pd.DataFrame([{
        "Código": codigo, "Quantidade P.C.": pc, "Semana P.C.": sem_pc,
        "Nº P.C.": num_pc, "Quantidade S.C.": sc,
        "Semana S.C.": sem_sc, "Nº S.C.": num_sc,
    }])


def proj(*, codigo=50172, semana=202646, demanda=0, produzindo=0):
    return pd.DataFrame([{
        "Código": codigo, "Semana": semana, "Demanda": demanda,
        "Produzindo": produzindo,
    }])


class ExcedentesTests(unittest.TestCase):
    def calcular(self, geral, compras, projecao=None):
        return calcular_excedentes(geral, compras, projecao, hoje=HOJE)

    def test_pc_integral_sem_demanda(self):
        sc, pc = self.calcular(base(pc=3), compra(pc=3), proj())
        self.assertEqual(len(sc), 0)
        self.assertEqual(pc.iloc[0]["Quantidade cancelável"], 3)
        self.assertEqual(pc.iloc[0]["Situação"], "CANCELAMENTO TOTAL — AVALIAR")
        self.assertEqual(pc.iloc[0]["Prioridade"], "MÉDIA")

    def test_tipo_ii_nao_deve_constar(self):
        sc, pc = self.calcular(base(pc=3, tipo="II"), compra(pc=3), proj())
        self.assertTrue(sc.empty and pc.empty)

    def test_falta_nao_e_excedente(self):
        sc, pc = self.calcular(base(estoque=4, demanda=7, sc=3),
                               compra(sc=3), proj(semana=202648, demanda=7))
        self.assertTrue(sc.empty and pc.empty)

    def test_cancelamento_parcial_sc(self):
        sc, pc = self.calcular(base(estoque=4, demanda=7, sc=5),
                               compra(sc=5), proj(semana=202648, demanda=7))
        self.assertEqual(sc.iloc[0]["Quantidade cancelável"], 2)
        self.assertEqual(sc.iloc[0]["Quantidade a manter"], 3)
        self.assertIn("PARCIAL", sc.iloc[0]["Situação"])

    def test_documentos_nao_duplicam_sobra_global(self):
        geral = base(pc=3, sc=2)
        compras = pd.concat([compra(pc=3, sc=0),
                             compra(pc=0, sc=2, sem_sc=202650)], ignore_index=True)
        sc, pc = self.calcular(geral, compras, proj())
        self.assertEqual(sc["Quantidade cancelável"].sum() + pc["Quantidade cancelável"].sum(), 5)

    def test_compra_precoce_e_preservada_quando_necessaria_antes_da_sc(self):
        geral = base(pc=3, sc=3, demanda=3)
        compras = pd.concat([compra(pc=3), compra(sc=3, sem_sc=202650)], ignore_index=True)
        sc, pc = self.calcular(geral, compras, proj(semana=202648, demanda=3))
        self.assertEqual(pc.iloc[0]["Quantidade cancelável"], 0)
        self.assertEqual(sc.iloc[0]["Quantidade cancelável"], 3)

    def test_pc_sem_semana_nao_compunha_sf(self):
        geral = base(estoque=3)
        sc, pc = self.calcular(geral, compra(pc=5, sem_pc=None), None)
        self.assertEqual(pc.iloc[0]["Quantidade cancelável"], 0)
        self.assertEqual(pc.iloc[0]["Situação"], "VALIDAR SEMANA")

    def test_sc_sem_semana_tem_alerta(self):
        geral = base(estoque=5, sc=5)
        sc, pc = self.calcular(geral, compra(sc=5, sem_sc=None), None)
        self.assertEqual(sc.iloc[0]["Quantidade cancelável"], 5)
        self.assertEqual(sc.iloc[0]["Situação"], "VALIDAR PREVISÃO")

    def test_divergencia_das_bases_impede_recomendacao(self):
        geral = base(pc=3)
        sc, pc = self.calcular(geral, compra(pc=5), proj())
        self.assertEqual(pc.iloc[0]["Quantidade cancelável"], 0)
        self.assertIn("DIVERGÊNCIA", pc.iloc[0]["Situação"])

    def test_excedente_estoque_sem_compras_nao_gera_documento(self):
        geral = base(estoque=10)
        compras = compra()
        sc, pc = self.calcular(geral, compras, None)
        self.assertTrue(sc.empty and pc.empty)


if __name__ == "__main__":
    unittest.main()
