-- MRP SETTA: converter SOMENTE os 3 protocolos antigos, já categorizados e conferidos.
-- Não altera itens, quantidades, reservas, status de itens ou autoria original.
do $mrp$
declare
  v_count integer;
begin
  perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
  select count(*) into v_count
    from public.mrp_avulsas_pedidos
   where numero in (1,2,3)
     and estado in ('LEGADO','PENDENTE','SEPARADA');
  if v_count <> 3 then
    raise exception 'SA_000001_000003_CONFERENCIA_DIVERGENTE';
  end if;

  -- As 000002/000003 só podem ser pendentes se todos os respectivos itens estiverem abertos.
  update public.mrp_avulsas_pedidos p
     set estado='PENDENTE'
   where p.numero in (2,3) and p.estado='LEGADO'
     and exists (select 1 from public.mrp_solicitacoes_avulsas i where i.pedido_id=p.id)
     and not exists (select 1 from public.mrp_solicitacoes_avulsas i
                     where i.pedido_id=p.id and i.status <> 'ABERTA');

  -- A 000001 foi separada no fluxo antigo. Respeitar data e operador reais dos itens.
  update public.mrp_avulsas_pedidos p
     set estado='SEPARADA',
         separado_em=(select max(i.atendido_em) from public.mrp_solicitacoes_avulsas i
                      where i.pedido_id=p.id),
         separado_por=(select i.atendido_por from public.mrp_solicitacoes_avulsas i
                       where i.pedido_id=p.id and i.atendido_por is not null
                       order by i.atendido_em desc nulls last,i.id desc limit 1)
   where p.numero=1 and p.estado='LEGADO'
     and exists (select 1 from public.mrp_solicitacoes_avulsas i where i.pedido_id=p.id)
     and not exists (select 1 from public.mrp_solicitacoes_avulsas i
                     where i.pedido_id=p.id and i.status <> 'ATENDIDA');

  if exists(select 1 from public.mrp_avulsas_pedidos
             where numero in (1,2,3) and estado='LEGADO') then
    raise exception 'PEDIDOS_AINDA_LEGADOS_OPERACAO_CANCELADA';
  end if;
end
$mrp$;

-- Completar apenas os dados da finalidade no momento da entrega física.
-- A confirmação da entrega e seus eventos ocorrerão na mesma transação.
create or replace function public.mrp_avulsa_entregar_com_dados_seguro(
  p_pedido_id uuid,
  p_actor uuid,
  p_psys text default null,
  p_cr text default null,
  p_aprovador text default null
) returns jsonb
language plpgsql security definer set search_path=public as $$
declare
  v_pedido public.mrp_avulsas_pedidos%rowtype;
  v_psys text;
  v_cr text;
  v_aprovador text;
  v_result jsonb;
begin
  if not exists(select 1 from public.user_roles
                 where user_id=p_actor and role='OPERADOR') then
    raise exception 'OPERADOR_OBRIGATORIO';
  end if;
  perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
  select * into v_pedido from public.mrp_avulsas_pedidos
    where id=p_pedido_id for update;
  if not found then raise exception 'PEDIDO_NAO_ENCONTRADO'; end if;
  if v_pedido.estado<>'SEPARADA' then raise exception 'PEDIDO_AINDA_NAO_SEPARADO'; end if;

  v_psys:=coalesce(nullif(trim(coalesce(p_psys,'')),''),v_pedido.psys);
  v_cr:=coalesce(nullif(trim(coalesce(p_cr,'')),''),v_pedido.cr);
  v_aprovador:=coalesce(nullif(trim(coalesce(p_aprovador,'')),''),v_pedido.aprovador);
  if v_pedido.finalidade='GARANTIA' then
    if length(trim(coalesce(v_psys,'')))<2 or length(v_psys)>1000 then
      raise exception 'INFORME_OS_PSYS_ANTES_DA_ENTREGA';
    end if;
  elsif v_pedido.finalidade='ACERTO_GERENCIAL' then
    if length(trim(coalesce(v_cr,'')))<1 or length(v_cr)>150
       or length(trim(coalesce(v_aprovador,'')))<2 or length(v_aprovador)>180 then
      raise exception 'INFORME_CR_E_APROVADOR_ANTES_DA_ENTREGA';
    end if;
  elsif v_pedido.finalidade<>'TRANSFERENCIA' then
    raise exception 'FINALIDADE_NAO_DEFINIDA_PARA_ENTREGA';
  end if;

  update public.mrp_avulsas_pedidos
     set psys=case when finalidade='GARANTIA' then trim(v_psys) else psys end,
         cr=case when finalidade='ACERTO_GERENCIAL' then trim(v_cr) else cr end,
         aprovador=case when finalidade='ACERTO_GERENCIAL' then trim(v_aprovador) else aprovador end
   where id=p_pedido_id;

  -- Reutiliza os controles atuais (operador, estado, custo=0, auditoria e email_evento).
  v_result:=public.mrp_avulsa_pedido_tratar_seguro(
    p_pedido_id,p_actor,'ENTREGAR',''
  );
  return v_result;
end
$$;
revoke all on function public.mrp_avulsa_entregar_com_dados_seguro(uuid,uuid,text,text,text)
 from public,anon,authenticated;
grant execute on function public.mrp_avulsa_entregar_com_dados_seguro(uuid,uuid,text,text,text)
 to service_role;
