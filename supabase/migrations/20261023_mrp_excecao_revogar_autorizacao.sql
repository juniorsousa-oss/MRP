-- Permite cancelar aprovação ainda não convertida em S.A., com motivo registrado.
create or replace function public.mrp_excecao_decidir_seguro(
 p_id uuid,p_actor uuid,p_decisao text,
 p_autorizador text,p_referencia text,p_projeto_op text,p_observacao text,
 p_snapshot_id bigint,p_saldo numeric
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_req public.mrp_avulsas_excecoes%rowtype;v_latest bigint;v_normal numeric;v_aprovado numeric;
begin
 if not exists(select 1 from public.user_roles where user_id=p_actor and role='ADMIN')
 then raise exception 'ADMIN_REQUIRED';end if;
 perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
 select * into v_req from public.mrp_avulsas_excecoes where id=p_id for update;
 if not found then raise exception 'EXCECAO_NAO_ENCONTRADA';end if;
 if v_req.situacao not in ('PENDENTE','APROVADA') then raise exception 'EXCECAO_JA_TRATADA';end if;
 if p_decisao='RECUSAR' then
   if length(trim(coalesce(p_observacao,'')))<5 then raise exception 'MOTIVO_OBRIGATORIO';end if;
   update public.mrp_avulsas_excecoes set situacao='RECUSADA',decidido_por=p_actor,
     decidido_em=now(),administracao_observacao=left(trim(p_observacao),1000) where id=p_id;
   return jsonb_build_object('id',p_id,'situacao','RECUSADA');
 end if;
 if p_decisao<>'APROVAR' then raise exception 'DECISAO_INVALIDA';end if;
 if v_req.situacao<>'PENDENTE' then raise exception 'AUTORIZACAO_JA_DECIDIDA';end if;
 if length(trim(coalesce(p_autorizador,'')))<3
 or length(trim(coalesce(p_referencia,'')))<3
 or length(trim(coalesce(p_projeto_op,'')))<3
 then raise exception 'AUTORIZACAO_E_PROJETO_OBRIGATORIOS';end if;
 select id into v_latest from public.mrp_snapshots order by created_at desc,id desc limit 1;
 if v_latest is distinct from p_snapshot_id or v_req.snapshot_id<>v_latest
 then raise exception 'MRP_ALTERADO_REQUER_NOVA_SOLICITACAO';end if;
 if p_saldo is null or p_saldo<=0 or p_saldo<v_req.quantidade
 then raise exception 'SALDO_FISICO_INSUFICIENTE';end if;
 select coalesce(sum(quantidade),0) into v_normal
 from public.mrp_solicitacoes_avulsas
 where codigo=v_req.codigo and
 (status='ABERTA' or (status='ATENDIDA' and snapshot_id=v_latest));
 select coalesce(sum(quantidade),0) into v_aprovado
 from public.mrp_avulsas_excecoes
 where codigo=v_req.codigo and snapshot_id=v_latest
 and situacao in ('APROVADA','EFETIVADA');
 -- Efetivadas também estão em solicitações e precisam ser contadas apenas uma vez.
 select coalesce(sum(e.quantidade),0) into v_aprovado
 from public.mrp_avulsas_excecoes e
 where e.codigo=v_req.codigo and e.snapshot_id=v_latest and e.situacao='APROVADA';
 if v_req.quantidade > p_saldo-v_normal-v_aprovado+0.000001
 then raise exception 'ESTOQUE_FISICO_JA_COMPROMETIDO (ESTOQUE %, SOLICITACOES %, AUTORIZACOES %)',
 p_saldo,v_normal,v_aprovado;end if;
 update public.mrp_avulsas_excecoes set situacao='APROVADA',
    autoridade_nome=left(trim(p_autorizador),180),
    autorizacao_referencia=left(trim(p_referencia),250),
    projeto_op_impactado=left(trim(p_projeto_op),250),
    administracao_observacao=nullif(left(trim(coalesce(p_observacao,'')),1000),''),
    decidido_por=p_actor,decidido_em=now(),saldo_fisico_referencia=p_saldo
 where id=p_id;
 return jsonb_build_object('id',p_id,'situacao','APROVADA');
end;$$;

