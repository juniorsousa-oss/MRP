"""Regressão dos dados obrigatórios da exceção de estoque empenhado.

Validação estática sem criar solicitações ou modificar dados da produção.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
form=(root/"mrp_avulsas_fluxo_patch.py").read_text("utf-8")
api=(root/"supabase/functions/mrp-avulsas-api/index.ts").read_text("utf-8")
sql=(root/"supabase/migrations/20261029_mrp_excecao_solicitante_responsavel.sql").read_text("utf-8")
for expected in (
    'st.text_input("E-MAIL DO SOLICITANTE *"',
    'st.session_state.get("auth_email")',
    'RESPONSÁVEL QUE AUTORIZOU O USO DO MATERIAL EMPENHADO *',
    '"solicitante":_exc_email',
    '"responsavel_autorizacao":_exc_responsavel.strip()',
    'Informe o e-mail corporativo completo do solicitante',
    'Informe o nome do responsável que autorizou o uso',
    'str(_ex.get("responsavel_autorizacao_informado")',
    'st.write("**Solicitante:**',
): assert expected in form, expected
for expected in (
    'const emailSolicitante=String(input.solicitante||"").trim().toLowerCase();',
    'const responsavel=String(input.responsavel_autorizacao||"").trim();',
    'EMAIL_SOLICITANTE_INVALIDO',
    'RESPONSAVEL_AUTORIZACAO_OBRIGATORIO',
    'p_email:emailSolicitante',
    'p_responsavel_autorizacao:responsavel',
    'mrp_excecao_solicitar_identificada_seguro',
    'responsavel_autorizacao_informado',
): assert expected in api, expected
for expected in (
    'add column if not exists responsavel_autorizacao_informado text',
    'mrp_excecao_solicitar_identificada_seguro',
    "raise exception 'RESPONSAVEL_AUTORIZACAO_OBRIGATORIO'",
    'v_exists.solicitante<>lower(trim(p_email))',
    'v_exists.responsavel_autorizacao_informado is distinct from trim(p_responsavel_autorizacao)',
    'responsavel_autorizacao_informado',
    'grant execute on function',
    'to service_role;',
): assert expected in sql, expected
assert 'p_email:String(identity.user.email||"").toLowerCase(),' not in api
print("OK: e-mail do solicitante e responsável de autorização exigidos e rastreáveis.")
