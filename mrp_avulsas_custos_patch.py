AVULSAS_CUSTOS_PATCH = r'''
# MRP SETTA - custo de referencia do CADASTROS: VALOR DA ULTIMA COMPRA.
# Regra acordada: valor vazio, nao numerico ou nao encontrado recebe R$ 0,00.
_cost_anchor='    cad=cad[_cad_ok].copy()'
if _source.count(_cost_anchor)!=2:
    raise RuntimeError("Custos avulsos: carregadores CADASTROS nao encontrados.")
_cost_prefix="""    # CADASTROS: colunas B=Codigo e M=Ult. Preco (indice 12), linha 2=cabecalho.
    # Ausente, vazio, texto nao numerico ou valor invalido => R$ 0,00.
    def _mrp_cadastro_ultimo_preco(v):
        import math as _math_preco
        if v is None or pd.isna(v):
            return 0.0
        if isinstance(v,(int,float)):
            preco=float(v)
            return preco if _math_preco.isfinite(preco) and preco>=0 else 0.0
        t=str(v).strip().replace("R$","").replace(" ","")
        if not t:
            return 0.0
        if "," in t:
            t=t.replace(".","").replace(",",".")
        try:
            preco=float(t)
        except (ValueError,TypeError):
            return 0.0
        return preco if _math_preco.isfinite(preco) and preco>=0 else 0.0
    cad["Valor Última Compra"]=(
        _cad_raw.iloc[:,12].map(_mrp_cadastro_ultimo_preco)
        if _cad_raw.shape[1]>12 else 0.0
    )
"""
_source=_source.replace(_cost_anchor,_cost_prefix+_cost_anchor)
# Nova assinatura de calculo: obriga nova fotografia com o valor da ultima compra.
if _source.count("MRP-CALC-V4-COMPRA-TCTP-GRUPO")!=1:
    raise RuntimeError("Custos avulsos: assinatura do MRP nao localizada.")
_source=_source.replace(
    "MRP-CALC-V4-COMPRA-TCTP-GRUPO",
    "MRP-CALC-V6-CUSTO-CADASTROS-COLUNA-M",
    1,
)
'''
