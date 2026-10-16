-- Em pedidos anteriores, o preço estava ausente do item.
-- Registrar atomicamente a última compra da coluna M no momento da entrega.
-- Preservar valores já gravados para novos pedidos (histórico de custo).
create or replace function public.mrp_avulsa_entregar_com_custos_seguro(
  p_pedido_id uuid,
  p_actor uuid,
  p_psys text,
  p_cr text,
  p_aprovador text,
  p_precos jsonb
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

  update public.mrp_avulsas_pedidos set
    psys=case when finalidade='GARANTIA' then trim(v_psys) else psys end,
    cr=case when finalidade='ACERTO_GERENCIAL' then trim(v_cr) else cr end,
    aprovador=case when finalidade='ACERTO_GERENCIAL' then trim(v_aprovador) else aprovador end
  where id=p_pedido_id;

  -- O mapa de custos é buscado pela Edge Function diretamente do CADASTROS.
  update public.mrp_solicitacoes_avulsas i
     set valor_unitario_ref=case
       when jsonb_typeof(p_precos -> i.codigo)='number'
            and (p_precos ->> i.codigo)::numeric >= 0
       then round((p_precos ->> i.codigo)::numeric,4)
       else 0
     end
   where i.pedido_id=p_pedido_id and i.valor_unitario_ref is null;

  v_result:=public.mrp_avulsa_pedido_tratar_seguro(p_pedido_id,p_actor,'ENTREGAR','');
  return v_result;
end;
$$;
revoke all on function public.mrp_avulsa_entregar_com_custos_seguro(uuid,uuid,text,text,text,jsonb)
 from public,anon,authenticated;
grant execute on function public.mrp_avulsa_entregar_com_custos_seguro(uuid,uuid,text,text,text,jsonb)
 to service_role;
