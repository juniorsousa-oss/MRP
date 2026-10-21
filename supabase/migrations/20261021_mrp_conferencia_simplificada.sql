-- SETTA MRP | encerramento administrativo simplificado
-- Confirma somente o procedimento e o número de documento; mantém auditoria
-- de responsável/data. Os antigos checkboxes permanecem historicamente íntegros.
-- Novas confirmações simples NÃO declaram conferência individual inexistente.
alter table public.mrp_avulsas_conferencias_finais
  drop constraint if exists mrp_avulsas_conferencias_finais_confere_materiais_check;
alter table public.mrp_avulsas_conferencias_finais
  drop constraint if exists mrp_avulsas_conferencias_finais_confere_movimentacao_check;
alter table public.mrp_avulsas_conferencias_finais
  drop constraint if exists mrp_avulsas_conferencias_finais_confere_documento_check;
alter table public.mrp_avulsas_conferencias_finais
  drop constraint if exists mrp_avulsas_conferencias_finais_documento_referencia_check;
alter table public.mrp_avulsas_conferencias_finais
  add constraint mrp_avulsas_conferencias_finais_documento_referencia_check
  check (documento_referencia is null
    or length(btrim(documento_referencia)) between 1 and 120);

create or replace function public.mrp_avulsa_conferencia_simples_seguro(
  p_pedido_id uuid,
  p_actor uuid,
  p_procedimento text,
  p_documento text,
  p_observacao text default ''
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $fn$
declare
  v_pedido public.mrp_avulsas_pedidos%rowtype;
  v_procedimento text := upper(btrim(coalesce(p_procedimento,'')));
  v_documento text := btrim(coalesce(p_documento,''));
  v_obs text := btrim(coalesce(p_observacao,''));
  v_agora timestamptz := now();
begin
  if not exists (
    select 1 from public.user_roles
    where user_id=p_actor and upper(role)='ADMIN'
  ) then raise exception 'ADMIN_REQUIRED'; end if;

  select * into v_pedido from public.mrp_avulsas_pedidos
  where id=p_pedido_id for update;
  if not found then raise exception 'PEDIDO_NAO_ENCONTRADO'; end if;
  if v_pedido.estado<>'ENTREGUE' or v_pedido.entregue_em is null then
    raise exception 'ENTREGA_FISICA_NAO_CONFIRMADA';
  end if;
  if exists (select 1 from public.mrp_avulsas_conferencias_finais
             where pedido_id=p_pedido_id) then
    raise exception 'CONFERENCIA_FINAL_JA_CONCLUIDA';
  end if;

  -- Garantias têm as 3 etapas específicas: ASTEC/resultado/baixa ou retorno.
  if v_pedido.finalidade='GARANTIA' then
    raise exception 'GARANTIA_EXIGE_FLUXO_ASTEC';
  elsif v_pedido.finalidade='TRANSFERENCIA' and v_procedimento<>'EMISSAO_NF' then
    raise exception 'TRANSFERENCIA_ENTRE_FILIAIS_EXIGE_NF';
  elsif v_pedido.finalidade='ACERTO_GERENCIAL'
    and v_procedimento not in ('BAIXA','TRANSFERENCIA') then
    raise exception 'ACERTO_EXIGE_BAIXA_OU_TRANSFERENCIA';
  elsif v_pedido.finalidade not in ('TRANSFERENCIA','ACERTO_GERENCIAL') then
    raise exception 'FINALIDADE_NAO_SUPORTADA';
  end if;

  if length(v_documento) not between 1 and 120 then
    raise exception 'NUMERO_DOCUMENTO_OBRIGATORIO';
  end if;
  if length(v_obs)>1000 then
    raise exception 'OBSERVACAO_MAXIMO_1000_CARACTERES';
  end if;
  if not exists(select 1 from public.mrp_solicitacoes_avulsas
                where pedido_id=p_pedido_id) then
    raise exception 'PEDIDO_SEM_MATERIAIS';
  end if;

  insert into public.mrp_avulsas_conferencias_finais(
    pedido_id,procedimento,documento_referencia,
    confere_materiais,confere_movimentacao,confere_documento,
    observacao,confirmado_por,confirmado_em
  ) values (
    p_pedido_id,v_procedimento,v_documento,
    false,false,false, v_obs,p_actor,v_agora
  );
  insert into public.mrp_avulsas_eventos(pedido_id,evento,autor,observacao)
  values(p_pedido_id,'CONFERENCIA_FINAL',p_actor,
    left('Confirmação simples | Procedimento: '||v_procedimento||
         ' | Documento: '||v_documento||
         case when v_obs<>'' then ' | '||v_obs else '' end,1000));
  return jsonb_build_object(
    'pedido_id',p_pedido_id,'status_administrativo','CONCLUIDO',
    'procedimento',v_procedimento,'documento_referencia',v_documento,
    'confirmado_por',p_actor,'confirmado_em',v_agora
  );
end;
$fn$;

revoke all on function public.mrp_avulsa_conferencia_simples_seguro(
  uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.mrp_avulsa_conferencia_simples_seguro(
  uuid,uuid,text,text,text) to service_role;

comment on function public.mrp_avulsa_conferencia_simples_seguro(uuid,uuid,text,text,text)
is 'ADMIN confirma procedimento e documento no MRP sem marcar checklists não realizados; rastreia usuário e data.';
