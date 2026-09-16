LAYOUT_PATCH = r"""
# =========================================================
# PADRÃO VISUAL — DIMENSÕES EFETIVAS DA GESTÃO DE ENTREGAS
# Replica também o override final de largura do app-base.
# Não altera lógica, cálculos ou persistência do MRP.
# =========================================================

_layout_old = '''.block-container {
    max-width: 1780px !important;
    padding-top: 3.2rem !important;
    padding-left: 2.7rem !important;
    padding-right: 2.7rem !important;
    padding-bottom: 3rem !important;
}
.setta-brand {'''

_layout_new = '''.block-container {
    max-width: 1780px !important;
    padding-top: 3.2rem !important;
    padding-left: 2.7rem !important;
    padding-right: 2.7rem !important;
    padding-bottom: 3rem !important;
    width: 100% !important;
}

[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] .main,
[data-testid="stMain"],
.stMain {
    width: 100% !important;
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

[data-testid="stAppViewContainer"] .main .block-container,
[data-testid="stMain"] .block-container,
.stMain .block-container {
    width: 100% !important;
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

.setta-brand {'''

if _layout_old not in _source:
    raise RuntimeError("Bloco visual principal não encontrado para padronização de largura.")
_source = _source.replace(_layout_old, _layout_new, 1)

# Cabeçalho/logo — mesmos valores do app-base.
_source = _source.replace(
    '''    min-height: 128px !important;
    display: flex !important;''',
    '''    min-height: 128px !important;
    display: flex !important;''',
    1,
)
_source = _source.replace(
    '''    margin: 0 0 2.55rem 0 !important;
    padding: 1.1rem 2rem !important;''',
    '''    margin: 0 0 2.55rem 0 !important;
    padding: 1.1rem 2rem !important;''',
    1,
)
_source = _source.replace(
    '''    max-width: 205px !important;
    max-height: 86px !important;''',
    '''    max-width: 205px !important;
    max-height: 86px !important;''',
    1,
)

# Título/subtítulo — mesmos valores do app-base.
_source = _source.replace(
    '''    font-size: 2.55rem !important;
    line-height: 1.08 !important;''',
    '''    font-size: 2.55rem !important;
    line-height: 1.08 !important;''',
    1,
)

# Métricas/balões — mesmas dimensões quando houver st.metric.
_metric_old = '''div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e7eaf0 !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
}'''
_metric_new = '''div[data-testid="stMetric"] {
    position: relative !important;
    min-height: 116px !important;
    padding: 16px 18px 15px 18px !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    background: #ffffff !important;
    box-shadow: 0 4px 16px rgba(15, 23, 42, .055) !important;
    overflow: hidden !important;
}
div[data-testid="stMetricLabel"] p {
    color: #475569 !important;
    font-size: .83rem !important;
    font-weight: 700 !important;
    line-height: 1.15 !important;
}
div[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    line-height: 1 !important;
    letter-spacing: -.035em !important;
}'''
if _metric_old in _source:
    _source = _source.replace(_metric_old, _metric_new, 1)
"""
