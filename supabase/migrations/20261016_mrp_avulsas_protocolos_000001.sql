-- MRP SETTA — reiniciar numeros publicos das S.A. em SA-000001.
-- Preserva pedidos, itens, UUIDs, auditoria, origem e datas.
-- Registro da equivalencia protege referencias historicas.
create table if not exists public.mrp_avulsas_protocolo_migracoes (
 pedido_id uuid primary key references public.mrp_avulsas_pedidos(id),
 numero_anterior bigint not null,
 numero_novo bigint not null,
 migrado_em timestamptz not null default now()
);
alter table public.mrp_avulsas_protocolo_migracoes enable row level security;
revoke all on public.mrp_avulsas_protocolo_migracoes from public,anon,authenticated;
grant select,insert on public.mrp_avulsas_protocolo_migracoes to service_role;

do $$
declare v_qtd bigint; v_min bigint; v_max bigint;
begin
  lock table public.mrp_avulsas_pedidos in exclusive mode;
  select count(*),min(numero),max(numero) into v_qtd,v_min,v_max
  from public.mrp_avulsas_pedidos;
  if v_qtd>0 and v_min>=1001 then
    -- Conferimos antes se não existem numeros novos intercalados.
    with nova_ordem as (
      select id,numero as numero_antigo,
      row_number() over(order by criado_em,id)::bigint as novo_numero
      from public.mrp_avulsas_pedidos
    ),auditoria as (
      insert into public.mrp_avulsas_protocolo_migracoes(pedido_id,numero_anterior,numero_novo)
      select id,numero_antigo,novo_numero from nova_ordem
      on conflict(pedido_id) do nothing
    )
    update public.mrp_avulsas_pedidos p
    set numero=n.novo_numero
    from nova_ordem n where p.id=n.id;
  elsif v_qtd>0 and v_min<1001 then
    -- Idempotente em execucoes futuras, sem renumerar novamente.
    null;
  end if;
  select max(numero) into v_max from public.mrp_avulsas_pedidos;
  if v_max is null then
    perform setval('public.mrp_avulsas_numero_seq',1,false);
  else
    perform setval('public.mrp_avulsas_numero_seq',v_max,true);
  end if;
end;
$$;
