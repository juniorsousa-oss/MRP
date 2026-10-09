-- Solicitações avulsas vinculadas ao último MRP efetivamente salvo.
-- Operações somente pelo serviço validado, nunca RPC direta do navegador.
create table if not exists public.mrp_solicitacoes_avulsas (
 id bigint generated always as identity primary key,
 snapshot_id bigint not null references public.mrp_snapshots(id),
 codigo text not null,
 descricao text not null default '',
 quantidade numeric(18,3) not null check (quantidade > 0),
 div_referencia numeric(18,3) not null check(div_referencia > 0),
 solicitante text not null,
 criado_por uuid not null,
 criado_em timestamptz not null default now(),
 status text not null default 'ABERTA' check(status in ('ABERTA','ATENDIDA')),
 atendido_por uuid,
 atendido_em timestamptz,
 observacao_atendimento text not null default ''
);
create index if not exists idx_mrp_avulsas_abertas
 on public.mrp_solicitacoes_avulsas (codigo) where status='ABERTA';
create index if not exists idx_mrp_avulsas_data
 on public.mrp_solicitacoes_avulsas (criado_em desc);
alter table public.mrp_solicitacoes_avulsas enable row level security;
revoke all on public.mrp_solicitacoes_avulsas from public,anon,authenticated;
grant select,insert,update on public.mrp_solicitacoes_avulsas to service_role;
grant usage,select on sequence public.mrp_solicitacoes_avulsas_id_seq to service_role;

create or replace function public.mrp_avulsa_criar_seguro(
 p_snapshot_id bigint,p_codigo text,p_descricao text,p_div numeric,
 p_quantidade numeric,p_solicitante text,p_criado_por uuid
) returns jsonb language plpgsql security definer set search_path=public as $$
declare
 v_latest bigint;
 v_reserved numeric(18,3);
 v_id bigint;
begin
 perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
 select id into v_latest from public.mrp_snapshots order by created_at desc,id desc limit 1;
 if v_latest is null or p_snapshot_id is distinct from v_latest then
  raise exception 'MRP_DESATUALIZADO_RECARREGAR';
 end if;
 if trim(coalesce(p_codigo,''))='' or trim(coalesce(p_solicitante,''))='' or p_criado_por is null then
  raise exception 'MATERIAL_E_SOLICITANTE_OBRIGATORIOS';
 end if;
 if p_div is null or p_div<=0 then raise exception 'MATERIAL_SEM_DIV_POSITIVA'; end if;
 if p_quantidade is null or p_quantidade<=0 or p_quantidade>p_div then
  raise exception 'QUANTIDADE_SUPERIOR_A_DIV';
 end if;
 select coalesce(sum(quantidade),0) into v_reserved
 from public.mrp_solicitacoes_avulsas
 where codigo=p_codigo and status='ABERTA';
 if p_quantidade+v_reserved>p_div then
  raise exception 'QUANTIDADE_SUPERIOR_A_DIV_DISPONIVEL (DIV %, ABERTAS %, DISPONIVEL %)',
   p_div,v_reserved,greatest(p_div-v_reserved,0);
 end if;
 insert into public.mrp_solicitacoes_avulsas
 (snapshot_id,codigo,descricao,quantidade,div_referencia,solicitante,criado_por)
 values (p_snapshot_id,p_codigo,left(coalesce(p_descricao,''),500),p_quantidade,p_div,
 left(trim(p_solicitante),180),p_criado_por)
 returning id into v_id;
 return jsonb_build_object('id',v_id,'status','ABERTA','disponivel_apos',p_div-v_reserved-p_quantidade);
end;
$$;
revoke all on function public.mrp_avulsa_criar_seguro(bigint,text,text,numeric,numeric,text,uuid)
 from public,anon,authenticated;
grant execute on function public.mrp_avulsa_criar_seguro(bigint,text,text,numeric,numeric,text,uuid) to service_role;

create or replace function public.mrp_avulsa_atender_seguro(
 p_id bigint,p_actor uuid,p_observacao text default ''
) returns jsonb language plpgsql security definer set search_path=public as $$
declare v_status text;
begin
 if p_actor is null then raise exception 'IDENTIFICACAO_OBRIGATORIA'; end if;
 update public.mrp_solicitacoes_avulsas
 set status='ATENDIDA',atendido_por=p_actor,atendido_em=now(),
 observacao_atendimento=left(trim(coalesce(p_observacao,'')),1000)
 where id=p_id and status='ABERTA'
 returning status into v_status;
 if v_status is null then raise exception 'SOLICITACAO_INEXISTENTE_OU_JA_ATENDIDA'; end if;
 return jsonb_build_object('id',p_id,'status',v_status);
end;
$$;
revoke all on function public.mrp_avulsa_atender_seguro(bigint,uuid,text)
 from public,anon,authenticated;
grant execute on function public.mrp_avulsa_atender_seguro(bigint,uuid,text) to service_role;
