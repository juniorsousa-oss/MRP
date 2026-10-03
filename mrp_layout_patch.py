LAYOUT_PATCH = r"""
# =========================================================
# MRP — AJUSTE DOS CARDS DE MÉTRICAS
# Moldura, cabeçalho e menus pertencem exclusivamente ao SETTA_UI_V1_PATCH.
# =========================================================

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
