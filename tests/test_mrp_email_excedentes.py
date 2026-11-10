"""Testes sem SMTP, sem envio externo e sem acesso ao banco real."""
from datetime import date, datetime, timezone
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch
import json
import os
import pandas as pd

import mrp_email_excedentes as report
from mrp_excedentes import calcular_excedentes


HOJE = date(2026, 11, 10)


def fixture():
    mrp = pd.DataFrame([
        {"Código": 50172, "Descrição": "FONTE TESTE", "Tipo": "MP",
         "Saldo em Estoque": 3, "Demanda": 3, "P.C.": 5, "S.C.": 2,
         "Produzindo": 0, "SF": 7},
        {"Código": 50173, "Descrição": "OUTRO MATERIAL", "Tipo": "II",
         "Saldo em Estoque": 0, "Demanda": 0, "P.C.": 5, "S.C.": 0,
         "Produzindo": 0, "SF": 5},
    ])
    cp = pd.DataFrame([
        {"Código": 50172, "Quantidade P.C.": 5, "Semana P.C.": "2026-46",
         "Nº P.C.": "034196", "Quantidade S.C.": 0, "Semana S.C.": None,
         "Nº S.C.": ""},
        {"Código": 50172, "Quantidade P.C.": 0, "Semana P.C.": None,
         "Nº P.C.": "", "Quantidade S.C.": 2, "Semana S.C.": "2026-47",
         "Nº S.C.": "034257"},
        {"Código": 50173, "Quantidade P.C.": 5, "Semana P.C.": "2026-46",
         "Nº P.C.": "888888", "Quantidade S.C.": 0, "Semana S.C.": None,
         "Nº S.C.": ""},
    ])
    proj = pd.DataFrame([
        {"Código": 50172, "Semana": "2026-45", "Demanda": 3, "Produzindo": 0},
    ])
    return {
        "id": 105,
        "created_at": "2026-11-10T13:00:00Z",
        "mrp_geral": mrp.to_dict("records"),
        "compras": cp.to_dict("records"),
        "projecao_semanal": proj.to_dict("records"),
    }


class CancelEmailTests(TestCase):
    def test_relatorio_usa_duas_abas_enxutas_e_descarta_tipo_ii(self):
        x = report.preparar_cancelamentos(fixture(), HOJE)
        self.assertEqual(x["resumo"]["pedidos"] + x["resumo"]["solicitacoes"], 2)
        with pd.ExcelFile(BytesIO(x["excel"])) as excel:
            self.assertEqual(excel.sheet_names, ["Solicitações SC", "Pedidos PC"])
            sc = pd.read_excel(excel, "Solicitações SC")
            pc = pd.read_excel(excel, "Pedidos PC")
        self.assertEqual(sc["Qtd. Cancelar"].sum() + pc["Qtd. Cancelar"].sum(), 7)
        self.assertNotIn("Quantidade em aberto", sc.columns)
        self.assertNotIn("Quantidade a manter", pc.columns)
        self.assertFalse((pc["Nº P.C."].astype(str) == "888888").any())

    def test_sem_data_atual_nunca_envia(self):
        sample = fixture()
        sample["created_at"] = "2026-11-09T12:00:00Z"
        metas = [
            {"base_key": base, "status": "ATUALIZADO", "processed_at": "2026-11-09T10:00:00Z"}
            for base in report.BASES
        ]
        metas[0]["source_versions"] = {
            item["base_key"]: item["processed_at"] for item in metas[1:]
        }
        with self.assertRaisesRegex(report.RelatorioIndisponivel, "hoje"):
            report._snapshot_consistente(sample, metas, HOJE)

    def test_base_mais_nova_que_snapshot_bloqueia(self):
        sample = fixture()
        metas = [
            {"base_key": base, "status": "ATUALIZADO", "processed_at": "2026-11-10T12:00:00Z"}
            for base in report.BASES
        ]
        metas[0]["source_versions"] = {
            item["base_key"]: item["processed_at"] for item in metas[1:]
        }
        metas[2]["processed_at"] = "2026-11-10T15:00:00Z"
        with self.assertRaisesRegex(report.RelatorioIndisponivel, "mais recente"):
            report._snapshot_consistente(sample, metas, HOJE)

    def test_snapshot_com_dependencias_atrasadas_e_bloqueado(self):
        sample = fixture()
        metas = [
            {"base_key": base, "status": "ATUALIZADO", "processed_at": "2026-11-10T12:00:00Z"}
            for base in report.BASES
        ]
        metas[0]["source_versions"] = {
            item["base_key"]: item["processed_at"] for item in metas[1:]
        }
        metas[0]["source_versions"]["compras_tratado"] = "2026-11-09T12:00:00Z"
        with self.assertRaisesRegex(report.RelatorioIndisponivel, "não corresponde"):
            report._snapshot_consistente(sample, metas, HOJE)

    def test_dry_run_nao_envia_nem_reserva(self):
        with patch.object(report, "_settings") as settings, \
             patch.object(report, "_registrar_envio") as reserve, \
             patch.object(report, "_smtp_send") as send:
            result = report.executar(hoje=HOJE, dry_run=True, snapshot=fixture())
        self.assertEqual(result["status"], "SIMULADO")
        settings.assert_not_called()
        reserve.assert_not_called()
        send.assert_not_called()

    def test_sem_destinatario_ou_transportadora_envio_bloqueado(self):
        with patch.dict(os.environ, {"MRP_CANCEL_EMAIL_TO": "",
                                     "MRP_CANCEL_DELIVERY_MODE": "smtp"}):
            with self.assertRaisesRegex(report.RelatorioIndisponivel, "Destinatário"):
                report.executar(hoje=HOJE, snapshot=fixture())

    def test_destinatario_externo_e_rejeitado(self):
        with self.assertRaises(report.RelatorioIndisponivel):
            report._enderecos("fornecedor@externo.com")

    def test_nao_dispara_duas_vezes_no_mesmo_dia(self):
        params = {"MRP_CANCEL_EMAIL_TO": "compras@gruposetta.com",
                  "MRP_CANCEL_DELIVERY_MODE": "smtp",
                  "MRP_CANCEL_SEND_ENABLED": "true"}
        with patch.dict(os.environ, params), \
             patch.object(report, "_settings", return_value=("https://cuixazpxkvniqldmmnth.supabase.co", "fake")), \
             patch.object(report, "_registrar_envio", return_value=False) as reserve, \
             patch.object(report, "_smtp_send") as send:
            result = report.executar(hoje=HOJE, snapshot=fixture())
        self.assertEqual(result["status"], "JA_PROCESSADO_HOJE")
        reserve.assert_called_once()
        send.assert_not_called()

    def test_envio_real_somente_apos_reserva(self):
        params = {"MRP_CANCEL_EMAIL_TO": "compras@gruposetta.com",
                  "MRP_CANCEL_DELIVERY_MODE": "smtp",
                  "MRP_CANCEL_SEND_ENABLED": "true"}
        with patch.dict(os.environ, params), \
             patch.object(report, "_settings", return_value=("https://cuixazpxkvniqldmmnth.supabase.co", "fake")), \
             patch.object(report, "_registrar_envio", return_value=True), \
             patch.object(report, "_finalizar_envio") as done, \
             patch.object(report, "_smtp_send") as send:
            result = report.executar(hoje=HOJE, snapshot=fixture())
        self.assertEqual(result["status"], "ACEITO_PELO_TRANSPORTE")
        send.assert_called_once()
        done.assert_called_once()

    def test_webhook_teams_aceita_http_202_e_mantem_anexo(self):
        from unittest.mock import Mock
        from base64 import b64decode
        preparado = report.preparar_cancelamentos(fixture(), HOJE)
        conn = Mock()
        conn.post.return_value.status_code = 202
        with patch.dict(os.environ, {
            "MRP_CANCEL_EMAIL_WORKFLOW_URL":
                "https://example.com/endpoint-de-teste",
        }):
            report._workflow_send(
                preparado, ["compras@gruposetta.com"], [], "Assunto",
                "Texto", "<p>Corpo</p>", conn,
            )
        payload = conn.post.call_args.kwargs["json"]
        self.assertEqual(payload["type"], "message")
        self.assertEqual(payload["attachments"], [])
        self.assertEqual(payload["para"], "compras@gruposetta.com")
        self.assertEqual(payload["assunto"], "Assunto")
        self.assertEqual(payload["html"], "<p>Corpo</p>")
        self.assertEqual(b64decode(payload["anexo_base64"]), preparado["excel"])
        self.assertTrue(payload["nome_anexo"].endswith(".xlsx"))
        self.assertFalse(conn.post.call_args.kwargs["allow_redirects"])

    def test_webhook_teams_rejeitado_http_401_gera_erro(self):
        from unittest.mock import Mock
        preparado = report.preparar_cancelamentos(fixture(), HOJE)
        conn = Mock()
        conn.post.return_value.status_code = 401
        with patch.dict(os.environ, {
            "MRP_CANCEL_EMAIL_WORKFLOW_URL":
                "https://example.com/endpoint-de-teste",
        }):
            with self.assertRaisesRegex(
                report.RelatorioIndisponivel, "HTTP 401",
            ):
                report._workflow_send(
                    preparado, ["compras@gruposetta.com"], [], "Assunto",
                    "Texto", "<p>Corpo</p>", conn,
                )

    def test_email_conteudo_nao_ordenar_sc_antes_de_pc(self):
        subject, text, html_body = report._mensagem(
            report.preparar_cancelamentos(fixture(), HOJE)
        )
        self.assertIn("S.C. e P.C.", subject)
        self.assertIn("duas abas", text)
        self.assertIn("Nenhuma compra será cancelada automaticamente", html_body)


if __name__ == "__main__":
    import unittest
    unittest.main()
