LAYOUT_PATCH = r"""
# =========================================================
# PADRÃO VISUAL — DIMENSÕES EXATAS DA GESTÃO DE ENTREGAS
# Fonte de referência: streamlit_app.py enviado em 16/09/2026.
# Não altera lógica, cálculos ou persistência do MRP.
# =========================================================

# O runtime do MRP já possuía quase todas as dimensões do app de referência.
# Este bloco garante explicitamente os mesmos valores e desfaz o ajuste
# compacto aplicado anteriormente.
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
    max-width: 1780px !important;
    padding-top: 3.2rem !important;
    padding-left: 2.7rem !important;
    padding-right: 2.7rem !important;
    padding-bottom: 3rem !important;
    width: 100% !important;
}'''
    ),
]

for _old_layout, _new_layout in _layout_replacements:
    if _old_layout in _source:
        _source = _source.replace(_old_layout, _new_layout, 1)

# Cabeçalho/logo — exatamente as dimensões do app de referência.
# A classe do MRP é .setta-brand; no app-base a equivalente é .setta-logo-card.
_source = _source.replace(
    '''.setta-brand {
    width: 100% !important;
    min-height: 128px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #ffffff !important;
    border: 1px solid #e5e8ee !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(24, 39, 75, 0.08) !important;
    box-sizing: border-box !important;
    margin: 0 0 2.55rem 0 !important;
    padding: 1.1rem 2rem !important;
}''',
    '''.setta-brand {
    width: 100% !important;
    min-height: 128px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #ffffff !important;
    border: 1px solid #e5e8ee !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(24, 39, 75, 0.08) !important;
    box-sizing: border-box !important;
    margin: 0 0 2.55rem 0 !important;
    padding: 1.1rem 2rem !important;
}''',
    1,
)

_source = _source.replace(
    '''.setta-brand-logo img {
    display: block !important;
    width: auto !important;
    height: auto !important;
    max-width: 205px !important;
    max-height: 86px !important;
    object-fit: contain !important;
    margin: 0 !important;
}''',
    '''.setta-brand-logo img {
    display: block !important;
    width: auto !important;
    height: auto !important;
    max-width: 205px !important;
    max-height: 86px !important;
    object-fit: contain !important;
    margin: 0 !important;
}''',
    1,
)

# Título/subtítulo — mesmas proporções do app-base.
_source = _source.replace(
    '''.app-title {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 2.55rem !important;
    line-height: 1.08 !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: #050505 !important;
}''',
    '''.app-title {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 2.55rem !important;
    line-height: 1.08 !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: #050505 !important;
}''',
    1,
)

_source = _source.replace(
    '''.app-subtitle {
    margin-top: 0.72rem !important;
    margin-bottom: 0 !important;
    font-size: 0.94rem !important;
    color: #4f5661 !important;
}''',
    '''.app-subtitle {
    margin-top: 0.72rem !important;
    margin-bottom: 0 !important;
    font-size: 0.94rem !important;
    color: #4f5661 !important;
}''',
    1,
)

# Cards/"balões" — replica a caixa KPI do app-base (116 px).
_source = _source.replace(
    '''div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e7eaf0 !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
}''',
    '''div[data-testid="stMetric"] {
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
}''',
    1,
)

# Responsivo — mantém exatamente o padrão já existente no app-base.
_source = _source.replace(
    '''        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;''',
    '''        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;''',
    1,
)
"""
