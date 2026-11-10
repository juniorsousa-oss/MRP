"""Relatório diário de sugestões de cancelamento de S.C./P.C. — SETTA.

Executa apenas em ambiente servidor. NÃO altera pedidos/solicitações.
Reutiliza o motor e o Excel oficiais de mrp_excedentes, inclusive priorização
por semana e preservação de quantidades necessárias.
Bloqueia e-mails com snapshot defasado e bloqueia duplicação pelo livro
de envios na Central de Dados.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, date
from email.message import EmailMessage
from email.utils import getaddresses
import hashlib
import html
import json
import os
import re
import smtplib
import ssl
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from mrp_excedentes import (
    _excel_excedentes, calcular_excedentes, preparar_relatorio_enxuto,
)
from mrp_shadow_compare import abrir_snapshot

TZ = ZoneInfo("America/Sao_Paulo")
BASES = (
    "relatorio_mrp", "relatorio_geral_tratado",
    "compras_tratado", "estoque_tratado", "tctp_tratado",
)
TABLE = "mrp_excedentes_envios"
MAX_BYTES = 6_000_000


class RelatorioIndisponivel(RuntimeError):
    """Pré-condições para envio ainda não atendidas."""


def _utc_datetime(value):
    if not value:
        raise RelatorioIndisponivel("Fonte sem instante de atualização.")
    instante = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(instante):
        raise RelatorioIndisponivel("Data de atualização inválida.")
    return instante.to_pydatetime()


def _settings():
    url = os.getenv("MRP_EMAIL_SUPABASE_URL", "https://cuixazpxkvniqldmmnth.supabase.co").rstrip("/")
    host = urlparse(url)
    if host.scheme != "https" or host.hostname != "cuixazpxkvniqldmmnth.supabase.co":
        raise RelatorioIndisponivel("URL da Central não autorizada para a rotina de e-mail.")
    token = os.getenv("MRP_EMAIL_SUPABASE_KEY", "").strip()
    if not token:
        raise RelatorioIndisponivel("Credencial servidor/serviço de leitura e controle não configurada.")
    return url, token


def _get_rows(session, url, key, table, params, *, timeout=45):
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    try:
        response = session.get(f"{url}/rest/v1/{table}", headers=headers, params=params, timeout=timeout)
        if response.status_code != 200:
            raise RelatorioIndisponivel(f"Consulta da Central indisponível: HTTP {response.status_code}.")
        values = response.json()
        if not isinstance(values, list):
            raise ValueError("Expected array")
        return values
    except (requests.RequestException, ValueError):
        raise RelatorioIndisponivel("Resposta inválida na leitura da Central.") from None


def _snapshot_consistente(snapshot, metas, hoje):
    """Recusa fotografia anterior à última versão das entradas do MRP."""
    instante = _utc_datetime(snapshot.get("created_at"))
    if instante.astimezone(TZ).date() != hoje:
        raise RelatorioIndisponivel("MRP oficial não foi recalculado hoje. E-mail não enviado.")
    por_chave = {x.get("base_key"): x for x in metas}
    faltando = set(BASES) - set(por_chave)
    if faltando:
        raise RelatorioIndisponivel("Há bases tratadas sem metadados.")
    for item in por_chave.values():
        status = str(item.get("status") or "").upper()
        if status and status not in {"ATUALIZADO", "SEM ALTERAÇÃO", "OK", "SUCCESS"}:
            raise RelatorioIndisponivel("Uma base tratada não está atualizada.")
        processado = _utc_datetime(item.get("processed_at"))
        if processado > instante:
            raise RelatorioIndisponivel("Fonte mais recente que o MRP salvo; atualizar o MRP antes do e-mail.")
    saida = por_chave["relatorio_mrp"].get("source_versions") or {}
    for nome in BASES:
        if nome == "relatorio_mrp":
            continue
        registrado = saida.get(nome)
        atual = por_chave[nome].get("processed_at")
        if not registrado or not atual:
            raise RelatorioIndisponivel("Versões de dependência não verificáveis.")
        if abs((_utc_datetime(registrado) - _utc_datetime(atual)).total_seconds()) > 2:
            raise RelatorioIndisponivel("MRP publicado não corresponde à versão das bases tratadas.")
    return instante


def coletar_snapshot_consistente(session=None, hoje=None):
    session = session or requests.Session()
    hoje = hoje or datetime.now(TZ).date()
    url, key = _settings()
    base = _get_rows(
        session, url, key, "mrp_snapshots",
        {"select": "id,created_at,calculation_key,compressed_payload",
         "order": "created_at.desc", "limit": "1"},
    )
    metas = _get_rows(
        session, url, key, "setta_derived_bases",
        {"select": "base_key,status,processed_at,source_versions",
         "base_key": "in.(" + ",".join(BASES) + ")"},
    )
    if not base:
        raise RelatorioIndisponivel("Ainda não existe snapshot oficial do MRP.")
    snapshot = base[0]
    _snapshot_consistente(snapshot, metas, hoje)
    # Descompactação em memória com o limite já aplicado pelo comparador do MRP.
    resultado = abrir_snapshot(snapshot)
    return resultado


def preparar_cancelamentos(snapshot, hoje=None):
    hoje = hoje or datetime.now(TZ).date()
    for nome in ("mrp_geral", "compras", "projecao_semanal"):
        if not isinstance(snapshot.get(nome), list):
            raise RelatorioIndisponivel("Snapshot não contém a seção " + nome + ".")
    mrp = pd.DataFrame(snapshot["mrp_geral"])
    compras = pd.DataFrame(snapshot["compras"])
    projecao = pd.DataFrame(snapshot["projecao_semanal"])
    if mrp.empty or compras.empty or projecao.empty:
        raise RelatorioIndisponivel("MRP, compras ou projeção vazios; não é seguro enviar recomendações.")
    required_mrp = {"Código", "Descrição", "Tipo", "Demanda", "Produzindo",
                    "Saldo em Estoque", "P.C.", "S.C."}
    if not required_mrp.issubset(mrp.columns) or not ({"SF", "DIV"} & set(mrp.columns)):
        raise RelatorioIndisponivel("Colunas necessárias do MRP ausentes.")
    required_cp = {"Código", "Quantidade S.C.", "Semana S.C.", "Nº S.C.",
                   "Quantidade P.C.", "Semana P.C.", "Nº P.C."}
    required_proj = {"Código", "Semana", "Demanda", "Produzindo"}
    if not required_cp.issubset(compras.columns) or not required_proj.issubset(projecao.columns):
        raise RelatorioIndisponivel("Compras ou projeção sem campos essenciais.")

    sc, pc = calcular_excedentes(mrp, compras, projecao, hoje=hoje)
    sc_resumo = preparar_relatorio_enxuto(sc, "S.C.")
    pc_resumo = preparar_relatorio_enxuto(pc, "P.C.")
    # O motor já elimina sugestões inseguras e documentos com dados agrupados.
    # Uma linha por produto-documento; abas independentes.
    excel = _excel_excedentes(sc, pc, hoje)
    if len(excel) > MAX_BYTES:
        raise RelatorioIndisponivel("Anexo excede o limite de 6 MB; envio bloqueado.")
    return {
        "sc": sc_resumo,
        "pc": pc_resumo,
        "excel": excel,
        "snapshot_id": snapshot.get("id"),
        "data": hoje,
        "resumo": {
            "solicitacoes": len(sc_resumo),
            "pedidos": len(pc_resumo),
            "parciais_sc": int(sc_resumo["Cancelamento"].eq("PARCIAL").sum()),
            "parciais_pc": int(pc_resumo["Cancelamento"].eq("PARCIAL").sum()),
        },
    }


def _enderecos(raw):
    if not str(raw or "").strip():
        return []
    candidatos = getaddresses([str(raw).replace(";", ",")])
    encontrados = []
    allowed = set(filter(None, re.split(r"[,;\s]+", os.getenv("MRP_CANCEL_ALLOWED_DOMAINS", "gruposetta.com").lower())))
    for _, addr in candidatos:
        addr = addr.strip()
        if not re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", addr):
            raise RelatorioIndisponivel("Endereço de destinatário inválido.")
        if addr.rsplit("@", 1)[-1].lower() not in allowed:
            raise RelatorioIndisponivel("Destinatário fora do domínio corporativo autorizado.")
        if addr.lower() not in [x.lower() for x in encontrados]:
            encontrados.append(addr)
    return encontrados


def _mensagem(relatorio):
    today = relatorio["data"]
    s = relatorio["resumo"]
    subject = f"SETTA | Análise de cancelamentos S.C. e P.C. | {today:%d/%m/%Y}"
    text = (
        f"Suprimentos,\n\nSegue a análise indicativa de compras potencialmente canceláveis "
        f"do MRP SETTA, referência {today:%d/%m/%Y}.\n\n"
        f"S.C.: {s['solicitacoes']} produto-solicitação "
        f"({s['parciais_sc']} parciais).\n"
        f"P.C.: {s['pedidos']} produto-pedido "
        f"({s['parciais_pc']} parciais).\n\n"
        "A planilha contém duas abas distintas e apenas a quantidade sugerida "
        "para cancelamento por produto e documento. A prioridade decorre da semana "
        "prevista, com os prazos mais próximos primeiro.\n\n"
        "Atenção: são recomendações para análise de Suprimentos; este relatório "
        "não cancela S.C. ou P.C. automaticamente. Confirmar condições de "
        "fornecedor, recebimento e ERP antes da tratativa.\n\n"
        "Relatório gerado automaticamente pelo MRP SETTA."
    )
    body = "<html><body style='font-family:Arial,sans-serif;color:#182033'>"
    body += "<h2>SETTA | Compras para avaliação de cancelamento</h2>"
    body += f"<p>Referência: <strong>{today:%d/%m/%Y}</strong></p>"
    body += "<table cellpadding='10' style='border-collapse:collapse;border:1px solid #dfe5ee'>"
    body += "<tr><th>Solicitações (S.C.)</th><th>Pedidos (P.C.)</th></tr>"
    body += f"<tr><td>{s['solicitacoes']} documentos/produtos (parciais: {s['parciais_sc']})</td>"
    body += f"<td>{s['pedidos']} documentos/produtos (parciais: {s['parciais_pc']})</td></tr></table>"
    body += (
        "<p>A planilha anexa tem abas separadas para S.C. e P.C., com "
        "<strong>quantidade cancelável por produto-documento</strong> e "
        "prioridade pela proximidade da semana prevista.</p>"
        "<p><strong>Atenção:</strong> indicação para análise de Suprimentos. "
        "Nenhuma compra será cancelada automaticamente.</p>"
        "<p style='color:#64748b'>MRP SETTA — comunicado automático.</p></body></html>"
    )
    return subject, text, body


def _smtp_send(report, to, cc, subject, text, body):
    host = os.getenv("MRP_CANCEL_SMTP_HOST", "").strip()
    user = os.getenv("MRP_CANCEL_SMTP_USER", "").strip()
    password = os.getenv("MRP_CANCEL_SMTP_PASSWORD", "").strip()
    from_mail = os.getenv("MRP_CANCEL_EMAIL_FROM", "").strip()
    port = int(os.getenv("MRP_CANCEL_SMTP_PORT", "587"))
    if not all((host, user, password, from_mail)) or port not in (465, 587):
        raise RelatorioIndisponivel("SMTP corporativo não configurado.")
    if len(_enderecos(from_mail)) != 1:
        raise RelatorioIndisponivel("Remetente inválido.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_mail
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.set_content(text)
    msg.add_alternative(body, subtype="html")
    msg.add_attachment(
        report["excel"],
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"SETTA_Cancelamentos_SC_PC_{report['data']:%Y%m%d}.xlsx",
    )
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=35, context=ssl.create_default_context()) as conn:
            conn.login(user, password)
            conn.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=35) as conn:
            conn.ehlo()
            conn.starttls(context=ssl.create_default_context())
            conn.ehlo()
            conn.login(user, password)
            conn.send_message(msg)


def _workflow_send(report, to, cc, subject, text, body, session):
    url = os.getenv("MRP_CANCEL_EMAIL_WORKFLOW_URL", "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise RelatorioIndisponivel("Power Automate não configurado por URL HTTPS.")
    payload = {
        "tipo": "CANCELAMENTO_COMPRAS", "para": ";".join(to),
        "copia": cc, "assunto": subject,
        "texto": text, "html": body,
        "nome_anexo": f"SETTA_Cancelamentos_SC_PC_{report['data']:%Y%m%d}.xlsx",
        "anexo_base64": base64.b64encode(report["excel"]).decode("ascii"),
    }
    # Não registrar endereço do webhook (pode conter assinatura secreta).
    try:
        response = session.post(url, json=payload, timeout=65, allow_redirects=False)
    except requests.RequestException:
        raise RelatorioIndisponivel("Falha de comunicação com o serviço de envio.") from None
    if response.status_code != 200:
        raise RelatorioIndisponivel(
            f"O fluxo de e-mail não confirmou conclusão (HTTP {response.status_code})."
        )


def _registrar_envio(session, url, key, report, recipient_hash):
    digest = hashlib.sha256(report["excel"]).hexdigest()
    headers = {
        "apikey": key, "Authorization": f"Bearer {key}",
        "Prefer": "resolution=ignore-duplicates,return=representation",
        "Content-Type": "application/json",
    }
    payload = {
        "data_referencia": report["data"].isoformat(),
        "snapshot_id": int(report["snapshot_id"]),
        "status": "RESERVADO",
        "planilha_hash": digest,
        "destinatarios_hash": recipient_hash,
        "qtd_sc": report["resumo"]["solicitacoes"],
        "qtd_pc": report["resumo"]["pedidos"],
    }
    try:
        response = session.post(
            f"{url}/rest/v1/{TABLE}?on_conflict=data_referencia",
            headers=headers, json=payload, timeout=30,
        )
        response.raise_for_status()
        rows = response.json()
    except (requests.RequestException, ValueError):
        raise RelatorioIndisponivel("Não foi possível reservar o envio; sem e-mail para evitar duplicidade.") from None
    if not isinstance(rows, list):
        raise RelatorioIndisponivel("Controle de duplicidade não confirmou reserva.")
    return bool(rows)


def _finalizar_envio(session, url, key, report, status):
    headers = {
        "apikey": key, "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    try:
        response = session.patch(
            f"{url}/rest/v1/{TABLE}",
            params={"data_referencia": "eq." + report["data"].isoformat(),
                    "status": "eq.RESERVADO"},
            headers=headers, json={"status": status}, timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException:
        # Estado reservado nunca será reenviado automaticamente, evitando
        # duplicidade mesmo quando a confirmação da entrega falhar.
        raise RelatorioIndisponivel("Envio realizado, mas auditoria não confirmada; verificar no serviço.") from None


def executar(hoje=None, *, dry_run=False, session=None, snapshot=None):
    hoje = hoje or datetime.now(TZ).date()
    if isinstance(hoje, datetime):
        hoje = hoje.date()
    session = session or requests.Session()
    if snapshot is None:
        snapshot = coletar_snapshot_consistente(session, hoje)
    report = preparar_cancelamentos(snapshot, hoje)
    summary = {
        "status": "SIMULADO" if dry_run else "AGUARDANDO",
        "data": hoje.isoformat(), "snapshot_id": report["snapshot_id"],
        **report["resumo"],
    }
    if dry_run:
        return summary
    if not report["resumo"]["solicitacoes"] and not report["resumo"]["pedidos"]:
        summary["status"] = "SEM_CANCELAMENTOS"
        return summary

    to = _enderecos(os.getenv("MRP_CANCEL_EMAIL_TO"))
    cc = _enderecos(os.getenv("MRP_CANCEL_EMAIL_CC"))
    cc = [a for a in cc if a.lower() not in {b.lower() for b in to}]
    if not to:
        raise RelatorioIndisponivel("Destinatário de Suprimentos não configurado.")
    mode = os.getenv("MRP_CANCEL_DELIVERY_MODE", "").lower().strip()
    if mode not in ("smtp", "power_automate"):
        raise RelatorioIndisponivel("Transporte de e-mail não configurado.")
    url, key = _settings()
    if os.getenv("MRP_CANCEL_SEND_ENABLED") != "true":
        raise RelatorioIndisponivel("Envio real desabilitado até homologar destinatário e transporte.")
    recipient_hash = hashlib.sha256(";".join(sorted([*to, *cc])).lower().encode()).hexdigest()
    if not _registrar_envio(session, url, key, report, recipient_hash):
        summary["status"] = "JA_PROCESSADO_HOJE"
        return summary
    subject, text, body = _mensagem(report)
    try:
        if mode == "smtp":
            _smtp_send(report, to, cc, subject, text, body)
        else:
            _workflow_send(report, to, cc, subject, text, body, session)
    except Exception:
        # Por cautela, não reprocessar automaticamente tentativas com
        # resultado incerto; Suprimentos deve consultar o serviço de e-mail.
        _finalizar_envio(session, url, key, report, "VERIFICAR_FALHA")
        raise RelatorioIndisponivel("O transporte não confirmou o e-mail; verificar antes de reenviar.") from None
    _finalizar_envio(session, url, key, report, "ACEITO_PELO_TRANSPORTE")
    summary["status"] = "ACEITO_PELO_TRANSPORTE"
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Sem envio nem gravação de auditoria")
    args = parser.parse_args()
    try:
        result = executar(dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        # Não imprimir corpo de snapshot, e-mails, URLs assinadas ou token.
        print(json.dumps({"status": "NAO_ENVIADO", "tipo": type(exc).__name__,
                          "motivo": str(exc) if isinstance(exc, RelatorioIndisponivel)
                          else "Erro inesperado; consultar diagnóstico protegido."},
                         ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
