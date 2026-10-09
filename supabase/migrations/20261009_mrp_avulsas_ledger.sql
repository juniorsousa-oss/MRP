-- Atendimentos continuam consumindo a DIV da versão original do MRP.
-- Solicitações ainda em aberto de versões anteriores continuam reservadas.
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
 where codigo=p_codigo and (
  status='ABERTA'
  or (status='ATENDIDA' and snapshot_id=p_snapshot_id)
 );
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
