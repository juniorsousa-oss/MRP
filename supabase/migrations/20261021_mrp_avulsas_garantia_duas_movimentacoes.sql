-- MRP SETTA: regularização da garantia em dois movimentos reais com evidência por item.
-- O registro é prova declarada de movimentação no Protheus; nenhuma movimentação ERP automática.
create table if not exists public.mrp_avulsas_garantia_regularizacoes (
  item_id bigint primary key references public.mrp_solicitacoes_avulsas(id) on delete restrict,
  pedido_id uuid not null references public.mrp_avulsas_pedidos(id) on delete restrict,
  astec_documento text not null check (length(btrim(astec_documento)) between 3 and 120),
  astec_confirmado_por uuid not null references auth.users(id),
  astec_confirmado_em timestamptz not null default now(),
  movimento_final_tipo text check (movimento_final_tipo in ('BAIXA','TRANSFERENCIA_ESTOQUE')),
  movimento_final_documento text check (movimento_final_documento is null or length(btrim(movimento_final_documento)) between 3 and 120),
  movimento_final_confirmado_por uuid references auth.users(id),
  movimento_final_confirmado_em timestamptz,
  constraint garantia_movimento_completo_check check (
   (movimento_final_tipo is null and movimento_final_documento is null
      and movimento_final_confirmado_por is null and movimento_final_confirmado_em is null)
    or
   (movimento_final_tipo is not null and movimento_final_documento is not null
      and movimento_final_confirmado_por is not null and movimento_final_confirmado_em is not null)
  )
);
create index if not exists mrp_avulsas_garantia_regularizacoes_pedido_idx
 on public.mrp_avulsas_garantia_regularizacoes(pedido_id);
alter table public.mrp_avulsas_garantia_regularizacoes enable row level security;
revoke all on table public.mrp_avulsas_garantia_regularizacoes from public, anon, authenticated;
grant select, insert, update on table public.mrp_avulsas_garantia_regularizacoes to service_role;

-- Uma S.A. possui um encaminhamento à ASTEC comum aos materiais; registro atômico.
create or replace function public.mrp_avulsa_garantia_ast_ec_seguro(
  p_pedido_id uuid,p_actor uuid,p_documento text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
 v_pedido public.mrp_avulsas_pedidos%rowtype;
 v_doc text:=btrim(coalesce(p_documento,''));
 v_qtd int;
begin
 if not exists(select 1 from public.user_roles where user_id=p_actor and upper(role)='ADMIN') then
   raise exception 'ADMIN_REQUIRED';end if;
 select * into v_pedido from public.mrp_avulsas_pedidos where id=p_pedido_id for update;
 if not found or v_pedido.finalidade<>'GARANTIA' or v_pedido.estado<>'ENTREGUE'
   or v_pedido.entregue_em is null then raise exception 'GARANTIA_NAO_ENTREGUE';end if;
 if length(v_doc) not between 3 and 120 then raise exception 'DOCUMENTO_ASTEC_OBRIGATORIO';end if;
 if exists(select 1 from public.mrp_avulsas_conferencias_finais where pedido_id=p_pedido_id) then
   raise exception 'CONFERENCIA_FINAL_JA_CONCLUIDA';end if;
 if exists(select 1 from public.mrp_avulsas_garantia_regularizacoes where pedido_id=p_pedido_id) then
   raise exception 'ENCAMINHAMENTO_ASTEC_JA_REGISTRADO';end if;
 select count(*) into v_qtd from public.mrp_solicitacoes_avulsas where pedido_id=p_pedido_id;
 if v_qtd=0 then raise exception 'PEDIDO_SEM_MATERIAIS'; end if;
 insert into public.mrp_avulsas_garantia_regularizacoes(
   item_id,pedido_id,astec_documento,astec_confirmado_por)
 select id,pedido_id,v_doc,p_actor from public.mrp_solicitacoes_avulsas
 where pedido_id=p_pedido_id;
 insert into public.mrp_avulsas_eventos(pedido_id,evento,autor,observacao)
 values(p_pedido_id,'GARANTIA_ASTEC',p_actor,'Encaminhamento ASTEC | Protheus: '||v_doc);
 return jsonb_build_object('pedido_id',p_pedido_id,'itens',v_qtd,'astec_documento',v_doc);
end;$$;

-- Após a ASTEC informar se houve uso ou devolução, o ADMIN comprova o movimento correto por item.
create or replace function public.mrp_avulsa_garantia_movimento_final_seguro(
  p_item_id bigint,p_actor uuid,p_documento text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare
 v_item record;
 v_reg public.mrp_avulsas_garantia_regularizacoes%rowtype;
 v_tipo text;
 v_doc text:=btrim(coalesce(p_documento,''));
begin
 if not exists(select 1 from public.user_roles where user_id=p_actor and upper(role)='ADMIN') then
   raise exception 'ADMIN_REQUIRED';end if;
 select i.id,i.pedido_id,i.destino_garantia,p.finalidade,p.estado,p.entregue_em
 into v_item from public.mrp_solicitacoes_avulsas i
 join public.mrp_avulsas_pedidos p on p.id=i.pedido_id
 where i.id=p_item_id for update of i;
 if not found or v_item.finalidade<>'GARANTIA' or v_item.estado<>'ENTREGUE'
    or v_item.entregue_em is null then raise exception 'ITEM_GARANTIA_NAO_ENTREGUE';end if;
 if v_item.destino_garantia not in ('UTILIZADO','DEVOLVIDO') or v_item.destino_garantia is null then
   raise exception 'AGUARDANDO_RESULTADO_DA_ASTEC';end if;
 select * into v_reg from public.mrp_avulsas_garantia_regularizacoes
 where item_id=p_item_id and pedido_id=v_item.pedido_id for update;
 if not found then raise exception 'ENCAMINHAMENTO_ASTEC_NAO_REGISTRADO';end if;
 if v_reg.movimento_final_documento is not null then raise exception 'MOVIMENTACAO_FINAL_JA_CONFIRMADA';end if;
 if exists(select 1 from public.mrp_avulsas_conferencias_finais where pedido_id=v_item.pedido_id) then
   raise exception 'CONFERENCIA_FINAL_JA_CONCLUIDA';end if;
 if length(v_doc) not between 3 and 120 then raise exception 'DOCUMENTO_MOVIMENTO_OBRIGATORIO';end if;
 v_tipo:=case when v_item.destino_garantia='UTILIZADO' then 'BAIXA' else 'TRANSFERENCIA_ESTOQUE' end;
 update public.mrp_avulsas_garantia_regularizacoes set
   movimento_final_tipo=v_tipo,movimento_final_documento=v_doc,
   movimento_final_confirmado_por=p_actor,movimento_final_confirmado_em=now()
 where item_id=p_item_id;
 insert into public.mrp_avulsas_eventos(pedido_id,item_id,evento,autor,observacao)
 values(v_item.pedido_id,p_item_id,'GARANTIA_'||v_tipo,p_actor,'Documento Protheus: '||v_doc);
 return jsonb_build_object('item_id',p_item_id,'pedido_id',v_item.pedido_id,
    'movimento_final_tipo',v_tipo,'movimento_final_documento',v_doc);
end;$$;

-- Não permitir resultado de uso/devolução antes de ASTEC, ou mudar decisão depois da movimentação.
create or replace function public.mrp_avulsa_garantia_resultado_seguro(
 p_item bigint,p_actor uuid,p_resultado text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_registro record;
begin
 if p_resultado not in ('AGUARDANDO_RETORNO','UTILIZADO','DEVOLVIDO') then
    raise exception 'RESULTADO_INVALIDO';end if;
 select i.id,i.pedido_id,p.criado_por,p.finalidade,p.estado,
        i.destino_garantia,g.item_id as astec_id,g.movimento_final_documento
 into v_registro from public.mrp_solicitacoes_avulsas i
 join public.mrp_avulsas_pedidos p on p.id=i.pedido_id
 left join public.mrp_avulsas_garantia_regularizacoes g on g.item_id=i.id
 where i.id=p_item for update of i;
 if not found or v_registro.criado_por<>p_actor or
    v_registro.finalidade<>'GARANTIA' or v_registro.estado<>'ENTREGUE' then
   raise exception 'ITEM_GARANTIA_NAO_DISPONIVEL';end if;
 if not exists(select 1 from public.user_roles where user_id=p_actor and upper(role)='CONSULTA') then
    raise exception 'CONSULTA_OBRIGATORIA';end if;
 if v_registro.destino_garantia is not distinct from p_resultado then
    return jsonb_build_object('item_id',p_item,'destino_garantia',p_resultado,'alterado',false);end if;
 if v_registro.astec_id is null then raise exception 'AGUARDANDO_ENDERECAMENTO_ASTEC';end if;
 if v_registro.movimento_final_documento is not null then
    raise exception 'RESULTADO_BLOQUEADO_APOS_MOVIMENTACAO_FINAL';end if;
 if exists(select 1 from public.mrp_avulsas_conferencias_finais where pedido_id=v_registro.pedido_id) then
    raise exception 'CONFERENCIA_FINAL_JA_CONCLUIDA';end if;
 update public.mrp_solicitacoes_avulsas set
   destino_garantia=p_resultado,destino_garantia_em=now(),destino_garantia_por=p_actor
 where id=p_item;
 insert into public.mrp_avulsas_eventos(pedido_id,item_id,evento,autor)
 values(v_registro.pedido_id,p_item,'GARANTIA_'||p_resultado,p_actor);
 return jsonb_build_object('item_id',p_item,'destino_garantia',p_resultado,'alterado',true);
end;$$;

-- Encerramento geral de GARANTIA permitido apenas quando 100% dos itens têm ASTEC,
-- destino informado e respectiva baixa ou retorno ao estoque com documento.
alter table public.mrp_avulsas_conferencias_finais
 drop constraint if exists mrp_avulsas_conferencias_finais_procedimento_check;
alter table public.mrp_avulsas_conferencias_finais
 add constraint mrp_avulsas_conferencias_finais_procedimento_check
 check (procedimento in ('EMISSAO_NF','BAIXA','TRANSFERENCIA','REGULARIZACAO_GARANTIA'));
create or replace function public.mrp_avulsa_conferencia_final_seguro(
  p_pedido_id uuid,
  p_actor uuid,
  p_procedimento text,
  p_documento text,
  p_confere_materiais boolean,
  p_confere_movimentacao boolean,
  p_confere_documento boolean,
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
    where user_id = p_actor and upper(role) = 'ADMIN'
  ) then raise exception 'ADMIN_REQUIRED'; end if;

  select * into v_pedido from public.mrp_avulsas_pedidos
    where id = p_pedido_id for update;
  if not found then raise exception 'PEDIDO_NAO_ENCONTRADO'; end if;
  if v_pedido.estado <> 'ENTREGUE' or v_pedido.entregue_em is null then
    raise exception 'ENTREGA_FISICA_NAO_CONFIRMADA';
  end if;
  if exists (select 1 from public.mrp_avulsas_conferencias_finais
             where pedido_id = p_pedido_id) then
    raise exception 'CONFERENCIA_FINAL_JA_CONCLUIDA';
  end if;
  if v_procedimento not in ('EMISSAO_NF','BAIXA','TRANSFERENCIA','REGULARIZACAO_GARANTIA') then
    raise exception 'PROCEDIMENTO_INVALIDO';
  end if;
  if v_pedido.finalidade = 'GARANTIA'
     and v_procedimento <> 'REGULARIZACAO_GARANTIA' then
    raise exception 'GARANTIA_EXIGE_REGULARIZACAO_COMPLETA';
  elsif v_pedido.finalidade = 'ACERTO_GERENCIAL'
     and v_procedimento not in ('BAIXA','TRANSFERENCIA') then
    raise exception 'ACERTO_EXIGE_BAIXA_OU_TRANSFERENCIA';
  elsif v_pedido.finalidade = 'TRANSFERENCIA'
     and v_procedimento <> 'EMISSAO_NF' then
    raise exception 'TRANSFERENCIA_ENTRE_FILIAIS_EXIGE_NF';
  elsif v_pedido.finalidade not in ('GARANTIA','ACERTO_GERENCIAL','TRANSFERENCIA') then
    raise exception 'FINALIDADE_NAO_SUPORTADA';
  end if;

  if v_pedido.finalidade = 'GARANTIA' and exists (
    select 1 from public.mrp_solicitacoes_avulsas i
    left join public.mrp_avulsas_garantia_regularizacoes g on g.item_id=i.id and g.pedido_id=i.pedido_id
    where i.pedido_id=p_pedido_id and
      (g.item_id is null or g.astec_documento is null
        or i.destino_garantia not in ('UTILIZADO','DEVOLVIDO')
        or g.movimento_final_documento is null or g.movimento_final_tipo is distinct from
         case when i.destino_garantia='UTILIZADO' then 'BAIXA'
              when i.destino_garantia='DEVOLVIDO' then 'TRANSFERENCIA_ESTOQUE'
              else null end)
  ) then raise exception 'GARANTIA_PENDENTE_ASTEC_DESTINACAO_OU_MOVIMENTACAO_FINAL'; end if;

  if length(v_documento) < 3 or length(v_documento) > 120 then
    raise exception 'DOCUMENTO_PROTHEUS_OBRIGATORIO_3_A_120_CARACTERES';
  end if;
  if length(v_obs) > 1000 then
    raise exception 'OBSERVACAO_MAXIMO_1000_CARACTERES';
  end if;
  if not (coalesce(p_confere_materiais,false)
          and coalesce(p_confere_movimentacao,false)
          and coalesce(p_confere_documento,false)) then
    raise exception 'CHECKLIST_FINAL_INCOMPLETO';
  end if;
  if not exists (
    select 1 from public.mrp_solicitacoes_avulsas
    where pedido_id=p_pedido_id
  ) then raise exception 'PEDIDO_SEM_MATERIAIS'; end if;

  insert into public.mrp_avulsas_conferencias_finais(
    pedido_id,procedimento,documento_referencia,
    confere_materiais,confere_movimentacao,confere_documento,
    observacao,confirmado_por,confirmado_em
  ) values (
    p_pedido_id,v_procedimento,v_documento,
    true,true,true,v_obs,p_actor,v_agora
  );
  insert into public.mrp_avulsas_eventos(pedido_id,evento,autor,observacao)
  values (
    p_pedido_id,'CONFERENCIA_FINAL',p_actor,
    left('Procedimento: '||v_procedimento||' | Documento: '||v_documento||
         case when v_obs<>'' then ' | '||v_obs else '' end,1000)
  );
  return jsonb_build_object(
    'pedido_id', p_pedido_id,
    'status_administrativo', 'CONCLUIDO',
    'procedimento', v_procedimento,
    'documento_referencia', v_documento,
    'confirmado_por', p_actor,
    'confirmado_em', v_agora
  );
end;
$fn$;

revoke all on function public.mrp_avulsa_garantia_ast_ec_seguro(uuid,uuid,text) from public,anon,authenticated;
revoke all on function public.mrp_avulsa_garantia_movimento_final_seguro(bigint,uuid,text) from public,anon,authenticated;
revoke all on function public.mrp_avulsa_garantia_resultado_seguro(bigint,uuid,text) from public,anon,authenticated;
grant execute on function public.mrp_avulsa_garantia_ast_ec_seguro(uuid,uuid,text) to service_role;
grant execute on function public.mrp_avulsa_garantia_movimento_final_seguro(bigint,uuid,text) to service_role;
grant execute on function public.mrp_avulsa_garantia_resultado_seguro(bigint,uuid,text) to service_role;
comment on table public.mrp_avulsas_garantia_regularizacoes is
'Encaminhamento à ASTEC, desfecho do solicitante e regularização Protheus por item; gestor encerra somente após 100%.';
