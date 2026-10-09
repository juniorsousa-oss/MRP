MRP_TABLES_PATCH = r'''
# Redimensiona tabelas de consulta/conferência ao total de linhas após filtros.
# Esta camada executa depois das demais e não altera dados nem cálculos do MRP.
if _source.count("import streamlit as st\n") != 1:
    raise RuntimeError("Import do Streamlit não localizado para tabelas adaptativas.")
_source=_source.replace("st.dataframe(", "_setta_dataframe(")
_source=_source.replace("st.data_editor(", "_setta_data_editor(")
_mrp_table_helpers = """# Altura adaptativa para qualquer relatório do MRP (sem linhas vazias artificiais).
def _setta_table_height(data, requested=None):
    try:
        rows=len(data)
    except (TypeError,ValueError):
        return requested
    maximum=requested if isinstance(requested,int) and requested>0 else 600
    return min(maximum,max(84,42+35*(min(rows,100)+1)))

def _setta_dataframe(data,*args,**kwargs):
    kwargs["height"]=_setta_table_height(data,kwargs.get("height"))
    return st.dataframe(data,*args,**kwargs)

def _setta_data_editor(data,*args,**kwargs):
    if kwargs.get("num_rows")!="dynamic":
        kwargs["height"]=_setta_table_height(data,kwargs.get("height"))
    return st.data_editor(data,*args,**kwargs)

"""
_source=_source.replace("import streamlit as st\n","import streamlit as st\n"+_mrp_table_helpers,1)
'''