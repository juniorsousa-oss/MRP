"""Read-only checks for email integration diagnostics and delivery authorization."""
from pathlib import Path
import ast
import runpy

root=Path(__file__).resolve().parents[1]
src=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
email=(root/"supabase/functions/mrp-avulsas-api/email.ts").read_text("utf-8")
view=runpy.run_path(str(root/"scripts"/"validate_generated_mrp.py"))["final"]
ast.parse(view)
for token in (
    'action === "email_config_status"',
    'if (role !== "ADMIN") return fail("ADMIN_REQUIRED", 403);',
    'Deno.env.get("MRP_EMAIL_WORKFLOW_URL")',
    'status: configured.startsWith("https://")',
    'Endpoint presente. O envio real ainda precisa ser testado no Outlook.',
):
    assert token in src,token

assert '"VERIFICAR CONFIGURAÇÃO DE E-MAIL"' in view
assert '"email_config_status"' in view
assert '"ADMINISTRAÇÃO · NOTIFICAÇÕES POR E-MAIL"' in view
assert 'MRP_EMAIL_WORKFLOW_URL' in email
assert 'const to = tipo==="ENTREGUE"?gestão:usuario;' in email
assert 'const cc = tipo==="ENTREGUE"?[usuario]:[];' in email
assert '"ENTREGA DE PEÇAS AVULSAS - "+nomeFinalidade' in email
assert 'notificacao_id:event.id' in email
assert 'if(event.status==="ACEITO")return "ACEITO";' in email
assert 'status:"NAO_CONFIGURADO"' in email
doc=(root/"docs"/"NOTIFICACOES_SOLICITACOES_AVULSAS.md").read_text("utf-8")
for token in ("When an HTTP request is received", "Send an email (V2)",
              "notificacao_id", "MRP_EMAIL_WORKFLOW_URL", "oauth-authentication"):
    assert token in doc,token
print("MRP_EMAIL_ADMIN_STATUS_AND_FLOW_CONTRACT_OK")
