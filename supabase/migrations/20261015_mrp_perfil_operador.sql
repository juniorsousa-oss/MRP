-- MRP SETTA — tres perfis independentes de acesso.
-- ADMIN: configuracoes e supervisao.
-- CONSULTA: novas solicitacoes e acompanhamento das proprias requisicoes.
-- OPERADOR: visualizar todas as requisicoes e registrar separacao/recusa.
alter table public.user_roles
  drop constraint if exists user_roles_role_check;
alter table public.user_roles
  add constraint user_roles_role_check
  check (role = any(array['ADMIN'::text,'CONSULTA'::text,'OPERADOR'::text]));
comment on column public.user_roles.role is
  'ADMIN: configuracao e supervisao; CONSULTA: solicitar e acompanhar; OPERADOR: separar e recusar requisicoes.';
