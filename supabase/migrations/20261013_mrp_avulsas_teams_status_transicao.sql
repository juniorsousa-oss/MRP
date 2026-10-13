alter table public.mrp_avulsas_pedidos
  drop constraint if exists mrp_avulsas_pedidos_teams_status_check;
alter table public.mrp_avulsas_pedidos
  add constraint mrp_avulsas_pedidos_teams_status_check
  check (teams_status in ('PENDENTE','ENVIANDO','ENVIADO','FALHA','NAO_CONFIGURADO'));