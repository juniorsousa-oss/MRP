"""Validação de identificadores obrigatórios das Solicitações Avulsas."""
from __future__ import annotations

import re
import unicodedata

_INVALIDOS = {
    "n/a", "na", "n.a.", "nao se aplica", "s/n", "sem dados",
    "sem informacao", "nao informado", "nao sei", "aguardando",
    "pendente", "a definir", "a preencher", "teste", "test",
    "xxx", "xxxx", "xxxxx", "preencher depois",
    "preencher na entrega", "a preencher na entrega",
    "sera informado", "informar depois",
}
_PREFIXOS = re.compile(
    r"^(?:a preencher|preencher na entrega|preencher depois|a definir|"
    r"aguardando|pendente de|informar depois|sera informado|"
    r"nao informado)(?:\W|$)"
)


def identificacao_valida(valor: object, minimo: int = 1) -> bool:
    """Não aceita campos vazios nem promessas de preenchimento posterior.

    A validação não substitui conferência do CR e da autoridade aprovadora.
    """
    txt = unicodedata.normalize("NFKD", str(valor or "").strip().casefold())
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    txt = re.sub(r"\s+", " ", txt)
    if len(txt) < max(1, minimo) or txt in _INVALIDOS:
        return False
    if _PREFIXOS.match(txt) or re.fullmatch(r"[-_./x\s]+", txt):
        return False
    return True
