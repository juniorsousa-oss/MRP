-- MRP SETTA: conferência administrativa posterior à entrega física.
-- Aditivo e não destrutivo; nenhuma S.A. antiga é encerrada automaticamente.
create table if not exists public.mrp_avulsas_conferencias_finais (
  pedido_id uuid primary key references public.mrp_avulsas_pedidos(id) on delete restrict,
  procedimento text not null check (procedimento in ('EMISSAO_NF','BAIXA','TRANSFERENCIA')),
  documento_referencia text not null check (length(btrim(documento_referencia)) between 3 and 120),
  confere_materiais boolean not null check (confere_materiais is true),
  confere_movimentacao boolean not null check (confere_movimentacao is true),
  confere_documento boolean not null check (confere_documento is true),
  observacao text not null default '' check (length(observacao) <= 1000),
  confirmado_por uuid not null references auth.users(id),
  confirmado_em timestamptz not null default now()
);
create index if not exists mrp_avulsas_conferencias_finais_confirmado_em_idx
 on public.mrp_avulsas_conferencias_finais (confirmado_em desc);
alter table public.mrp_avulsas_conferencias_finais enable row level security;
revoke all on public.mrp_avulsas_conferencias_finais from public, anon, authenticated;
grant select, insert on public.mrp_avulsas_conferencias_finais to service_role;

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
  if v_procedimento not in ('EMISSAO_NF','BAIXA','TRANSFERENCIA') then
    raise exception 'PROCEDIMENTO_INVALIDO';
  end if;
  if v_pedido.finalidade = 'GARANTIA'
     and v_procedimento <> 'TRANSFERENCIA' then
    raise exception 'GARANTIA_EXIGE_TRANSFERENCIA';
  elsif v_pedido.finalidade = 'ACERTO_GERENCIAL'
     and v_procedimento not in ('BAIXA','TRANSFERENCIA') then
    raise exception 'ACERTO_EXIGE_BAIXA_OU_TRANSFERENCIA';
  elsif v_pedido.finalidade = 'TRANSFERENCIA'
     and v_procedimento <> 'EMISSAO_NF' then
    raise exception 'TRANSFERENCIA_ENTRE_FILIAIS_EXIGE_NF';
  elsif v_pedido.finalidade not in ('GARANTIA','ACERTO_GERENCIAL','TRANSFERENCIA') then
    raise exception 'FINALIDADE_NAO_SUPORTADA';
  end if;

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
revoke all on function public.mrp_avulsa_conferencia_final_seguro(
 uuid,uuid,text,text,boolean,boolean,boolean,text
) from public, anon, authenticated;
grant execute on function public.mrp_avulsa_conferencia_final_seguro(
 uuid,uuid,text,text,boolean,boolean,boolean,text
) to service_role;
comment on table public.mrp_avulsas_conferencias_finais is
'Conferência final ADMIN com evidência documental; estado operacional ENTREGUE permanece inalterado.';
