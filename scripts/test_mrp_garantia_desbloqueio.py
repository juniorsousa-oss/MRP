"""Regressão S.A. 000018: ASTEC confirmada sem documento não deve bloquear retorno.
Não consulta nem modifica registros reais.
"""
import ast
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
entry=(root/"app_mrp.py").read_text("utf-8")
marker='exec(compile(_runtime_source, "app_mrp_runtime.py", "exec"), globals(), globals())'
assert entry.count(marker)==1
ctx={"__file__":str(root/"app_mrp.py"),"__name__":"garantia_desbloqueio_teste"}
exec(compile(entry.split(marker)[0],"app_mrp.py","exec"),ctx,ctx)
runtime=ctx["_runtime_source"]
stop='exec(compile(_source, "app_mrp_original.py", "exec"), globals(), globals())'
assert runtime.count(stop)==1
env={"__file__":str(root/"app_mrp_runtime.py"),"__name__":"garantia_desbloqueio_teste"}
exec(compile(runtime.rsplit(stop,1)[0],"app_mrp_runtime.py","exec"),env,env)
source=env["_source"]
view=next(n for n in ast.parse(source).body
          if isinstance(n,ast.FunctionDef) and n.name=="_mrp_avulsas_view")

def expression_for(name):
    matches=[n.value for n in ast.walk(view) if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
    assert len(matches)==1,(name,len(matches))
    return compile(ast.Expression(body=matches[0]),"condicao_garantia","eval")

astec=expression_for("_astec_liberada")
fim=expression_for("_movimentacao_final")

def check(row,expected_astec,expected_fim):
    scope={"_regularizacao_item":row}
    liberada=bool(eval(astec,{},scope))
    finalizada=bool(eval(fim,{},scope))
    assert liberada==expected_astec,(row,liberada)
    assert finalizada==expected_fim,(row,finalizada)
    return liberada,finalizada

# Exatamente o estado real da SA-000018: documento opcional, confirmado_em preenchido.
liberada,finalizada=check({
    "astec_documento":None,
    "astec_confirmado_em":"2026-10-29T12:03:25+00:00",
    "movimento_final_documento":None,
    "movimento_final_confirmado_em":None,
},True,False)
assert liberada and not finalizada, "Botão salvar resultado da ASTEC deve habilitar"

# Documento não é suficiente se não houver comprovação de confirmação.
check({"astec_documento":"123","astec_confirmado_em":None,
       "movimento_final_documento":"234","movimento_final_confirmado_em":None},False,False)

# A confirmação de baixa/devolução também dispensa número de documento.
check({"astec_documento":None,"astec_confirmado_em":"2026-10-29",
       "movimento_final_documento":None,"movimento_final_confirmado_em":"2026-10-29"},True,True)

# Um registro ainda sem confirmação permanece bloqueado.
check({},False,False)
assert "disabled=(not _astec_liberada or _movimentacao_final)" in ast.get_source_segment(source,view)
print("OK: SA 000018 desbloqueada; movimento final e bloqueios corretos")
