-- Implantado na Central SETTA em 10/11/2026.
-- Tabela somente para controle de envios; não armazena nomes ou códigos.
create table if not exists public.mrp_excedentes_envios (
  data_referencia date primary key,
  snapshot_id bigint not null references public.mrp_snapshots(id),
  status text not null check (status in ('RESERVADO', 'ACEITO_PELO_TRANSPORTE', 'VERIFICAR_FALHA')),
  planilha_hash text not null check (length(planilha_hash) = 64),
  destinatarios_hash text not null check (length(destinatarios_hash) = 64),
  qtd_sc integer not null check (qtd_sc >= 0),
  qtd_pc integer not null check (qtd_pc >= 0),
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
comment on table public.mrp_excedentes_envios is
  'Controle dos e-mails de cancelamento MRP sem dados de materiais ou destinatários.';
alter table public.mrp_excedentes_envios enable row level security;
revoke all on public.mrp_excedentes_envios from anon, authenticated;
grant select, insert, update on public.mrp_excedentes_envios to service_role;
-- Reserva única por data impede envios repetidos se o job for reexecutado.
