LAYOUT_PATCH = r"""
# =========================================================
# PADRÃO VISUAL — REFERÊNCIA: GESTÃO DE ENTREGAS
# Ajusta somente espaçamentos, cabeçalho, título e KPIs.
# =========================================================

_layout_replacements = [
    (
        '''.block-container {
    max-width: 1780px !important;
    padding-top: 3.2rem !important;
    padding-left: 2.7rem !important;
    padding-right: 2.7rem !important;
    padding-bottom: 3rem !important;
}''',
        '''.block-container {
    max-width: 100% !important;
    padding-top: 1.35rem !important;
    padding-left: 1.55rem !important;
    padding-right: 1.55rem !important;
    padding-bottom: 2rem !important;
}'''
    ),
    (
        '''    min-height: 128px !important;''',
        '''    min-height: 96px !important;'''
    ),
    (
        '''    margin: 0 0 2.55rem 0 !important;''',
        '''    margin: 0 0 1.45rem 0 !important;'''
    ),
    (
        '''    padding: 1.1rem 2rem !important;''',
        '''    padding: .75rem 1.4rem !important;'''
    ),
    (
        '''    max-width: 205px !important;
    max-height: 86px !important;''',
        '''    max-width: 170px !important;
    max-height: 62px !important;'''
    ),
    (
        '''    font-size: 2.55rem !important;''',
        '''    font-size: 2rem !important;'''
    ),
    (
        '''    margin-top: 0.72rem !important;
    margin-bottom: 0 !important;
    font-size: 0.94rem !important;''',
        '''    margin-top: .38rem !important;
    margin-bottom: .75rem !important;
    font-size: .86rem !important;'''
    ),
    (
        '''    margin: 1.05rem 0 1.65rem 0 !important;
    padding: 1rem 1.05rem !important;''',
        '''    margin: .72rem 0 1.05rem 0 !important;
    padding: .72rem .9rem !important;'''
    ),
    (
        '''    border-radius: 9px !important;
    font-size: 0.98rem !important;''',
        '''    border-radius: 8px !important;
    font-size: .88rem !important;'''
    ),
    (
        '''div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e7eaf0 !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
}''',
        '''div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e7eaf0 !important;
    border-radius: 11px !important;
    padding: .62rem .78rem !important;
    min-height: 78px !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, .045) !important;
}
div[data-testid="stMetricLabel"] p {
    font-size: .74rem !important;
    line-height: 1.15 !important;
}
div[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    line-height: 1 !important;
}'''
    ),
]

for _old_layout, _new_layout in _layout_replacements:
    if _old_layout in _source:
        _source = _source.replace(_old_layout, _new_layout, 1)

# Ajuste responsivo: mantém laterais enxutas em telas menores.
_source = _source.replace(
    '''        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;''',
    '''        padding-top: 1.1rem !important;
        padding-left: .8rem !important;
        padding-right: .8rem !important;''',
    1,
)
"""
