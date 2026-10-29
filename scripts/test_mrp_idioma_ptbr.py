"""Auditoria de idioma da interface final (montada com todos os patches).
Garante textos de seleção em PT-BR para não herdar 'Choose an option(s)'.
"""
import ast
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
main=(root/"app_mrp.py").read_text(encoding="utf-8")
boot='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert main.count(boot)==1
ctx={"__name__":"auditoria_idioma","__file__":str(root/"app_mrp.py")}
exec(compile(main.split(boot)[0],"app_mrp.py","exec"),ctx,ctx)
runtime=ctx["_runtime_source"]
run='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(run)==1
env={"__name__":"auditoria_idioma","__file__":str(root/"app_mrp_runtime.py")}
exec(compile(runtime.rsplit(run,1)[0],"app_mrp_runtime.py","exec"),env,env)
final=env["_source"]
tree=ast.parse(final)
problem=[]
count=0
for node in ast.walk(tree):
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):
        continue
    if not isinstance(node.func.value,ast.Name) or node.func.value.id!="st":
        continue
    method=node.func.attr
    if method not in ("selectbox","multiselect"):continue
    count+=1
    kwargs={kw.arg:kw.value for kw in node.keywords if kw.arg}
    index_none=method=="selectbox" and isinstance(kwargs.get("index"),ast.Constant) and kwargs["index"].value is None
    if method=="multiselect" or index_none:
        placeholder=kwargs.get("placeholder")
        if not isinstance(placeholder,ast.Constant) or not isinstance(placeholder.value,str) or not placeholder.value.strip():
            problem.append(f"{method} sem placeholder pt-BR na linha {node.lineno}: {ast.get_source_segment(final,node)[:190]}")
            continue
        txt=placeholder.value.lower()
        if any(t in txt for t in ("choose","select an","search","browse","click here")):
            problem.append(f"{method} com texto inglês na linha {node.lineno}: {txt}")
for english in ("Choose an option","Choose options","Select an option","Search here","Click here"):
    if english in final:problem.append(f"Texto de interface inglês detectado: {english}")
print(f"Auditoria idioma: {count} seletores Streamlit analisados")
if problem:
    for issue in problem:print("FALHA IDIOMA:",issue)
    raise SystemExit(1)
print("OK: todos os seletores que exigem orientação usam português na interface montada.")
