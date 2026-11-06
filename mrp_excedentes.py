"""Análise de excedentes de compra do MRP SETTA.

Motor independente do Streamlit para permitir validação de cancelamentos.
A coluna DIV continua interna para compatibilidade com snapshots antigos;
a apresentação e os arquivos exportados utilizam SF.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
from math import isfinite
from zoneinfo import ZoneInfo

import pandas as pd

EPS = 1e-8
COLUNAS = [
    "Código", "Descrição", "Tipo", "Documento", "Quantidade em aberto",
    "Quantidade cancelável", "Quantidade a manter", "SF do material",
    "Semana prevista", "Período previsto", "Início da semana",
    "Dias até início", "Prioridade", "Situação", "Observação",
]


def _numero(valor):
    try:
        n = float(valor)
        return n if isfinite(n) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _codigo(valor):
    try:
        if pd.isna(valor):
            return ""
        texto = str(valor).strip()
        if texto.endswith(".0"):
            texto = texto[:-2]
        return str(int(texto)) if texto.isdigit() else texto
    except (ValueError, TypeError):
        return ""


def _semana(valor, ano_fallback):
    if pd.isna(valor) or str(valor).strip() == "":
        return None, ""
    texto = str(valor).strip()
    try:
        if "-" in texto:
            ano, numero = (int(x) for x in texto.split("-", 1))
        else:
            n = int(float(texto))
            if n >= 200001:
                ano, numero = divmod(n, 100)
            else:
                ano, numero = ano_fallback, n
        if not (2000 <= ano <= 9999 and 1 <= numero <= 53):
            return None, ""
        primeiro = date(ano, 1, 1)
        domingo = primeiro + timedelta(days=(6 - primeiro.weekday()) % 7)
        inicio = domingo + timedelta(weeks=numero - 1)
        return inicio, f"{ano:04d}-{numero:02d}"
    except (ValueError, OverflowError, TypeError):
        return None, ""


def _prioridade(inicio, hoje):
    if inicio is None:
        return "INDEFINIDA", None
    dias = (inicio - hoje).days
    if dias <= 3:
        return "CRÍTICA", dias
    if dias <= 7:
        return "ALTA", dias
    if dias <= 15:
        return "MÉDIA", dias
    return "BAIXA", dias


def _data_local():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def _somar_evento(eventos, quando, valor):
    eventos[quando] = eventos.get(quando, 0.0) + valor


def _vazio():
    return pd.DataFrame(columns=COLUNAS)


def calcular_excedentes(mrp, compras, projecao, hoje=None):
    """Devolve (SC, PC) sem duplicar a quantidade cancelável.

    O limite global é SF>0. Cada exclusão simulada deve preservar
    todos os saldos projetados a partir da semana do documento.
    A análise é indicativa: não modifica P.C., S.C. ou estoque.
    """
    hoje = hoje or _data_local()
    if isinstance(hoje, datetime):
        hoje = hoje.date()
    if mrp is None or compras is None or len(mrp) == 0 or len(compras) == 0:
        return _vazio(), _vazio()

    base = mrp.copy()
    base["_chave"] = base["Código"].map(_codigo)
    cp = compras.copy()
    cp["_chave"] = cp["Código"].map(_codigo)
    pr = projecao.copy() if projecao is not None else pd.DataFrame()
    if not pr.empty and "Código" in pr:
        pr["_chave"] = pr["Código"].map(_codigo)

    linhas = {"S.C.": [], "P.C.": []}
    for _, mat in base.iterrows():
        chave = mat["_chave"]
        sf = _numero(mat.get("SF", mat.get("DIV", 0)))
        tipo = str(mat.get("Tipo", "")).strip().upper()
        if not chave or tipo == "II" or sf <= EPS:
            continue
        cx = cp[cp["_chave"] == chave]
        if cx.empty:
            continue

        documentos = []
        for indice, r in cx.iterrows():
            for sigla, col_qtd, col_sem, col_doc in (
                ("S.C.", "Quantidade S.C.", "Semana S.C.", "Nº S.C."),
                ("P.C.", "Quantidade P.C.", "Semana P.C.", "Nº P.C."),
            ):
                qtd = _numero(r.get(col_qtd, 0))
                if qtd <= EPS:
                    continue
                data, semana = _semana(r.get(col_sem), hoje.year)
                num = str(r.get(col_doc, "") or "").strip()
                if num.endswith(".0"):
                    num = num[:-2]
                if num.lower() in ("nan", "none"):
                    num = ""
                documentos.append({
                    "sigla": sigla, "qtd": qtd, "numero": num,
                    "inicio": data, "semana": semana, "origem": str(indice),
                    # P.C. sem semana não integra a coluna P.C. do MRP.
                    "integra": sigla == "S.C." or data is not None,
                })
        if not documentos:
            continue

        pc_total = sum(d["qtd"] for d in documentos if d["sigla"] == "P.C." and d["integra"])
        sc_total = sum(d["qtd"] for d in documentos if d["sigla"] == "S.C.")
        conciliado = (
            abs(pc_total - _numero(mat.get("P.C.", 0))) <= EPS
            and abs(sc_total - _numero(mat.get("S.C.", 0))) <= EPS
        )

        eventos = {}
        pmat = pr[pr["_chave"] == chave] if not pr.empty and "_chave" in pr else pd.DataFrame()
        if len(pmat):
            demanda_projetada = 0.0
            fabricacao_projetada = 0.0
            for _, p in pmat.iterrows():
                quando, _ = _semana(p.get("Semana"), hoje.year)
                if quando is None:
                    conciliado = False
                    continue
                quando = max(quando, hoje)
                demanda = _numero(p.get("Demanda", 0))
                fabricacao = _numero(p.get("Produzindo", 0))
                demanda_projetada += demanda
                fabricacao_projetada += fabricacao
                _somar_evento(eventos, quando, fabricacao - demanda)
            if (
                abs(demanda_projetada - _numero(mat.get("Demanda", 0))) > EPS
                or abs(fabricacao_projetada - _numero(mat.get("Produzindo", 0))) > EPS
            ):
                # Em históricos incompletos, não autorizar cancelamentos com
                # base numa projeção que não concilia com o saldo final.
                conciliado = False
        else:
            # Sem projeção temporal, a demanda deve ser protegida imediatamente.
            _somar_evento(
                eventos, hoje,
                _numero(mat.get("Produzindo", 0)) - _numero(mat.get("Demanda", 0)),
            )

        datas_previstas = [max(d["inicio"], hoje) for d in documentos if d["inicio"]]
        data_sem_previsao = max([hoje, *datas_previstas, *eventos.keys()]) + timedelta(days=7)

        for d in documentos:
            d["efetiva"] = max(d["inicio"], hoje) if d["inicio"] else data_sem_previsao
            if d["integra"]:
                _somar_evento(eventos, d["efetiva"], d["qtd"])

        # Teste de reconciliação adicional entre a linha do MRP e o livro de eventos.
        saldo = _numero(mat.get("Saldo em Estoque", 0))
        saldos = {}
        for quando in sorted(eventos):
            saldo += eventos[quando]
            saldos[quando] = saldo
        if abs(saldo - sf) > EPS:
            conciliado = False

        disponivel = sf
        ordem = sorted(
            documentos,
            key=lambda d: (d["efetiva"], d["numero"], d["origem"], d["sigla"]),
        )
        for d in ordem:
            inicio = d["inicio"]
            prioridade, dias = _prioridade(inicio, hoje)
            sem_previsao = inicio is None
            sem_numero = not d["numero"]
            pode_alocar = conciliado and d["integra"] and not sem_numero
            futuro = [s for quando, s in saldos.items() if quando >= d["efetiva"]]
            menor_saldo = min(futuro) if futuro else 0.0
            qtd = max(0.0, min(d["qtd"], disponivel, menor_saldo)) if pode_alocar else 0.0
            if qtd < EPS:
                qtd = 0.0

            if qtd:
                disponivel -= qtd
                for quando in saldos:
                    if quando >= d["efetiva"]:
                        saldos[quando] -= qtd

            if not conciliado:
                situacao = "DIVERGÊNCIA — CONFERIR BASES"
                obs = "Saldo, documentos ou projeção não conciliam com o MRP; sem recomendação automática."
            elif not d["integra"]:
                situacao = "VALIDAR SEMANA"
                obs = "P.C. sem semana não compõe a SF do MRP; verificar a base de compras."
            elif sem_numero:
                situacao = "VALIDAR DOCUMENTO"
                obs = "Documento sem identificação; não recomendar cancelamento."
            elif sem_previsao:
                situacao = "VALIDAR PREVISÃO"
                obs = "S.C. sem semana: quantidade potencial, sujeita à confirmação da previsão."
            elif qtd >= d["qtd"] - EPS:
                situacao = "CANCELAMENTO TOTAL — AVALIAR"
                obs = "Proposta condicionada à confirmação de Suprimentos."
            elif qtd > EPS:
                situacao = "CANCELAMENTO PARCIAL — AVALIAR"
                obs = "Manter a quantidade necessária; confirmar com Suprimentos."
            else:
                situacao = "MANTER"
                obs = "Não foi identificada quantidade cancelável com segurança."

            linhas[d["sigla"]].append({
                "Código": mat.get("Código", ""),
                "Descrição": mat.get("Descrição", ""),
                "Tipo": mat.get("Tipo", ""),
                "Documento": d["numero"] or "NÃO INFORMADO",
                "Quantidade em aberto": d["qtd"],
                "Quantidade cancelável": qtd,
                "Quantidade a manter": max(0.0, d["qtd"] - qtd),
                "SF do material": sf,
                "Semana prevista": d["semana"] or "SEM PREVISÃO",
                "Período previsto": (
                    f"{inicio:%d/%m/%Y} a {inicio + timedelta(days=6):%d/%m/%Y}"
                    if inicio else "SEM PREVISÃO"
                ),
                "Início da semana": inicio.strftime("%d/%m/%Y") if inicio else "",
                "Dias até início": dias,
                "Prioridade": prioridade,
                "Situação": situacao,
                "Observação": obs,
            })

    ordem_prioridade = {"CRÍTICA": 0, "ALTA": 1, "MÉDIA": 2, "BAIXA": 3, "INDEFINIDA": 4}
    resultado = []
    for sigla in ("S.C.", "P.C."):
        out = pd.DataFrame(linhas[sigla], columns=COLUNAS)
        if not out.empty:
            out["_ordem"] = out["Prioridade"].map(ordem_prioridade).fillna(9)
            out["_dias"] = pd.to_numeric(out["Dias até início"], errors="coerce").fillna(999999)
            out = out.sort_values(["_ordem", "_dias", "Código", "Documento"], kind="stable")
            out = out[COLUNAS].reset_index(drop=True)
        resultado.append(out)
    return tuple(resultado)


def _excel_excedentes(sc, pc, hoje):
    arquivo = BytesIO()
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        for nome, frame in (("Solicitações SC", sc), ("Pedidos PC", pc)):
            frame.to_excel(writer, sheet_name=nome, index=False)
            aba = writer.sheets[nome]
            aba.freeze_panes = "A2"
            aba.auto_filter.ref = aba.dimensions
            for coluna in aba.columns:
                letra = coluna[0].column_letter
                largura = min(62, max(14, max(len(str(c.value or "")) for c in coluna) + 2))
                aba.column_dimensions[letra].width = largura
        pd.DataFrame([
            {"Campo": "Gerado em", "Informação": hoje.strftime("%d/%m/%Y")},
            {"Campo": "Critério", "Informação": "SF positiva, Tipo diferente de II, respeito à projeção cronológica"},
            {"Campo": "Prioridade", "Informação": "Proximidade do início da semana prevista; não é data exata de entrega"},
            {"Campo": "Controle", "Informação": "Relatório indicativo; não cancela documentos automaticamente"},
        ]).to_excel(writer, sheet_name="Critérios", index=False)
    return arquivo.getvalue()


def exibir_analise_excedentes(mrp, compras, projecao, prefixo, data_snapshot=None):
    """Painel Streamlit, com S.C. e P.C. independentes e Excel para conferência."""
    import streamlit as st

    chave = f"mrp_excedentes_aberto_{prefixo}"
    if st.button("ANÁLISE DE EXCEDENTES", key=f"mrp_excedentes_botao_{prefixo}", use_container_width=True):
        st.session_state[chave] = not st.session_state.get(chave, False)
    if not st.session_state.get(chave, False):
        return

    st.markdown("### ANÁLISE DE EXCEDENTES — S.C. E P.C.")
    st.caption(
        "Análise indicativa de cancelamentos. A prioridade considera o INÍCIO DA SEMANA "
        "prevista, pois a base MRP não contém o dia exato de entrega."
    )
    if data_snapshot:
        instante = pd.to_datetime(data_snapshot, errors="coerce", utc=True)
        if pd.notna(instante):
            local = instante.tz_convert("America/Sao_Paulo")
            st.caption(f"MRP considerado: {local:%d/%m/%Y %H:%M} (Brasília)")
            if (_data_local() - local.date()).days >= 1:
                st.warning("O MRP consultado não foi atualizado hoje. Atualize a base antes de solicitar cancelamentos.")

    sc, pc = calcular_excedentes(mrp, compras, projecao)
    candidatos = pd.concat([sc, pc], ignore_index=True)
    validos = candidatos[candidatos["Quantidade cancelável"] > EPS] if not candidatos.empty else candidatos
    a, b, c = st.columns(3)
    a.metric("Documentos com excedentes", len(validos))
    b.metric("S.C. com excedentes", int((sc["Quantidade cancelável"] > EPS).sum()))
    c.metric("P.C. com excedentes", int((pc["Quantidade cancelável"] > EPS).sum()))
    mostrar_todos = st.checkbox(
        "Exibir também os documentos sem quantidade cancelável e com inconsistências",
        value=False, key=f"mrp_excedentes_todos_{prefixo}",
    )

    aba_sc, aba_pc = st.tabs(["SOLICITAÇÕES DE COMPRA (S.C.)", "PEDIDOS DE COMPRA (P.C.)"])
    for aba, frame, nome in ((aba_sc, sc, "S.C."), (aba_pc, pc, "P.C.")):
        with aba:
            visivel = frame if mostrar_todos else frame[
                (frame["Quantidade cancelável"] > EPS)
                | frame["Situação"].str.startswith(("VALIDAR", "DIVERGÊNCIA"), na=False)
            ]
            if visivel.empty:
                st.info(f"Nenhuma {nome} com excedente cancelável identificada.")
            else:
                st.dataframe(visivel, use_container_width=True, hide_index=True)
                st.caption(
                    "Quantidades são sugestões para validação de Suprimentos; "
                    "cancelamentos parciais preservam a quantidade necessária."
                )
    st.download_button(
        "BAIXAR ANÁLISE DE EXCEDENTES — EXCEL",
        data=_excel_excedentes(sc, pc, _data_local()),
        file_name=f"MRP_Excedentes_{_data_local():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"mrp_excedentes_excel_{prefixo}",
        use_container_width=True,
    )
    st.caption("Envio automático de e-mail: não ativado nesta etapa de validação.")
