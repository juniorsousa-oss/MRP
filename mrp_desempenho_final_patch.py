DESEMPENHO_FINAL_PATCH = r'''
# =========================================================
# DESEMPENHO FINAL — CÁLCULO PESADO SOMENTE QUANDO INSUMOS MUDAM
# =========================================================

# Evita varrer Compras/TCTP do zero para cada produto da Demanda por Projeto.
_pool_anchor = 'def calcular_demanda_projeto(df):'
_pool_code = r"""
_pc_pool_map={}
for _pool_code,_pool_rows in cp[cp["Quantidade P.C."]>0].sort_values(
    ["Código","Semana P.C."],na_position="last"
).groupby("Código",sort=False):
    _pc_pool_map[int(_pool_code)]=[
        {"qty":float(_q),"week":_w}
        for _q,_w in zip(_pool_rows["Quantidade P.C."],_pool_rows["Semana P.C."])
    ]

_sc_pool_map={}
for _pool_code,_pool_rows in cp[cp["Quantidade S.C."]>0].sort_values(
    ["Código","Semana S.C."],na_position="last"
).groupby("Código",sort=False):
    _sc_pool_map[int(_pool_code)]=[
        {"qty":float(_q),"week":_w}
        for _q,_w in zip(_pool_rows["Quantidade S.C."],_pool_rows["Semana S.C."])
    ]

_fab_pool_map={}
for _pool_code,_pool_rows in op.sort_values(
    ["Código Produto","Semana Entrega"],na_position="last"
).groupby("Código Produto",sort=False):
    _fab_pool_map[int(_pool_code)]=[
        {"qty":1.0,"week":_w}
        for _w in _pool_rows["Semana Entrega"].tolist()
    ]

"""
if _source.count(_pool_anchor) == 1 and '_pc_pool_map={}' not in _source:
    _source = _source.replace(_pool_anchor, _pool_code + _pool_anchor, 1)

_pool_replacements = {
    '        pc_pool=[{"qty":float(r["Quantidade P.C."]),"week":r["Semana P.C."]} for _,r in cp[(cp["Código"]==int(code))&(cp["Quantidade P.C."]>0)].sort_values("Semana P.C.",na_position="last").iterrows()]':
    '        pc_pool=[item.copy() for item in _pc_pool_map.get(int(code),())]',
    '        fab_pool=[{"qty":1.0,"week":r["Semana Entrega"]} for _,r in op[op["Código Produto"]==int(code)].sort_values("Semana Entrega",na_position="last").iterrows()]':
    '        fab_pool=[item.copy() for item in _fab_pool_map.get(int(code),())]',
    '        sc_pool=[{"qty":float(r["Quantidade S.C."]),"week":r["Semana S.C."]} for _,r in cp[(cp["Código"]==int(code))&(cp["Quantidade S.C."]>0)].sort_values("Semana S.C.",na_position="last").iterrows()]':
    '        sc_pool=[item.copy() for item in _sc_pool_map.get(int(code),())]',
}
for _old,_new in _pool_replacements.items():
    if _old in _source:
        _source = _source.replace(_old,_new,1)

# Invalida cálculo imediatamente após gravar tratativas.
def _inject_calc_invalidation(function_name, cache_function_name):
    global _source
    pattern = rf'(def {function_name}\(df\):.*?)(    return len\(base\)\n)'
    def repl(match):
        insert = (
            f'    try:\n'
            f'        {cache_function_name}.clear()\n'
            f'    except Exception:\n'
            f'        pass\n'
            f'    st.session_state.pop("_mrp_compute_cache",None)\n'
        )
        return match.group(1) + insert + match.group(2)
    _source, _ = re.subn(pattern,repl,_source,count=1,flags=re.S)

_inject_calc_invalidation("_salvar_tratativas_db","_carregar_tratativas_salvas")
_inject_calc_invalidation("_salvar_tratativas_produto_db","_carregar_tratativas_produto_salvas")

# O bloco pesado inteiro fica em memória da sessão por assinatura das bases + tratativas.
_calc_start_marker = 'codigos_ii=set(cad.loc[cad["Tipo"].str.upper().eq("II"),"Código"])'
_calc_end_marker = 'fab_det=op[["ORDEM DE PRODUÇÃO","Código Produto","Semana Entrega"]].sort_values(["Código Produto","Semana Entrega","ORDEM DE PRODUÇÃO"]).copy(); fab_det["Quantidade"]=1'
_calc_start = _source.find(_calc_start_marker)
_calc_end_start = _source.find(_calc_end_marker,_calc_start)

if _calc_start < 0 or _calc_end_start < 0:
    raise RuntimeError("Bloco principal de cálculo do MRP não encontrado para otimização.")

_calc_end = _calc_end_start + len(_calc_end_marker)
_calc_block = _source[_calc_start:_calc_end]

if '_mrp_compute_cache_key' not in _source:
    _calc_indented = "\n".join(
        ("    " + line) if line.strip() else line
        for line in _calc_block.splitlines()
    )
    _calc_wrapper = r"""
_trat_project_for_sig=_carregar_tratativas_salvas()
_trat_product_for_sig=_carregar_tratativas_produto_salvas()

if _mrp_use_manual:
    _mrp_base_signature=hashlib.sha256(
        b"MRP-MANUAL|"+b"|".join(
            f.getvalue()
            for f in [cadastro_file,estoque_file,geral_file,compras_file,mt_file]
        )
    ).hexdigest()
else:
    _mrp_base_signature=str(_central_bundle.get("signature") or "")

_mrp_treatment_signature=hashlib.sha256(
    (
        _trat_project_for_sig.sort_values(list(_trat_project_for_sig.columns)).to_json(
            orient="records",date_format="iso",force_ascii=False
        )
        +
        _trat_product_for_sig.sort_values(list(_trat_product_for_sig.columns)).to_json(
            orient="records",date_format="iso",force_ascii=False
        )
    ).encode("utf-8")
).hexdigest()

_mrp_compute_cache_key=hashlib.sha256(
    f"{_mrp_base_signature}|{semana_atual}|{_mrp_treatment_signature}|MRP-CALC-V2".encode("utf-8")
).hexdigest()

_mrp_cached=st.session_state.get("_mrp_compute_cache")
if isinstance(_mrp_cached,dict) and _mrp_cached.get("key")==_mrp_compute_cache_key:
    macro=_mrp_cached["macro"]
    proj=_mrp_cached["proj"]
    demanda_projeto=_mrp_cached["demanda_projeto"]
    compras_mrp=_mrp_cached["compras_mrp"]
    fab_det=_mrp_cached["fab_det"]
    tratativas_projeto=_trat_project_for_sig.copy()
    tratativas_produto=_trat_product_for_sig.copy()
else:
__CALC_BLOCK__
    st.session_state["_mrp_compute_cache"]={
        "key":_mrp_compute_cache_key,
        "macro":macro,
        "proj":proj,
        "demanda_projeto":demanda_projeto,
        "compras_mrp":compras_mrp,
        "fab_det":fab_det,
    }
"""
    _calc_wrapper = _calc_wrapper.replace('__CALC_BLOCK__',_calc_indented)
    _source = _source[:_calc_start] + _calc_wrapper + _source[_calc_end:]

'''
