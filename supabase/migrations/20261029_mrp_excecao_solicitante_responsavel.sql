-- Exceção: solicitante editável como no fluxo normal e autor da autorização
-- registrado na origem; solicitações antigas preservadas (coluna anulável).
alter table public.mrp_avulsas_excecoes
 add column if not exists responsavel_autorizacao_informado text;
alter table public.mrp_avulsas_excecoes
 drop constraint if exists mrp_excecao_responsavel_autorizacao_valido;
alter table public.mrp_avulsas_excecoes
 add constraint mrp_excecao_responsavel_autorizacao_valido
 check (responsavel_autorizacao_informado is null or
  length(btrim(responsavel_autorizacao_informado)) between 3 and 180);

create or replace function public.mrp_excecao_solicitar_identificada_seguro(
 p_id uuid,p_snapshot_id bigint,p_actor uuid,p_email text,
 p_codigo text,p_descricao text,p_quantidade numeric,
 p_saldo numeric,p_div numeric,p_justificativa text,
 p_finalidade text,p_psys text,p_cr text,p_aprovador text,
 p_responsavel_autorizacao text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_latest bigint;v_exists public.mrp_avulsas_excecoes%rowtype;
begin
 if not exists(select 1 from public.user_roles where user_id=p_actor and role='CONSULTA')
 then raise exception 'CONSULTA_REQUIRED';end if;
 if p_id is null or p_actor is null or p_snapshot_id is null then raise exception 'DADOS_INVALIDOS';end if;
 select * into v_exists from public.mrp_avulsas_excecoes where id=p_id;
 if found then
   if v_exists.criado_por<>p_actor or v_exists.codigo<>p_codigo
      or v_exists.quantidade<>p_quantidade
      or v_exists.solicitante<>lower(trim(p_email))
      or v_exists.responsavel_autorizacao_informado is distinct from trim(p_responsavel_autorizacao)
      or v_exists.justificativa<>trim(p_justificativa)
      then raise exception 'IDENTIFICADOR_REUTILIZADO';end if;
   return jsonb_build_object('id',p_id,'situacao',v_exists.situacao,'repetido',true);
 end if;
 select id into v_latest from public.mrp_snapshots order by created_at desc,id desc limit 1;
 if v_latest is distinct from p_snapshot_id then raise exception 'MRP_DESATUALIZADO_RECARREGAR';end if;
 if p_codigo !~ '^[0-9]{8}$' or p_quantidade is null or p_quantidade <= 0
 or p_quantidade <> round(p_quantidade,3) or p_saldo is null or p_saldo <= 0
 or p_quantidade>p_saldo then raise exception 'SALDO_FISICO_INSUFICIENTE';end if;
 if length(trim(coalesce(p_justificativa,''))) not between 10 and 1000 then
 raise exception 'JUSTIFICATIVA_OBRIGATORIA';end if;
 if length(trim(coalesce(p_responsavel_autorizacao,''))) not between 3 and 180
 then raise exception 'RESPONSAVEL_AUTORIZACAO_OBRIGATORIO';end if;
 if length(trim(coalesce(p_email,'')))>180 or lower(trim(coalesce(p_email,'')))
    !~ '^[a-z0-9][a-z0-9._%+-]*[.][a-z0-9._%+-]+@gruposetta[.]com$' then
 raise exception 'EMAIL_CORPORATIVO_INVALIDO';end if;
 if p_finalidade not in ('GARANTIA','ACERTO_GERENCIAL','TRANSFERENCIA')
 then raise exception 'FINALIDADE_INVALIDA';end if;
 if p_finalidade='GARANTIA' and length(trim(coalesce(p_psys,'')))<2
 then raise exception 'PSYS_OBRIGATORIOS';end if;
 if p_finalidade='ACERTO_GERENCIAL' and
  (length(trim(coalesce(p_cr,'')))<1 or length(trim(coalesce(p_aprovador,'')))<2)
 then raise exception 'CR_E_APROVADOR_OBRIGATORIOS';end if;
 insert into public.mrp_avulsas_excecoes(
   id,snapshot_id,criado_por,solicitante,codigo,descricao,quantidade,
   justificativa,finalidade,psys,cr,aprovador,saldo_fisico_referencia,div_referencia,
   responsavel_autorizacao_informado
 ) values(
   p_id,p_snapshot_id,p_actor,lower(trim(p_email)),p_codigo,left(coalesce(p_descricao,''),500),
   p_quantidade,trim(p_justificativa),p_finalidade,
   case when p_finalidade='GARANTIA' then nullif(trim(coalesce(p_psys,'')),'') end,
   case when p_finalidade='ACERTO_GERENCIAL' then nullif(trim(coalesce(p_cr,'')),'') end,
   case when p_finalidade='ACERTO_GERENCIAL' then nullif(trim(coalesce(p_aprovador,'')),'') end,
   p_saldo,coalesce(p_div,0),trim(p_responsavel_autorizacao)
 );
 return jsonb_build_object('id',p_id,'situacao','PENDENTE','repetido',false);
end;$$;

revoke all on function public.mrp_excecao_solicitar_identificada_seguro(uuid,bigint,uuid,text,text,text,numeric,numeric,numeric,text,text,text,text,text,text)
 from public,anon,authenticated;
grant execute on function public.mrp_excecao_solicitar_identificada_seguro(uuid,bigint,uuid,text,text,text,numeric,numeric,numeric,text,text,text,text,text,text)
 to service_role;
