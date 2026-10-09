MRP_TABLES_PATCH = r'''
# Redimensiona tabelas de consulta/conferência ao total de linhas após filtros.
# Esta camada executa depois das demais e não altera dados nem cálculos do MRP.
if _source.count("import streamlit as st\n") != 1:
    raise RuntimeError("Import do Streamlit não localizado para tabelas adaptativas.")
_source=_source.replace("st.dataframe(", "_setta_dataframe(")
_source=_source.replace("st.data_editor(", "_setta_data_editor(")
_mrp_table_helpers = """# Altura adaptativa para qualquer relatório do MRP (sem linhas vazias artificiais).
def _setta_table_height(data, requested=None):
    if isinstance(requested, str):
        return requested
    frame=getattr(data,"data",data)
    try:
        rows=len(frame)
    except (TypeError,ValueError,AttributeError):
        return requested if isinstance(requested,int) and requested>=120 else None
    maximum=max(120,requested) if isinstance(requested,int) and requested>0 else 600
    return int(min(maximum,max(120,42+35*(min(max(0,rows),100)+1))))

def _setta_dataframe(data,*args,**kwargs):
    height=_setta_table_height(data,kwargs.get("height"))
    if height is None:
        kwargs.pop("height",None)
    else:
        kwargs["height"]=height
    return st.dataframe(data,*args,**kwargs)

def _setta_data_editor(data,*args,**kwargs):
    if kwargs.get("num_rows")!="dynamic":
        height=_setta_table_height(data,kwargs.get("height"))
        if height is None:
            kwargs.pop("height",None)
        else:
            kwargs["height"]=height
    return st.data_editor(data,*args,**kwargs)

"""
_source=_source.replace("import streamlit as st\n","import streamlit as st\n"+_mrp_table_helpers,1)
'''