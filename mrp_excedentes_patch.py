EXCEDENTES_PATCH = r"""
# Etapa piloto: excedentes de P.C. e S.C., sem envio de e-mails.
# Mantemos DIV na estrutura de dados para não romper histórico e comparativos.
_import = "import streamlit as st\n"
if _source.count(_import) != 1:
    raise RuntimeError("Excedentes: import do Streamlit não localizado.")
_source = _source.replace(
    _import,
    _import + "from mrp_excedentes import exibir_analise_excedentes\n",
    1,
)

# Renomeação somente de APRESENTAÇÃO. Os cálculos originais continuam usando DIV.
_tab_retorno = "    return st.dataframe(data,*args,**kwargs)"
if _source.count(_tab_retorno) != 1:
    raise RuntimeError("Excedentes: tabela adaptativa não localizada.")
_source = _source.replace(
    _tab_retorno,
    '''    if (hasattr(data,"columns") and "DIV" in data.columns
            and {"Código","Saldo em Estoque","Demanda"}.issubset(set(data.columns))):
        data=data.rename(columns={"DIV":"SF"})
        if kwargs.get("column_order") is not None:
            kwargs["column_order"]=["SF" if c=="DIV" else c for c in kwargs["column_order"]]
        if kwargs.get("column_config") is not None and "DIV" in kwargs["column_config"]:
            kwargs["column_config"]=dict(kwargs["column_config"])
            kwargs["column_config"]["SF"]=kwargs["column_config"].pop("DIV")
    return st.dataframe(data,*args,**kwargs)''',
    1,
)

_consulta = '        render_validacao_compra_mrp(comp,"consulta",mg)'
if _source.count(_consulta) != 1:
    raise RuntimeError("Excedentes: integração da consulta de compras não localizada.")
_source = _source.replace(
    _consulta,
    _consulta + '\n    exibir_analise_excedentes(mg,compras,proj,"consulta",snap.get("created_at"))',
    1,
)

_admin = '    render_validacao_compra_mrp(compras_mrp_export,"admin",cad)'
if _source.count(_admin) != 1:
    _pistas=[linha[:250] for linha in _source.splitlines() if "render_validacao_compra_mrp" in linha or "ANÁLISE DE COMPRA" in linha]
    raise RuntimeError("Excedentes: integração ADMIN não localizada: "+repr(_pistas[:12]))
_source = _source.replace(
    _admin,
    _admin + '\nexibir_analise_excedentes(macro,cp,proj,"admin")',
    1,
)

# O título SF é aplicado também aos relatórios principais gerados em Excel e CSV.
# Não modificar macro, mg nem os snapshots históricos.
_sf_export = '''def _mrp_geral_export_sf(frame):
    if frame is None:
        return frame
    return frame.rename(columns={"DIV":"SF"}) if hasattr(frame,"columns") else frame

'''
_anchor = "def render_consulta_view():"
if _source.count(_anchor) != 1:
    raise RuntimeError("Excedentes: função de consulta não localizada.")
_source = _source.replace(_anchor, _sf_export + _anchor, 1)

for _antigo, _novo in [
    ('"MRP_Geral": mg,', '"MRP_Geral": _mrp_geral_export_sf(mg),'),
    ('"MRP_Geral":export_macro,', '"MRP_Geral":_mrp_geral_export_sf(export_macro),'),
    ('csv_bytes(mg)', 'csv_bytes(_mrp_geral_export_sf(mg))'),
    ('csv_bytes(export_macro)', 'csv_bytes(_mrp_geral_export_sf(export_macro))'),
]:
    if _antigo not in _source:
        raise RuntimeError(f"Excedentes: exportação MRP não localizada: {_antigo}")
    _source = _source.replace(_antigo, _novo, 1)
"""
