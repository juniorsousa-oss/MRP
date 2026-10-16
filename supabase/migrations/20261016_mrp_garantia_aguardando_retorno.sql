-- MRP SETTA: controle do retorno de materiais de garantia.
-- Aguardando retorno ao entregar, depois utilizado ou devolvido;
-- não sobrescrever situações já validadas e manter auditoria.
alter table public.mrp_solicitacoes_avulsas
  drop constraint if exists mrp_avulsas_destino_garantia_check;
alter table public.mrp_solicitacoes_avulsas
  add constraint mrp_avulsas_destino_garantia_check
  check (destino_garantia is null or destino_garantia in
    ('AGUARDANDO_RETORNO','UTILIZADO','DEVOLVIDO'));

create or replace function public.mrp_avulsa_iniciar_garantia_entregue()
returns trigger language plpgsql security definer
set search_path=public as $$
begin
  if new.estado='ENTREGUE'
     and old.estado is distinct from new.estado
     and new.finalidade='GARANTIA' then
    update public.mrp_solicitacoes_avulsas
       set destino_garantia='AGUARDANDO_RETORNO'
     where pedido_id=new.id and destino_garantia is null;
  end if;
  return new;
end;
$$;

drop trigger if exists mrp_avulsa_ao_entregar_garantia on public.mrp_avulsas_pedidos;
create trigger mrp_avulsa_ao_entregar_garantia
after update of estado on public.mrp_avulsas_pedidos
for each row
execute function public.mrp_avulsa_iniciar_garantia_entregue();

-- Corrigir apenas garantias já entregues sem condição registrada.
update public.mrp_solicitacoes_avulsas i
   set destino_garantia='AGUARDANDO_RETORNO'
  from public.mrp_avulsas_pedidos p
 where p.id=i.pedido_id
   and p.finalidade='GARANTIA'
   and p.estado='ENTREGUE'
   and i.destino_garantia is null;

-- Reaproveita a validação do usuário CONSULTA e o histórico existente.
create or replace function public.mrp_avulsa_garantia_resultado_seguro(
  p_item bigint,p_actor uuid,p_resultado text
) returns jsonb
language plpgsql security definer set search_path=public as $$
declare
  v_registro record;
begin
  if p_resultado not in ('AGUARDANDO_RETORNO','UTILIZADO','DEVOLVIDO') then
    raise exception 'RESULTADO_INVALIDO';
  end if;
  select i.id,i.pedido_id,p.criado_por,p.finalidade,p.estado,i.destino_garantia
    into v_registro
    from public.mrp_solicitacoes_avulsas i
    join public.mrp_avulsas_pedidos p on p.id=i.pedido_id
    where i.id=p_item for update of i;
  if not found or v_registro.criado_por<>p_actor
       or v_registro.finalidade<>'GARANTIA'
       or v_registro.estado<>'ENTREGUE' then
    raise exception 'ITEM_GARANTIA_NAO_DISPONIVEL';
  end if;
  if not exists (select 1 from public.user_roles
                 where user_id=p_actor and role='CONSULTA') then
    raise exception 'CONSULTA_OBRIGATORIA';
  end if;
  if v_registro.destino_garantia is not distinct from p_resultado then
    return jsonb_build_object('item_id',p_item,'destino_garantia',p_resultado,'alterado',false);
  end if;
  update public.mrp_solicitacoes_avulsas
     set destino_garantia=p_resultado,
         destino_garantia_em=now(),
         destino_garantia_por=p_actor
   where id=p_item;
  insert into public.mrp_avulsas_eventos(pedido_id,item_id,evento,autor)
    values(v_registro.pedido_id,p_item,'GARANTIA_'||p_resultado,p_actor);
  return jsonb_build_object('item_id',p_item,'destino_garantia',p_resultado,'alterado',true);
end;
$$;
revoke all on function public.mrp_avulsa_garantia_resultado_seguro(bigint,uuid,text)
  from public,anon,authenticated;
grant execute on function public.mrp_avulsa_garantia_resultado_seguro(bigint,uuid,text)
  to service_role;
