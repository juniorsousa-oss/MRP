ANO_SEMANA_PATCH = r'''
# ADEQUAÇÃO ANO-SEMANA NO MOTOR OPERACIONAL (executada depois dos outros patches)
import re as _sem_re

def _sem_trocar(antigo, novo, rotulo):
    if _source.count(antigo) != 1:
        raise RuntimeError(f"MRP ano-semana: trecho inesperado em {rotulo}.")
    return _source.replace(antigo, novo, 1)

_semana_helpers = '''
def semana_id(valor):
    """Representação interna numérica AAAASS, preservando a ordenação cronológica."""
    if pd.isna(valor) or str(valor).strip() in ("", "nan", "None"):
        return float("nan")
    texto = str(valor).strip()
    encontrado = re.fullmatch(r"(\\d{4})-(\\d{1,2})", texto)
    if encontrado:
        ano, semana = int(encontrado.group(1)), int(encontrado.group(2))
    else:
        try:
            numero = float(texto)
            if not numero.is_integer():
                raise ValueError()
            chave = int(numero)
            if 1 <= chave <= 53:
                raise ValueError("Relatório antigo sem ano na semana: gere a base tratada novamente no Conversor MRP.")
            ano, semana = divmod(chave, 100)
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"Semana inválida na base MRP: {texto!r}. Use o formato AAAA-SS.") from exc
    if not 2000 <= ano <= 9999 or not 1 <= semana <= 53:
        raise ValueError(f"Ano e semana inválidos: {texto!r}.")
    return ano * 100 + semana


def formatar_semana(valor):
    if pd.isna(valor):
        return ""
    txt = str(valor).strip()
    if txt.upper() in ("", "NN", "N/A", "A DEFINIR"):
        return txt
    try:
        n = int(float(txt))
    except (ValueError, TypeError, OverflowError):
        return txt
    return f"{n // 100:04d}-{n % 100:02d}" if n >= 200001 else txt

'''
_source = _sem_trocar("def num(s): return pd.to_numeric(s, errors=\"coerce\")\n",
    _semana_helpers + "def num(s): return pd.to_numeric(s, errors=\"coerce\")\n",
    "funções de ano e semana")

_source = _sem_trocar(
    'df[name]=num(df.iloc[:,pos])',
    'df[name]=df.iloc[:,pos].map(semana_id) if name.startswith("Semana ") else num(df.iloc[:,pos])',
    "leitura das semanas do TC/TP"
)

_inicio = _source.index("def periodo_semana(semana,ano=2026):")
_fim = _source.index("def formatar_data_br(s):", _inicio)
_source = _source[:_inicio] + '''
def _inicio_semana(semana, ano=2026):
    """Domingo inicial da semana; aceita AAAASS e o formato antigo 1 a 53."""
    if pd.isna(semana):
        return None
    texto = str(semana).strip()
    achou = re.fullmatch(r"(\\d{4})-(\\d{1,2})", texto)
    if achou:
        ano, numero = int(achou.group(1)), int(achou.group(2))
    else:
        try:
            chave = int(float(texto))
        except (TypeError, ValueError, OverflowError):
            return None
        if chave >= 200001:
            ano, numero = divmod(chave, 100)
        else:
            numero = chave  # compatibilidade com históricos de 2026
    if not (2000 <= ano <= 9999 and 1 <= numero <= 53):
        return None
    primeiro = date(ano, 1, 1)
    primeiro += timedelta(days=(6 - primeiro.weekday()) % 7)
    return primeiro + timedelta(weeks=numero - 1)


def periodo_semana(semana, ano=2026):
    domingo = _inicio_semana(semana, ano)
    if domingo is None:
        return ""
    return f"{domingo:%d/%m/%Y} a {domingo + timedelta(days=6):%d/%m/%Y}"


def ultimo_dia_util_semana(semana, ano=2026):
    domingo = _inicio_semana(semana, ano)
    if domingo is None:
        return ""
    return f"{domingo + timedelta(days=5):%d/%m/%Y}"

''' + _source[_fim:]

_source = _sem_trocar(
    '"Semana":num(gr.iloc[:,15]),',
    '"Semana":gr.iloc[:,15].map(semana_id),',
    "ano da semana do Relatório Geral"
)
_source = _sem_trocar(
    '"Semana S.C.":num(cr.iloc[:,5])',
    '"Semana S.C.":cr.iloc[:,5].map(semana_id)',
    "ano da semana de S.C."
)
_source = _sem_trocar(
    '"Semana P.C.":num(cr.iloc[:,11])',
    '"Semana P.C.":cr.iloc[:,11].map(semana_id)',
    "ano da semana de P.C."
)
# Todos os filtros semanais operam sobre AAAASS; os campos de quantidade não mudam.
if _source.count(".between(1,53)") < 4:
    raise RuntimeError("MRP ano-semana: filtros de semanas insuficientes para atualização.")
_source = _source.replace(".between(1,53)", ".between(200001,999953)")
_source = _sem_trocar(
    'rg_semanas=num(rg_mrp["Semana"]).dropna(); rg_semanas=rg_semanas[(rg_semanas>=1)&(rg_semanas<=53)]',
    'rg_semanas=num(rg_mrp["Semana"]).dropna(); rg_semanas=rg_semanas[(rg_semanas>=200001)&(rg_semanas<=999953)]',
    "semana atual do Relatório Geral"
)
_source = _sem_trocar(
    'v=num(s).dropna(); v=v[(v>=1)&(v<=53)]',
    'v=num(s).dropna(); v=v[(v>=200001)&(v<=999953)]',
    "semana atual das outras bases"
)
_source = _sem_trocar(
    'st.number_input("Semana atual",min_value=1,max_value=53,value=semana_atual,disabled=True)',
    'st.text_input("Semana atual",value=formatar_semana(semana_atual),disabled=True)',
    "indicador da semana atual"
)
# A projeção pula semanas sem alteração. O saldo passa diretamente para o evento seguinte.
_source = _sem_trocar(
    'g0=g0.sort_values("Semana"); ultima_semana=int(g0["Semana"].max()); g=pd.DataFrame({"Semana":range(semana_atual,ultima_semana+1)}).merge(g0,on="Semana",how="left");',
    'g0=g0.sort_values("Semana"); g=g0.copy();',
    "projeção sem semanas vazias"
)
# Apresentação dos rótulos, sem transformar os dados numéricos de cálculo/histórico.
_display_anchor = '    out=df.copy()\n    colunas_quantidade={'
_display_replacement = '''    out=df.copy()
    for col_semana in ["Semana", "Semana de Necessidade", "Semana de Atendimento",
                       "Semana P.C.", "Semana S.C.", "Semana Entrega"]:
        if col_semana in out.columns:
            out[col_semana] = out[col_semana].map(formatar_semana)
    colunas_quantidade={'''
_source = _sem_trocar(_display_anchor, _display_replacement, "exibição do ano e semana")

'''
