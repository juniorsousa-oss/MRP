AVULSAS_CUSTOS_PATCH = r'''
# MRP SETTA - custo de referencia do CADASTROS: VALOR DA ULTIMA COMPRA.
# Conserva nulo quando nao ha valor verificavel; nunca inventar custo zero.
_cost_anchor='    cad=cad[_cad_ok].copy()'
if _source.count(_cost_anchor)!=2:
    raise RuntimeError("Custos avulsos: carregadores CADASTROS nao encontrados.")
_cost_prefix="""    import unicodedata as _unicode_cad
    def _cad_normalizar_nome(nome):
        texto=_unicode_cad.normalize("NFKD",str(nome or "").strip().upper())
        return "".join(ch for ch in texto if not _unicode_cad.combining(ch))
    _nomes_custo={
        "VALOR DA ULTIMA COMPRA","VALOR ULTIMA COMPRA",
        "VALOR DA ULT. COMPRA","VALOR ULT. COMPRA",
        "VALOR UNITARIO ULTIMA COMPRA","PRECO ULTIMA COMPRA",
        "PRECO DA ULTIMA COMPRA","CUSTO ULTIMA COMPRA",
        "PRC ULT COMPRA","VLR ULT COMPRA","VLR ULT. COMPRA",
        "VLR ULTIMA COMPRA","VLR. ULT. COMPRA",
    }
    _colunas_custo=[
        col for col in _cad_raw.columns
        if _cad_normalizar_nome(col) in _nomes_custo
    ]
    if not _colunas_custo:
        _colunas_custo=[
            col for col in _cad_raw.columns
            if ("COMPRA" in _cad_normalizar_nome(col))
            and ("ULT" in _cad_normalizar_nome(col))
            and any(x in _cad_normalizar_nome(col) for x in ("VALOR","PRECO","CUSTO","VLR","PRC"))
        ]
    if len(_colunas_custo)>1:
        raise ValueError("CADASTROS: coluna de valor da ultima compra ambigua: "+", ".join(map(str,_colunas_custo)))
    if _colunas_custo:
        def _cad_valor_monetario(v):
            if v is None or pd.isna(v): return float("nan")
            if isinstance(v,(int,float)): return float(v) if float(v)>=0 else float("nan")
            t=str(v).strip().replace("R$","").replace(" ","")
            if not t:return float("nan")
            if "," in t:t=t.replace(".","").replace(",",".")
            try:
                n=float(t)
                return n if pd.notna(n) and n>=0 else float("nan")
            except ValueError:return float("nan")
        cad["Valor Última Compra"]=_cad_raw[_colunas_custo[0]].map(_cad_valor_monetario)
    else:
        # Valor nao carregado no MRP ate que o CADASTROS tenha o campo.
        cad["Valor Última Compra"]=float("nan")
"""
_source=_source.replace(_cost_anchor,_cost_prefix+_cost_anchor)
# Nova assinatura de calculo: obriga nova fotografia com o valor da ultima compra.
if _source.count("MRP-CALC-V4-COMPRA-TCTP-GRUPO")!=1:
    raise RuntimeError("Custos avulsos: assinatura do MRP nao localizada.")
_source=_source.replace(
    "MRP-CALC-V4-COMPRA-TCTP-GRUPO",
    "MRP-CALC-V5-CUSTO-ULTIMA-COMPRA",
    1,
)
'''
