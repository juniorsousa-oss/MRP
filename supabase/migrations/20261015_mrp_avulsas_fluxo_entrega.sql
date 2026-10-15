-- MRP SETTA — protocolo unico por pedido, finalidade, entrega e auditoria.
-- Migração aditiva: pedidos/itens legados são preservados.
create sequence if not exists public.mrp_avulsas_numero_seq start with 1001 increment by 1;
alter table public.mrp_avulsas_pedidos
  add column if not exists numero bigint default nextval('public.mrp_avulsas_numero_seq'::regclass),
  add column if not exists finalidade text,
  add column if not exists psys text,
  add column if not exists cr text,
  add column if not exists aprovador text,
  add column if not exists destino text,
  add column if not exists estado text not null default 'LEGADO',
  add column if not exists separado_por uuid,
  add column if not exists separado_em timestamptz,
  add column if not exists entregue_por uuid,
  add column if not exists entregue_em timestamptz,
  add column if not exists observacao_operador text;
create unique index if not exists mrp_avulsas_numero_ux
  on public.mrp_avulsas_pedidos(numero);
alter table public.mrp_avulsas_pedidos
  drop constraint if exists mrp_avulsas_pedidos_finalidade_check;
alter table public.mrp_avulsas_pedidos
  add constraint mrp_avulsas_pedidos_finalidade_check
  check (finalidade is null or finalidade in ('GARANTIA','ACERTO_GERENCIAL','TRANSFERENCIA'));
alter table public.mrp_avulsas_pedidos
  drop constraint if exists mrp_avulsas_pedidos_estado_check;
alter table public.mrp_avulsas_pedidos
  add constraint mrp_avulsas_pedidos_estado_check
  check (estado in ('LEGADO','PENDENTE','SEPARADA','RECUSADA','ENTREGUE'));

alter table public.mrp_solicitacoes_avulsas
  add column if not exists valor_unitario_ref numeric(18,4),
  add column if not exists destino_garantia text,
  add column if not exists destino_garantia_em timestamptz,
  add column if not exists destino_garantia_por uuid;
alter table public.mrp_solicitacoes_avulsas
  drop constraint if exists mrp_avulsas_destino_garantia_check;
alter table public.mrp_solicitacoes_avulsas
  add constraint mrp_avulsas_destino_garantia_check
  check (destino_garantia is null or destino_garantia in ('UTILIZADO','DEVOLVIDO'));
alter table public.mrp_solicitacoes_avulsas
  drop constraint if exists mrp_avulsas_valor_ref_check;
alter table public.mrp_solicitacoes_avulsas
  add constraint mrp_avulsas_valor_ref_check
  check (valor_unitario_ref is null or valor_unitario_ref >= 0);

create table if not exists public.mrp_avulsas_eventos (
  id bigint generated always as identity primary key,
  pedido_id uuid not null references public.mrp_avulsas_pedidos(id),
  item_id bigint references public.mrp_solicitacoes_avulsas(id),
  evento text not null,
  autor uuid not null,
  observacao text,
  criado_em timestamptz not null default now()
);
create index if not exists mrp_avulsas_eventos_pedido_idx on public.mrp_avulsas_eventos(pedido_id,criado_em);
alter table public.mrp_avulsas_eventos enable row level security;
revoke all on public.mrp_avulsas_eventos from public,anon,authenticated;
grant select,insert on public.mrp_avulsas_eventos to service_role;

create table if not exists public.mrp_avulsas_email_eventos (
  id bigint generated always as identity primary key,
  pedido_id uuid not null references public.mrp_avulsas_pedidos(id),
  tipo text not null check (tipo in ('SEPARADA','ENTREGUE')),
  status text not null default 'PENDENTE'
    check (status in ('PENDENTE','ENVIANDO','ACEITO','FALHA','NAO_CONFIGURADO')),
  tentativas integer not null default 0,
  ultima_tentativa timestamptz,
  aceito_em timestamptz,
  erro text,
  unique(pedido_id,tipo)
);
alter table public.mrp_avulsas_email_eventos enable row level security;
revoke all on public.mrp_avulsas_email_eventos from public,anon,authenticated;
grant select,insert,update on public.mrp_avulsas_email_eventos to service_role;

-- A regra de reserva continua sendo consumida pelos itens ABERTA/ATENDIDA.
-- ENTREGUE é um estado do pedido e não executa baixa fiscal nem libera saldo.
create or replace function public.mrp_avulsa_criar_lote_v2_seguro(
  p_snapshot_id bigint,
  p_pedido_id uuid,
  p_itens jsonb,
  p_email text,
  p_finalidade text,
  p_psys text,
  p_cr text,
  p_aprovador text,
  p_criado_por uuid
) returns jsonb language plpgsql security definer set search_path=public as $$
declare
  v_result jsonb;
  v_pedido public.mrp_avulsas_pedidos%rowtype;
  v_item jsonb;
  v_itens jsonb := '[]'::jsonb;
  v_destino text;
  v_email text := lower(trim(coalesce(p_email,'')));
  v_finalidade text := trim(coalesce(p_finalidade,''));
begin
  if not exists (select 1 from public.user_roles
                  where user_id=p_criado_por and role='CONSULTA') then
    raise exception 'PERFIL_CONSULTA_OBRIGATORIO';
  end if;
  if length(v_email)>180 or
     v_email !~ '^[a-z0-9][a-z0-9._%+-]*\.[a-z0-9._%+-]+@gruposetta\.com$' then
    raise exception 'EMAIL_CORPORATIVO_INVALIDO';
  end if;
  if v_finalidade not in ('GARANTIA','ACERTO_GERENCIAL','TRANSFERENCIA') then
    raise exception 'FINALIDADE_INVALIDA';
  end if;
  if v_finalidade='GARANTIA' and length(trim(coalesce(p_psys,'')))<2 then
    raise exception 'PSYS_OBRIGATORIOS';
  end if;
  if v_finalidade='ACERTO_GERENCIAL' and
     (length(trim(coalesce(p_cr,'')))<1 or length(trim(coalesce(p_aprovador,'')))<2) then
    raise exception 'CR_E_APROVADOR_OBRIGATORIOS';
  end if;
  if length(coalesce(p_psys,''))>1000 or length(coalesce(p_cr,''))>150
     or length(coalesce(p_aprovador,''))>180 then
    raise exception 'CAMPOS_DA_FINALIDADE_MUITO_EXTENSOS';
  end if;
  v_destino := case when v_finalidade='TRANSFERENCIA' then 'ASTEC' else null end;
  -- A função original preserva trava transacional, limites de DIV e idempotência.
  v_result:=public.mrp_avulsa_criar_lote_seguro(
    p_snapshot_id,p_pedido_id,p_itens,v_email,p_criado_por
  );
  select * into v_pedido from public.mrp_avulsas_pedidos where id=p_pedido_id;
  if coalesce((v_result->>'repetido')::boolean,false) then
    if v_pedido.finalidade is distinct from v_finalidade or
       coalesce(v_pedido.psys,'') is distinct from case when v_finalidade='GARANTIA' then trim(coalesce(p_psys,'')) else '' end or
       coalesce(v_pedido.cr,'') is distinct from case when v_finalidade='ACERTO_GERENCIAL' then trim(coalesce(p_cr,'')) else '' end or
       coalesce(v_pedido.aprovador,'') is distinct from case when v_finalidade='ACERTO_GERENCIAL' then trim(coalesce(p_aprovador,'')) else '' end then
      raise exception 'PEDIDO_REPETIDO_COM_DADOS_DIFERENTES';
    end if;
  else
    update public.mrp_avulsas_pedidos
       set finalidade=v_finalidade,
           psys=case when v_finalidade='GARANTIA' then trim(p_psys) end,
           cr=case when v_finalidade='ACERTO_GERENCIAL' then trim(p_cr) end,
           aprovador=case when v_finalidade='ACERTO_GERENCIAL' then trim(p_aprovador) end,
           destino=v_destino,
           estado='PENDENTE'
     where id=p_pedido_id;
    for v_item in select value from jsonb_array_elements(p_itens) loop
      update public.mrp_solicitacoes_avulsas
         set valor_unitario_ref=
           case when jsonb_typeof(v_item->'valor_unitario')='number'
                 and (v_item->>'valor_unitario')::numeric >=0
                then round((v_item->>'valor_unitario')::numeric,4)
                else null end
       where pedido_id=p_pedido_id and codigo=v_item->>'codigo';
    end loop;
    insert into public.mrp_avulsas_eventos(pedido_id,evento,autor)
      values (p_pedido_id,'CRIADA',p_criado_por);
  end if;
  return v_result || jsonb_build_object('numero',v_pedido.numero,'finalidade',v_finalidade);
end;
$$;
revoke all on function public.mrp_avulsa_criar_lote_v2_seguro(bigint,uuid,jsonb,text,text,text,text,text,uuid) from public,anon,authenticated;
grant execute on function public.mrp_avulsa_criar_lote_v2_seguro(bigint,uuid,jsonb,text,text,text,text,text,uuid) to service_role;

create or replace function public.mrp_avulsa_pedido_tratar_seguro(
  p_pedido_id uuid,p_actor uuid,p_acao text,p_obs text default ''
) returns jsonb language plpgsql security definer set search_path=public as $$
declare
  v_pedido public.mrp_avulsas_pedidos%rowtype;
  v_motivo text:=trim(coalesce(p_obs,''));
  v_qtd integer;
begin
  if not exists (select 1 from public.user_roles
                 where user_id=p_actor and role='OPERADOR') then
    raise exception 'OPERADOR_OBRIGATORIO';
  end if;
  perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
  select * into v_pedido from public.mrp_avulsas_pedidos
    where id=p_pedido_id for update;
  if not found or v_pedido.estado='LEGADO' then
    raise exception 'PEDIDO_NAO_ENCONTRADO_OU_LEGADO';
  end if;
  if p_acao in ('SEPARAR','RECUSAR') then
    if v_pedido.estado<>'PENDENTE' then raise exception 'PEDIDO_JA_TRATADO'; end if;
    if p_acao='RECUSAR' and (length(v_motivo)<5 or length(v_motivo)>1000) then
      raise exception 'MOTIVO_RECUSA_OBRIGATORIO_5_A_1000_CARACTERES';
    end if;
    if p_acao='SEPARAR' then
      update public.mrp_solicitacoes_avulsas
        set status='ATENDIDA',atendido_por=p_actor,atendido_em=now(),
            observacao_atendimento=v_motivo
        where pedido_id=p_pedido_id and status='ABERTA';
      get diagnostics v_qtd=row_count;
      update public.mrp_avulsas_pedidos
        set estado='SEPARADA',separado_por=p_actor,separado_em=now(),observacao_operador=v_motivo
        where id=p_pedido_id;
      insert into public.mrp_avulsas_email_eventos(pedido_id,tipo) values(p_pedido_id,'SEPARADA')
        on conflict(pedido_id,tipo) do nothing;
    else
      update public.mrp_solicitacoes_avulsas
        set status='RECUSADA',recusado_por=p_actor,recusado_em=now(),
            observacao_atendimento=v_motivo
        where pedido_id=p_pedido_id and status='ABERTA';
      get diagnostics v_qtd=row_count;
      update public.mrp_avulsas_pedidos
        set estado='RECUSADA',observacao_operador=v_motivo where id=p_pedido_id;
    end if;
  elsif p_acao='ENTREGAR' then
    if v_pedido.estado<>'SEPARADA' then raise exception 'PEDIDO_AINDA_NAO_SEPARADO'; end if;
    if exists (select 1 from public.mrp_solicitacoes_avulsas
               where pedido_id=p_pedido_id and valor_unitario_ref is null) then
      raise exception 'VALOR_ULTIMA_COMPRA_AUSENTE_VERIFIQUE_CADASTROS';
    end if;
    update public.mrp_avulsas_pedidos
      set estado='ENTREGUE',entregue_por=p_actor,entregue_em=now()
      where id=p_pedido_id;
    select count(*) into v_qtd from public.mrp_solicitacoes_avulsas
      where pedido_id=p_pedido_id;
    insert into public.mrp_avulsas_email_eventos(pedido_id,tipo) values(p_pedido_id,'ENTREGUE')
      on conflict(pedido_id,tipo) do nothing;
  else
    raise exception 'ACAO_INVALIDA';
  end if;
  if coalesce(v_qtd,0)<1 then raise exception 'PEDIDO_SEM_ITENS_EM_ESTADO_ESPERADO'; end if;
  insert into public.mrp_avulsas_eventos(pedido_id,evento,autor,observacao)
    values(p_pedido_id,p_acao,p_actor,nullif(v_motivo,''));
  return jsonb_build_object('pedido_id',p_pedido_id,'estado',
    case when p_acao='SEPARAR' then 'SEPARADA'
         when p_acao='RECUSAR' then 'RECUSADA' else 'ENTREGUE' end,
    'quantidade_itens',v_qtd);
end;
$$;
revoke all on function public.mrp_avulsa_pedido_tratar_seguro(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.mrp_avulsa_pedido_tratar_seguro(uuid,uuid,text,text) to service_role;

create or replace function public.mrp_avulsa_garantia_resultado_seguro(
  p_item bigint,p_actor uuid,p_resultado text
) returns jsonb language plpgsql security definer set search_path=public as $$
declare
  v_registro record;
begin
  if p_resultado not in ('UTILIZADO','DEVOLVIDO') then raise exception 'RESULTADO_INVALIDO'; end if;
  select i.id,i.pedido_id,p.criado_por,p.finalidade,p.estado into v_registro
    from public.mrp_solicitacoes_avulsas i
    join public.mrp_avulsas_pedidos p on p.id=i.pedido_id
    where i.id=p_item for update of i;
  if not found or v_registro.criado_por<>p_actor or v_registro.finalidade<>'GARANTIA'
       or v_registro.estado<>'ENTREGUE' then
    raise exception 'ITEM_GARANTIA_NAO_DISPONIVEL';
  end if;
  if not exists (select 1 from public.user_roles
                 where user_id=p_actor and role='CONSULTA') then
    raise exception 'CONSULTA_OBRIGATORIA';
  end if;
  update public.mrp_solicitacoes_avulsas
    set destino_garantia=p_resultado,destino_garantia_em=now(),destino_garantia_por=p_actor
    where id=p_item;
  insert into public.mrp_avulsas_eventos(pedido_id,item_id,evento,autor)
    values(v_registro.pedido_id,p_item,'GARANTIA_'||p_resultado,p_actor);
  return jsonb_build_object('item_id',p_item,'destino_garantia',p_resultado);
end;
$$;
revoke all on function public.mrp_avulsa_garantia_resultado_seguro(bigint,uuid,text) from public,anon,authenticated;
grant execute on function public.mrp_avulsa_garantia_resultado_seguro(bigint,uuid,text) to service_role;
