"""Testes sem rede da classificação de dependências do MRP."""
import unittest

from mrp_worker_estado import avaliar_estado


def estado_base():
    versoes = {
        "cadastros": "v12",
        "relatorio_geral_tratado": "2026-10-16T19:35:15+00:00",
        "estoque_tratado": "2026-10-16T03:07:46+00:00",
        "compras_tratado": "2026-10-16T19:35:19+00:00",
        "tctp_tratado": "2026-10-16T19:21:31+00:00",
    }
    return {
        "ready": True, "output_stale": True, "stale_inputs": {},
        "cadastro_meta": {"available": True},
        "derived_meta": {
            k: {"available": True, "processed_at": v}
            for k, v in versoes.items() if k != "cadastros"
        },
        "source_meta": {},
        "dependency_versions": versoes,
        "output_meta": {
            "available": True, "processed_at": "2026-10-16T17:53:18+00:00",
            "rows_count": 7842,
        },
    }


class EstadoMRPTests(unittest.TestCase):
    def test_sinaliza_resultado_mrp_antigo(self):
        resultado = avaliar_estado(estado_base())
        self.assertEqual(resultado["status"], "REPROCESSAMENTO_NECESSARIO")
        self.assertTrue(resultado["pronto_para_calcular"])
        self.assertEqual(resultado["registros_do_ultimo_mrp"], 7842)

    def test_nao_atualiza_sem_nova_versao(self):
        dado = estado_base()
        dado["output_stale"] = False
        self.assertEqual(avaliar_estado(dado)["status"], "ATUALIZADO")

    def test_espera_por_conversor_sem_usar_base_antiga(self):
        dado = estado_base()
        dado["ready"] = False
        dado["stale_inputs"] = {
            "tctp_tratado": {"reason": "BASE DESATUALIZADA"}
        }
        self.assertEqual(avaliar_estado(dado)["status"], "AGUARDANDO_CONVERSOR")
        self.assertEqual(
            avaliar_estado(dado)["bases_tratadas_pendentes"], ["tctp_tratado"]
        )

    def test_espera_por_cadastro_ou_base_ausente(self):
        dado = estado_base()
        dado["ready"] = False
        dado["cadastro_meta"]["available"] = False
        dado["derived_meta"]["estoque_tratado"]["available"] = False
        resultado = avaliar_estado(dado)
        self.assertEqual(resultado["status"], "AGUARDANDO_FONTES")
        self.assertEqual(resultado["fontes_ausentes"], ["cadastros", "estoque_tratado"])

    def test_nao_altera_estado_original(self):
        dado = estado_base()
        avaliar_estado(dado)
        self.assertTrue(dado["output_stale"])
        self.assertTrue(dado["ready"])


if __name__ == "__main__":
    unittest.main()
