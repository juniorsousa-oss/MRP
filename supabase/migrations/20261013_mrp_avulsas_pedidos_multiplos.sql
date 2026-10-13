-- MRP SETTA: pedidos multi-itens, atomicidade e rastreio da notificação ao Teams.
-- Fluxos legados de item único e atendimento/recusa permanecem intactos.
create table if not exists public.mrp_avulsas_pedidos (
  id uuid primary key,
  snapshot_id bigint not null references public.mrp_snapshots(id),
  solicitante text not null,
  criado_por uuid not null,
  itens_hash text not null,
  criado_em timestamptz not null default now(),
  teams_status text not null default 'PENDENTE'
    check (teams_status in ('PENDENTE','ENVIADO','FALHA','NAO_CONFIGURADO')),
  teams_tentativas integer not null default 0,
  teams_enviado_em timestamptz,
  teams_erro text
);
alter table public.mrp_avulsas_pedidos enable row level security;
revoke all on public.mrp_avulsas_pedidos from public, anon, authenticated;
grant select, insert, update on public.mrp_avulsas_pedidos to service_role;

alter table public.mrp_solicitacoes_avulsas
  add column if not exists pedido_id uuid references public.mrp_avulsas_pedidos(id);
create index if not exists idx_mrp_avulsas_pedido
  on public.mrp_solicitacoes_avulsas(pedido_id);

create or replace function public.mrp_avulsa_criar_lote_seguro(
  p_snapshot_id bigint,
  p_pedido_id uuid,
  p_itens jsonb,
  p_solicitante text,
  p_criado_por uuid
) returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_latest bigint;
  v_existing public.mrp_avulsas_pedidos%rowtype;
  v_item jsonb;
  v_codigo text;
  v_desc text;
  v_qty numeric;
  v_limite numeric;
  v_reservado numeric;
  v_ids bigint[] := array[]::bigint[];
  v_id bigint;
  v_codes text[] := array[]::text[];
  v_hash text;
begin
  if p_pedido_id is null or p_criado_por is null or
     length(trim(coalesce(p_solicitante,''))) not between 1 and 180 then
    raise exception 'PEDIDO_OU_SOLICITANTE_INVALIDO';
  end if;
  if p_itens is null or jsonb_typeof(p_itens) <> 'array' or
     jsonb_array_length(p_itens) not between 1 and 30 then
    raise exception 'PEDIDO_DEVE_CONTER_1_A_30_MATERIAIS';
  end if;

  -- Validação dos números e do formato antes de reservar qualquer material.
  for v_item in select value from jsonb_array_elements(p_itens) loop
    v_codigo := trim(coalesce(v_item->>'codigo',''));
    if v_codigo !~ '^[0-9]{8}$' or v_codigo = any(v_codes) then
      raise exception 'CODIGO_INVALIDO_OU_DUPLICADO';
    end if;
    v_codes := array_append(v_codes, v_codigo);
    if coalesce(v_item->>'quantidade','') !~ '^[0-9]+(\.[0-9]{1,3})?$'
       or coalesce(v_item->>'limite','') !~ '^[0-9]+(\.[0-9]{1,3})?$' then
      raise exception 'QUANTIDADE_OU_LIMITE_INVALIDO';
    end if;
    v_qty := (v_item->>'quantidade')::numeric;
    v_limite := (v_item->>'limite')::numeric;
    if v_qty <= 0 or v_limite <= 0 or v_qty > v_limite then
      raise exception 'QUANTIDADE_SUPERIOR_A_DIV';
    end if;
  end loop;

  v_hash := md5(p_snapshot_id::text || '|' || p_criado_por::text || '|' ||
    trim(p_solicitante) || '|' || p_itens::text);

  -- Mesmo lock usado pelas requisições unitárias e atendimento/recusa.
  perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
  select * into v_existing from public.mrp_avulsas_pedidos where id=p_pedido_id;
  if found then
    if v_existing.criado_por is distinct from p_criado_por or
       v_existing.itens_hash is distinct from v_hash then
      raise exception 'IDENTIFICADOR_DE_PEDIDO_REUTILIZADO_COM_DADOS_DIFERENTES';
    end if;
    select coalesce(array_agg(id order by id),array[]::bigint[]) into v_ids
      from public.mrp_solicitacoes_avulsas where pedido_id=p_pedido_id;
    return jsonb_build_object('pedido_id',p_pedido_id,'ids',v_ids,
      'total_itens',cardinality(v_ids),'repetido',true,
      'teams_status',v_existing.teams_status);
  end if;

  select id into v_latest from public.mrp_snapshots
    order by created_at desc, id desc limit 1;
  if v_latest is null or v_latest is distinct from p_snapshot_id then
    raise exception 'MRP_DESATUALIZADO_RECARREGAR';
  end if;

  -- A trava cobre a validação e todos os INSERTs; falhar em qualquer item
  -- provoca rollback completo (nunca grava pedido parcial).
  insert into public.mrp_avulsas_pedidos(
    id,snapshot_id,solicitante,criado_por,itens_hash
  ) values(p_pedido_id,p_snapshot_id,trim(p_solicitante),p_criado_por,v_hash);

  for v_item in select value from jsonb_array_elements(p_itens) loop
    v_codigo := trim(v_item->>'codigo');
    v_desc := left(trim(coalesce(v_item->>'descricao','')),500);
    v_qty := (v_item->>'quantidade')::numeric;
    v_limite := (v_item->>'limite')::numeric;
    select coalesce(sum(quantidade),0) into v_reservado
      from public.mrp_solicitacoes_avulsas
      where codigo=v_codigo
        and (status='ABERTA' or (status='ATENDIDA' and snapshot_id=p_snapshot_id));
    if v_qty+v_reservado>v_limite then
      raise exception 'SALDO_INSUFICIENTE_CODIGO_% (LIMITE %, RESERVADO %, PEDIDO %)',
        v_codigo,v_limite,v_reservado,v_qty;
    end if;
    insert into public.mrp_solicitacoes_avulsas(
      pedido_id,snapshot_id,codigo,descricao,quantidade,div_referencia,
      solicitante,criado_por
    ) values (
      p_pedido_id,p_snapshot_id,v_codigo,v_desc,v_qty,v_limite,
      trim(p_solicitante),p_criado_por
    ) returning id into v_id;
    v_ids := array_append(v_ids,v_id);
  end loop;
  return jsonb_build_object('pedido_id',p_pedido_id,'ids',v_ids,
    'total_itens',cardinality(v_ids),'repetido',false,'teams_status','PENDENTE');
end;
$$;
revoke all on function public.mrp_avulsa_criar_lote_seguro(bigint,uuid,jsonb,text,uuid)
  from public,anon,authenticated;
grant execute on function public.mrp_avulsa_criar_lote_seguro(bigint,uuid,jsonb,text,uuid)
  to service_role;
