-- Testes controlados do webhook do Teams, sem criar pedidos ou reservar materiais.
create table if not exists public.mrp_teams_testes (
  id bigint generated always as identity primary key,
  user_id uuid not null,
  criado_em timestamptz not null default now(),
  status text not null default 'EM_ANDAMENTO'
    check (status in ('EM_ANDAMENTO','ACEITO','FALHA')),
  erro text
);
create index if not exists idx_mrp_teams_testes_usuario_data
  on public.mrp_teams_testes(user_id,criado_em desc);
alter table public.mrp_teams_testes enable row level security;
revoke all on public.mrp_teams_testes from public, anon, authenticated;
grant select,insert,update on public.mrp_teams_testes to service_role;
