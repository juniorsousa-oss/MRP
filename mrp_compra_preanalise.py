"""Relatorio de pre-analise da Compra MRP por OP.

Exportacao exclusivamente consultiva, ANTES da liberacao da carga Protheus.
Nao altera exclusoes, aprovacoes, snapshots ou quantidades de origem.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from math import isclose, isfinite
import re
from typing import Iterable, Mapping

import pandas as pd

CAMPOS = {"produto", "qnt", "data", "psy", "cc", "op", "obs", "prioridade"}
OP_NAO_INFORMADA = "SEM OP VINCULADA"
PREANALISE_VERSAO = "2026-11-25-v4"


def _texto(valor) -> str:
    if valor is None or (not isinstance(valor, (list, dict)) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _excel_texto(valor) -> str:
    """Evita formula injection ao encaminhar planilhas para terceiros."""
    texto = _texto(valor)
    return "'" + texto if texto and texto[0] in ("=", "+", "-", "@", "\t", "\r") else texto


def op_relatorio(valor) -> str:
    """A OP ausente e identificada, nunca inventada."""
    value = _texto(valor)
    if re.fullmatch(r"\d+\.0+", value):
        value = value.split(".")[0]
    return value if value else OP_NAO_INFORMADA


def _codigo_material(valor) -> str:
    """Chave de material com oito dígitos, compatível com CADASTROS e MRP."""
    texto = _texto(valor)
    if re.fullmatch(r"\d+(?:\.0+)?", texto):
        texto = texto.split(".")[0]
    return texto.zfill(8) if texto.isdigit() and len(texto) <= 8 else texto


def _data_solicitacao(valor) -> pd.Timestamp:
    """Interpreta datas da base tratada/snapshot; não usa data de necessidade."""
    if isinstance(valor, (datetime, date, pd.Timestamp)):
        result = pd.Timestamp(valor)
        return result.tz_localize(None).normalize() if pd.notna(result) else pd.NaT
    texto = _texto(valor)
    if texto.upper() in {"", "NI", "N/A", "NAN", "NAT", "NONE"}:
        return pd.NaT
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return pd.Timestamp(datetime.strptime(texto, formato))
        except ValueError:
            pass
    # ISO com fuso e DD/MM/AAAA usam orientações distintas para o parser.
    iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}[T ]", texto))
    resultado = pd.to_datetime(texto, errors="coerce", dayfirst=not iso)
    if pd.isna(resultado):
        return pd.NaT
    resultado = pd.Timestamp(resultado)
    return resultado.tz_localize(None).normalize()


def _mapa_ultimas_solicitacoes(
    solicitacoes: pd.DataFrame | None,
) -> dict[tuple[str, str], str]:
    """Relaciona a data pelo par OP+material; nunca pega data de outra OP.

    ADMIN: rg oriundo do Relatório Geral Tratado.
    CONSULTA: demanda_projeto do snapshot, que já inclui Última Solicitação
    derivada da mesma fonte tratada na execução original.
    """
    if solicitacoes is None or solicitacoes.empty:
        return {}
    if "Projeto" not in solicitacoes.columns:
        raise ValueError("Relatório tratado sem coluna Projeto para última solicitação.")
    col_codigo = next(
        (c for c in ("Código", "Produto") if c in solicitacoes.columns), None
    )
    col_data = next(
        (c for c in ("Data Solicitação", "Última solicitação", "Última Solicitação")
         if c in solicitacoes.columns), None
    )
    if col_codigo is None or col_data is None:
        raise ValueError(
            "Relatório tratado/snapshot sem código e data da última solicitação."
        )

    frame = solicitacoes[["Projeto", col_codigo, col_data]].copy()
    frame["_op"] = frame["Projeto"].map(op_relatorio)
    frame["_codigo"] = frame[col_codigo].map(_codigo_material)
    frame["_data"] = frame[col_data].map(_data_solicitacao)
    frame = frame[
        frame["_op"].ne(OP_NAO_INFORMADA)
        & frame["_codigo"].ne("")
        & frame["_data"].notna()
    ]
    if frame.empty:
        return {}
    ultimas = frame.groupby(["_op", "_codigo"], sort=False)["_data"].max()
    return {chave: data.strftime("%d/%m/%Y") for chave, data in ultimas.items()}


def _pascoa(ano: int) -> date:
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    mes, resto = divmod(h + l - 7*m + 114, 31)
    return date(ano, mes, resto + 1)


def _dia_util(dia: date, adicionais: frozenset[date]) -> bool:
    # Mesmo calendário fixo adotado nas cobranças SETTA/Patos de Minas.
    fixos = {(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2),
             (11, 15), (11, 20), (12, 25), (5, 24), (6, 13), (8, 15)}
    pascoa = _pascoa(dia.year)
    return (dia.weekday() < 5 and (dia.month, dia.day) not in fixos
            and dia not in adicionais
            and dia not in {pascoa - timedelta(days=2), pascoa + timedelta(days=60)})


def _janela_analise(referencia=None, feriados_adicionais=()) -> frozenset[date]:
    hoje = pd.Timestamp.now(tz="America/Sao_Paulo") if referencia is None else pd.Timestamp(referencia)
    if hoje.tzinfo is not None:
        hoje = hoje.tz_convert("America/Sao_Paulo")
    dia = hoje.date()
    adicionais = frozenset(pd.Timestamp(x).date() for x in feriados_adicionais)
    anterior = dia - timedelta(days=1)
    while not _dia_util(anterior, adicionais):
        anterior -= timedelta(days=1)
    return frozenset((dia, anterior))


def _semana_ordem(valor):
    texto = _texto(valor).removesuffix(".0")
    match = re.fullmatch(r"(\d{4})[-/]?(\d{2})", texto)
    if not match:
        return None
    ano, semana = map(int, match.groups())
    return (ano, semana) if 1 <= semana <= 53 else None


def _recursos_e_falta(acao, necessidade):
    """Extrai recursos EFETIVAMENTE consumidos, não os saldos antes da linha."""
    numero = r"([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)"
    usados = falta = 0.0
    for parte in _texto(acao).split(";"):
        parte = parte.strip()
        if not parte:
            continue
        consumo = re.fullmatch(r"(?:Estoque|P\.C\.|Fabricação|S\.C\.)\s+" + numero + r"(?:\s+\(sem\. [^)]*\))?", parte, flags=re.I)
        pendente = re.fullmatch(r"CRIAR S\.C\.\s*" + numero + r"\s+para semana\s+\S+", parte, flags=re.I)
        if consumo:
            usados += float(consumo.group(1))
        elif pendente:
            falta += float(pendente.group(1))
        else:
            return None
    # Ação utiliza quantidades formatadas com :g; admitir só arredondamento.
    if not isfinite(usados + falta) or not isclose(usados + falta, necessidade, rel_tol=1e-5, abs_tol=1e-7):
        return None
    return usados, falta


def _prioridade_anterior(a, b) -> bool:
    # Critério real do motor: semana, Data CM, projeto. Empate de data não
    # comprova antecipação; não atribuir uma redistribuição por ordem de ID.
    if a["semana"] is None or b["semana"] is None:
        return False
    if a["semana"] != b["semana"]:
        return a["semana"] < b["semana"]
    # O motor usa na_position="last": Data CM válida vem antes de NI.
    if pd.notna(a["cm"]) and pd.isna(b["cm"]):
        return True
    return (pd.notna(a["cm"]) and pd.notna(b["cm"]) and a["cm"] < b["cm"])


def _redistribuicoes(alocacoes, mapa_solicitacoes, janela):
    """Reconstrução contrafactual do pool atual, sem afirmar reserva histórica.

    Créditos vêm apenas do consumo efetivo de solicitações recentes anteriores
    na ordem do MRP. Cada crédito é usado uma vez, na ordem das faltas antigas,
    inclusive projetos fora do filtro/exportação. Dados ambíguos ficam manuais.
    """
    colunas = {"Projeto", "Produto", "Semana de Necessidade", "Data CM",
               "Necessidade", "Ação"}
    if not isinstance(alocacoes, pd.DataFrame) or not colunas.issubset(alocacoes.columns):
        return {}
    materiais = {}
    for _, linha in alocacoes.iterrows():
        codigo = _codigo_material(linha["Produto"])
        op = op_relatorio(linha["Projeto"])
        if not codigo:
            continue
        necessidade = pd.to_numeric(linha["Necessidade"], errors="coerce")
        if pd.notna(necessidade) and necessidade == 0:
            continue  # cancelados/suspensos/resíduos zerados pelo motor.
        semana = _semana_ordem(linha["Semana de Necessidade"])
        cm = _data_solicitacao(linha["Data CM"])
        data = _data_solicitacao(mapa_solicitacoes.get((op, codigo), ""))
        recursos = (_recursos_e_falta(linha["Ação"], float(necessidade))
                    if pd.notna(necessidade) and isfinite(necessidade) and necessidade > 0 else None)
        materiais.setdefault(codigo, []).append({
            "op": op, "semana": semana, "cm": cm, "data": data,
            "recursos": recursos,
        })
    resultado = {}
    for codigo, itens in materiais.items():
        # Sem uma fotografia íntegra não presumir recursos nem ordem.
        if any(x["semana"] is None or x["recursos"] is None or x["op"] == OP_NAO_INFORMADA for x in itens):
            continue
        # A fonte tratada/snapshot é agrupada por projeto/material.
        # Se houver duplicidade, não duplicar o crédito nem inferir causalidade.
        if len({x["op"] for x in itens}) != len(itens):
            continue
        itens.sort(key=lambda x: (x["semana"], pd.isna(x["cm"]),
                                  x["cm"] if pd.notna(x["cm"]) else pd.Timestamp.max,
                                  x["op"]))
        creditos = []
        for item in itens:
            usados, falta = item["recursos"]
            recente = pd.notna(item["data"]) and item["data"].date() in janela
            if recente:
                if usados > 1e-7:
                    creditos.append([item, usados])
                continue
            if falta <= 1e-7:
                continue
            restante = falta
            atribuicoes = {}
            # Uma falta de origem desconhecida também consome crédito antes
            # de outras faltas; não recebe justificativa automática.
            for credito in creditos:
                doador, saldo = credito
                if restante <= 1e-7:
                    break
                if saldo <= 1e-7 or doador["op"] == item["op"]:
                    continue
                # Em caso de empate ou data desconhecida, reservar o recurso
                # na simulação, mas não atribuir causalidade.
                take = min(restante, saldo)
                credito[1] -= take
                restante -= take
                if (_prioridade_anterior(doador, item)
                        and pd.notna(item["data"])
                        and doador["data"] > item["data"]):
                    atribuicoes[doador["op"]] = atribuicoes.get(doador["op"], 0.0) + take
            if atribuicoes:
                resultado[(item["op"], codigo)] = (falta, atribuicoes)
    return resultado


def _mapa_macro(macro):
    campos = ("Saldo em Estoque", "Demanda", "P.C.", "S.C.", "Produzindo")
    if not isinstance(macro, pd.DataFrame) or not {"Código", *campos}.issubset(macro.columns):
        return {}
    out = {}
    for _, linha in macro.iterrows():
        codigo = _codigo_material(linha["Código"])
        valores = pd.to_numeric(linha[list(campos)], errors="coerce")
        if codigo and valores.notna().all() and all(isfinite(float(v)) and v >= 0 for v in valores):
            if codigo in out:
                out[codigo] = None
            else:
                out[codigo] = tuple(float(v) for v in valores)
    return {k: v for k, v in out.items() if v is not None}


def _mapa_faltas(alocacoes):
    campos = {"Projeto", "Produto", "Necessidade", "Ação"}
    if not isinstance(alocacoes, pd.DataFrame) or not campos.issubset(alocacoes.columns):
        return {}
    out, invalidos = {}, set()
    for _, linha in alocacoes.iterrows():
        codigo = _codigo_material(linha["Produto"])
        op = op_relatorio(linha["Projeto"])
        necessidade = pd.to_numeric(linha["Necessidade"], errors="coerce")
        if pd.notna(necessidade) and necessidade == 0:
            continue
        recurso = (_recursos_e_falta(linha["Ação"], float(necessidade))
                   if pd.notna(necessidade) and isfinite(necessidade) and necessidade > 0 else None)
        if recurso is None or op == OP_NAO_INFORMADA or not codigo or op in out.get(codigo, {}):
            invalidos.add(codigo)
            continue
        out.setdefault(codigo, {})[op] = (float(necessidade), *recurso)
    return {k: v for k, v in out.items() if k not in invalidos}


def _observacoes_perda_estoque(alocacoes, macro_atual, historico):
    """Compara fotografias consecutivas; não infere movimento físico do ERP."""
    if not isinstance(historico, dict):
        return {}
    atual = _mapa_macro(macro_atual)
    anterior = _mapa_macro(historico.get("macro_anterior"))
    referencia = _mapa_macro(historico.get("macro_referencia"))
    faltas = _mapa_faltas(alocacoes)
    faltas_ant = _mapa_faltas(historico.get("alocacoes_anterior"))
    faltas_ref = _mapa_faltas(historico.get("alocacoes_referencia"))
    out = {}
    for codigo, novo in atual.items():
        velho = anterior.get(codigo)
        # ADMIN deve corresponder ao snapshot atual; não misturar cálculos.
        if velho is None or novo != referencia.get(codigo) or faltas.get(codigo) != faltas_ref.get(codigo):
            continue
        if codigo not in faltas or codigo not in faltas_ant:
            continue
        perda = velho[0] - novo[0]
        reducao = velho[1] - novo[1]
        if perda <= 1e-7 or reducao < -1e-7 or perda <= reducao + 1e-7:
            continue
        if any(not isclose(a, b, rel_tol=1e-7, abs_tol=1e-7) for a,b in zip(velho[2:],novo[2:])):
            continue
        antes = max(0.0, velho[1] - velho[0] - sum(velho[2:]))
        depois = max(0.0, novo[1] - novo[0] - sum(novo[2:]))
        delta = depois - antes
        if delta <= 1e-7 or not isclose(delta, perda-reducao, rel_tol=1e-7, abs_tol=1e-7):
            continue
        # Confirmar que a falta global e as faltas por projeto se reconciliam.
        # TC/TP e origens sem OP não podem ser atribuídas por engano.
        fa, fb = faltas[codigo], faltas_ant[codigo]
        if not (isclose(sum(x[0] for x in fa.values()), novo[1], rel_tol=1e-7, abs_tol=1e-7)
                and isclose(sum(x[0] for x in fb.values()), velho[1], rel_tol=1e-7, abs_tol=1e-7)
                and isclose(sum(x[2] for x in fa.values()), depois, rel_tol=1e-7, abs_tol=1e-7)
                and isclose(sum(x[2] for x in fb.values()), antes, rel_tol=1e-7, abs_tol=1e-7)):
            continue
        aumentos = {op: x[2] - fb.get(op, (0,0,0))[2] for op,x in fa.items()
                    if x[2] - fb.get(op, (0,0,0))[2] > 1e-7}
        if not isclose(sum(aumentos.values()), delta, rel_tol=1e-7, abs_tol=1e-7):
            continue
        for op, qtd in aumentos.items():
            out[(op,codigo)] = (fa[op][2], f"REDUÇÃO DE ESTOQUE DE {perda:g} UN. COM REDUÇÃO DE DEMANDA DE {reducao:g} UN. — NECESSIDADE ADICIONAL DE {qtd:g} UN. (COMPARATIVO MRP)")
    return out


def _analise_previa(fonte, mapa_solicitacoes, alocacoes, referencia, feriados_adicionais, macro_atual=None, historico=None):
    janela = _janela_analise(referencia, feriados_adicionais)
    redistribuicoes = _redistribuicoes(alocacoes, mapa_solicitacoes, janela)
    perdas = _observacoes_perda_estoque(alocacoes, macro_atual, historico)
    pareceres = {}
    for (op, codigo), linhas in fonte.groupby(["OP", "Código"], sort=False):
        chave = (op, _codigo_material(codigo))
        data = _data_solicitacao(mapa_solicitacoes.get(chave, ""))
        if op == OP_NAO_INFORMADA or pd.isna(data):
            pareceres[chave] = ("VERIFICAR", "")
            continue
        if data.date() in janela:
            pareceres[chave] = ("NOVA DEMANDA", "")
            continue
        if data.date() > max(janela):
            pareceres[chave] = ("VERIFICAR", "")
            continue
        observacao = ""
        redistribuicao = redistribuicoes.get(chave)
        if redistribuicao:
            falta, atribuicoes = redistribuicao
            total_compra = float(linhas["Quantidade"].sum())
            # Evita vincular uma linha TC/TP ou uma compra de outro cálculo.
            if isclose(falta, total_compra, rel_tol=1e-5, abs_tol=1e-7):
                partes = [
                    f"PROJETO {projeto} (SOLICITAÇÃO: {mapa_solicitacoes[(projeto, chave[1])]}) CONSIDEROU O SALDO QUE ESTAVA PARA ESSE PROJETO ({qtd:g} UN.)"
                    for projeto, qtd in atribuicoes.items()
                ]
                observacao = " | ".join(partes) + " — INDÍCIO PELA ALOCAÇÃO ATUAL DO MRP"
                if sum(atribuicoes.values()) < falta - 1e-7:
                    observacao += "; REDISTRIBUIÇÃO PARCIAL"
        perda = perdas.get(chave)
        if not observacao and perda and isclose(perda[0], float(linhas["Quantidade"].sum()), rel_tol=1e-5, abs_tol=1e-7):
            observacao = perda[1]
        pareceres[chave] = ("DEMANDA" if observacao else "VERIFICAR", observacao)
    return pareceres


def _preencher_analise(frame, pareceres):
    chaves = [(op, _codigo_material(c)) for op, c in zip(frame["OP"], frame["Código"])]
    # Prioridade 1 é normal; grupos mistos continuam emergenciais.
    frame["Parecer do analista"] = [
        "OK" if _texto(p).removesuffix(".0") == "1"
        else pareceres.get(chave, ("VERIFICAR", ""))[0]
        if _texto(p).removesuffix(".0") == "2" else "VERIFICAR"
        for chave,p in zip(chaves,frame["Prioridade"])
    ]
    frame["Observações da análise"] = [
        _excel_texto(pareceres.get(chave, ("", ""))[1]) if _texto(p).removesuffix(".0") == "2" else "" for chave,p in zip(chaves,frame["Prioridade"])
    ]


def validar_pareceres_exportacao(planilhas, referencia=None):
    """Bloqueia exportação silenciosa de um relatório sem parecer esperado."""
    for aba in ("MATERIAIS OP", "DETALHE OP"):
        quadro = planilhas[aba]
        for _, linha in quadro.iterrows():
            prioridade = _texto(linha["Prioridade"]).removesuffix(".0")
            parecer = _texto(linha["Parecer do analista"])
            observacao = _texto(linha["Observações da análise"])
            validos = ({"OK"} if prioridade == "1" else
                       {"DEMANDA", "NOVA DEMANDA", "VERIFICAR"} if prioridade == "2"
                       else {"VERIFICAR"})
            if (parecer not in validos or (parecer == "DEMANDA" and not observacao)
                    or (parecer == "OK" and observacao)):
                raise ValueError(
                    f"{aba}: parecer automático ausente para OP {linha['OP']}, "
                    f"material {linha['Código']}. Atualize a sessão antes de exportar."
                )


def construir_relatorio_compra_por_op(
    compra: pd.DataFrame,
    descricoes: Mapping[str, str] | None = None,
    ops: Iterable[str] | None = None,
    solicitacoes: pd.DataFrame | None = None,
    alocacoes: pd.DataFrame | None = None,
    referencia=None,
    feriados_adicionais=(),
    macro_atual=None,
    historico=None,
) -> dict[str, pd.DataFrame]:
    """Produz 4 abas com rastreabilidade, sem gerar carga de importacao.

    A 'compra' recebida e a PREVIA APROVAVEL ja filtrada pelas exclusoes.
    Nenhuma agregacao entre OPs; a quantidade por material e somada apenas
    dentro da mesma OP. Preserva linhas individuais e datas no detalhamento.
    """
    faltantes = CAMPOS.difference(compra.columns)
    if faltantes:
        raise ValueError("Pre-analise: colunas de compra ausentes: " + ", ".join(sorted(faltantes)))

    fonte = compra.copy(deep=True)
    fonte["OP"] = fonte["op"].map(op_relatorio)
    fonte["Código"] = fonte["produto"].map(_texto)
    fonte["Descrição"] = fonte["Código"].map(
        lambda c: _excel_texto((descricoes or {}).get(c, ""))
    )
    # A fonte da última solicitação é EXCLUSIVAMENTE o Relatório Tratado
    # ou seu snapshot correspondente. A data da compra ("data") é a data
    # de necessidade e NÃO deve substituir a data da solicitação.
    mapa_solicitacoes = _mapa_ultimas_solicitacoes(solicitacoes)
    fonte["Última solicitação"] = [
        mapa_solicitacoes.get((op, _codigo_material(codigo)), "NI")
        for op, codigo in zip(fonte["OP"], fonte["Código"])
    ]
    # Valor mínimo por linha de OP, inclusive 0, apenas informativo.
    # A carga oficial escolhe o menor POSITIVO entre OPs ou 0 se nenhum.
    fonte["Valor mínimo encontrado"] = pd.to_numeric(
        fonte["vunit"] if "vunit" in fonte.columns else pd.Series(0,index=fonte.index),
        errors="coerce",
    ).fillna(0).clip(lower=0).astype(float)
    fonte["Quantidade"] = pd.to_numeric(fonte["qnt"], errors="coerce")
    if fonte["Quantidade"].isna().any() or (fonte["Quantidade"] < 0).any():
        raise ValueError("Pre-analise: quantidade ausente, negativa ou invalida.")
    # Analisa o universo antes de filtrar OPs. A consulta recebe o próprio snapshot.
    pareceres = _analise_previa(fonte, mapa_solicitacoes,
        alocacoes if alocacoes is not None else solicitacoes, referencia, feriados_adicionais,
        macro_atual, historico)
    filtro = {op_relatorio(x) for x in ops} if ops is not None else None
    if filtro is not None:
        fonte = fonte[fonte["OP"].isin(filtro)].copy()
    if fonte.empty:
        raise ValueError("Pre-analise: nenhuma linha de compra nas OPs selecionadas.")

    fonte["Data de necessidade"] = fonte["data"].map(_texto)
    fonte["Prioridade"] = fonte["prioridade"].map(lambda x: _texto(x).removesuffix(".0"))
    fonte["PSY"] = fonte["psy"].map(_excel_texto)
    fonte["Centro de custo"] = fonte["cc"].map(_excel_texto)
    fonte["Observação MRP"] = fonte["obs"].map(_excel_texto)
    fonte["_data_ordem"] = pd.to_datetime(
        fonte["Data de necessidade"], format="%d/%m/%Y", errors="coerce"
    )
    fonte["_indice_origem"] = range(len(fonte))

    # Preservar as quantidades/OPs de cada linha de origem mesmo quando duas
    # demandas compartilham material e data.
    detalhado = fonte.sort_values(
        ["OP", "Código", "_data_ordem", "_indice_origem"], kind="stable"
    )[[
        "OP", "Código", "Descrição", "Quantidade", "Valor mínimo encontrado",
        "Última solicitação", "Data de necessidade", "Prioridade", "PSY",
        "Centro de custo", "Observação MRP",
    ]].copy()
    _preencher_analise(detalhado, pareceres)

    def _unicos(series: pd.Series) -> str:
        valores = list(dict.fromkeys(
            _texto(x) for x in series if _texto(x)
        ))
        return " | ".join(valores)

    por_material = (
        fonte.groupby(["OP", "Código", "Descrição"], sort=True, dropna=False)
        .agg(
            Quantidade=("Quantidade", "sum"),
            Valor_minimo_encontrado=("Valor mínimo encontrado",
                lambda v: float(v[v>0].min()) if (v>0).any() else 0.0),
            Última_solicitação=("Última solicitação", "first"),
            Linhas=("Código", "size"),
            Data_mais_proxima=("_data_ordem", "min"),
            Prioridade=("Prioridade", lambda s: "2" if (s == "2").any()
                        else ("1" if (s == "1").any() else _unicos(s))),
            PSY=("PSY", _unicos),
            Centro_de_custo=("Centro de custo", _unicos),
        )
        .reset_index()
        .rename(columns={
            "Última_solicitação": "Última solicitação",
            "Valor_minimo_encontrado": "Valor mínimo encontrado",
            "Linhas": "Linhas de demanda",
            "Data_mais_proxima": "Primeira necessidade",
            "Centro_de_custo": "Centro de custo",
        })
    )
    por_material["Primeira necessidade"] = por_material[
        "Primeira necessidade"
    ].dt.strftime("%d/%m/%Y").fillna("")
    _preencher_analise(por_material, pareceres)

    resumo = (
        fonte.groupby("OP", sort=True)
        .agg(
            Linhas_de_demanda=("Código", "size"),
            Materiais_distintos=("Código", "nunique"),
            Prioridades_emergenciais=("Prioridade", lambda s: int((s == "2").sum())),
            Primeira_necessidade=("_data_ordem", "min"),
        )
        .reset_index()
        .rename(columns={
            "Linhas_de_demanda": "Linhas de demanda",
            "Materiais_distintos": "Materiais distintos",
            "Prioridades_emergenciais": "Linhas emergenciais",
            "Primeira_necessidade": "Primeira necessidade",
        })
    )
    resumo["Primeira necessidade"] = resumo[
        "Primeira necessidade"
    ].dt.strftime("%d/%m/%Y").fillna("")
    resumo["Parecer do analista"] = ""
    resumo["Observações da análise"] = ""

    orientacoes = pd.DataFrame([
        ("TIPO", "RELATÓRIO DE PRÉ-ANÁLISE — NÃO É CARGA DO PROTHEUS"),
        ("FINALIDADE", "Revisão da proposta de compra por OP antes da aprovação definitiva."),
        ("SITUAÇÃO", "Documento de consulta; nenhum pedido, SC ou liberação é gerado pelo download."),
        ("ESCOPO", "Somente itens aptos na prévia de compra, após as exclusões vigentes."),
        ("CRITÉRIO", "Cada OP mantém seus materiais e respectivas quantidades; não mistura OPs."),
        ("ÚLTIMA SOLICITAÇÃO", "Data máxima registrada no Relatório Geral Tratado por OP + código de material; NI indica ausência de correspondência."),
        ("DATAS DISTINTAS", "Última solicitação é a data de pedido do material; data de necessidade é a previsão de atendimento e não é usada como substituta."),
        ("DETALHAMENTO", "Aba DETALHE OP mantém cada linha, a última solicitação da origem e a data de necessidade da compra."),
        ("CONSOLIDAÇÃO", "Aba MATERIAIS OP soma quantidades somente por OP e produto."),
        ("PRIORIDADE", "2 = emergencial; 1 = normal, conforme cálculo original do MRP."),
        ("VALOR MÍNIMO", "Mostra valor por OP e material, inclusive zero; a carga unificada usa o menor preço positivo entre OPs ou zero quando todos forem zero."),
        ("SEM OP", "Demandas sem OP de origem são exibidas como SEM OP VINCULADA."),
        ("PARECER", "Prioridade 1 = OK, sem observação. Prioridade 2: NOVA DEMANDA para solicitação de hoje ou do último dia útil; DEMANDA quando antiga com motivo identificado; VERIFICAR quando não há justificativa ou os dados são insuficientes. Pareceres editáveis."),
        ("REDISTRIBUIÇÃO", "Observação estimada pelo consumo efetivo registrado na Ação do MRP e pela ordem de necessidade. Inclui a última solicitação do projeto responsável por material; não prova reserva anterior. Créditos não são duplicados. Revisar antes de aprovar."),
        ("VARIAÇÃO DE ESTOQUE", "Compara a fotografia atual com a anterior quando as quantidades de compra e as faltas por projeto se reconciliam. Não comprova consumo físico nem movimentação de estoque."),
        ("CALENDÁRIO", "Dias úteis: finais de semana e feriados do calendário SETTA/Patos de Minas. Pontos facultativos não são bloqueados automaticamente."),
        ("IMPORTANTE", "Não utilizar este arquivo na rotina de importação STSUP25 do Protheus."),
        ("VERSÃO DA PRÉ-ANÁLISE", PREANALISE_VERSAO),
        ("GERAÇÃO", datetime.now().strftime("%d/%m/%Y %H:%M")),
    ], columns=["Informação", "Orientação"])

    return {
        "INSTRUÇÕES": orientacoes,
        "RESUMO OP": resumo,
        "MATERIAIS OP": por_material,
        "DETALHE OP": detalhado,
    }
