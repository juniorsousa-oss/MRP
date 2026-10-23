
-- Exceções autorizadas de reservas: não modifica a regra de sobrantes.
create table if not exists public.mrp_avulsas_excecoes (
 id uuid primary key,
 snapshot_id bigint not null references public.mrp_snapshots(id),
 criado_por uuid not null references auth.users(id),
 solicitante text not null,
 codigo text not null check(codigo ~ '^[0-9]{8}$'),
 descricao text not null default '',
 quantidade numeric(18,3) not null check(quantidade > 0),
 justificativa text not null check(length(btrim(justificativa)) between 10 and 1000),
 finalidade text not null check(finalidade in ('GARANTIA','ACERTO_GERENCIAL','TRANSFERENCIA')),
 psys text, cr text, aprovador text,
 saldo_fisico_referencia numeric(18,3) not null check(saldo_fisico_referencia > 0),
 div_referencia numeric(18,3) not null,
 situacao text not null default 'PENDENTE' check(situacao in
    ('PENDENTE','APROVADA','RECUSADA','EFETIVADA')),
 autoridade_nome text, autorizacao_referencia text, projeto_op_impactado text,
 administracao_observacao text,
 decidido_por uuid references auth.users(id), decidido_em timestamptz,
 regularizacao_referencia text,
 regularizado_por uuid references auth.users(id), regularizado_em timestamptz,
 pedido_id uuid unique references public.mrp_avulsas_pedidos(id),
 criado_em timestamptz not null default now(),
 constraint excecao_justifica_aprovacao check(
    situacao not in ('APROVADA','EFETIVADA') or
    (decidido_por is not null and decidido_em is not null
     and length(btrim(coalesce(autoridade_nome,'')))>=3
     and length(btrim(coalesce(autorizacao_referencia,'')))>=3
     and length(btrim(coalesce(projeto_op_impactado,'')))>=3)),
 constraint excecao_regularizacao check(
    situacao <> 'EFETIVADA' or
    (pedido_id is not null and regularizado_por is not null
     and regularizado_em is not null
     and length(btrim(coalesce(regularizacao_referencia,'')))>=3))
);
create index if not exists mrp_excecoes_codigo_situacao_idx
 on public.mrp_avulsas_excecoes(codigo,situacao,snapshot_id);
create index if not exists mrp_excecoes_usuario_idx
 on public.mrp_avulsas_excecoes(criado_por,criado_em desc);
alter table public.mrp_avulsas_excecoes enable row level security;
revoke all on public.mrp_avulsas_excecoes from public,anon,authenticated;
grant select,insert,update on public.mrp_avulsas_excecoes to service_role;

alter table public.mrp_avulsas_pedidos add column if not exists excecao_id uuid
  references public.mrp_avulsas_excecoes(id);
create unique index if not exists mrp_pedidos_excecao_unica_idx on
  public.mrp_avulsas_pedidos(excecao_id) where excecao_id is not null;

-- Somente service_role pode executar: API autentica sessão antes de repassar ator.
create or replace function public.mrp_excecao_solicitar_seguro(
 p_id uuid,p_snapshot_id bigint,p_actor uuid,p_email text,
 p_codigo text,p_descricao text,p_quantidade numeric,
 p_saldo numeric,p_div numeric,p_justificativa text,
 p_finalidade text,p_psys text,p_cr text,p_aprovador text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_latest bigint;v_exists public.mrp_avulsas_excecoes%rowtype;
begin
 if not exists(select 1 from public.user_roles where user_id=p_actor and role='CONSULTA')
 then raise exception 'CONSULTA_REQUIRED';end if;
 if p_id is null or p_actor is null or p_snapshot_id is null then raise exception 'DADOS_INVALIDOS';end if;
 select * into v_exists from public.mrp_avulsas_excecoes where id=p_id;
 if found then
   if v_exists.criado_por<>p_actor or v_exists.codigo<>p_codigo
      or v_exists.quantidade<>p_quantidade then raise exception 'IDENTIFICADOR_REUTILIZADO';end if;
   return jsonb_build_object('id',p_id,'situacao',v_exists.situacao,'repetido',true);
 end if;
 select id into v_latest from public.mrp_snapshots order by created_at desc,id desc limit 1;
 if v_latest is distinct from p_snapshot_id then raise exception 'MRP_DESATUALIZADO_RECARREGAR';end if;
 if p_codigo !~ '^[0-9]{8}$' or p_quantidade is null or p_quantidade <= 0
 or p_quantidade <> round(p_quantidade,3) or p_saldo is null or p_saldo <= 0
 or p_quantidade>p_saldo then raise exception 'SALDO_FISICO_INSUFICIENTE';end if;
 if length(trim(coalesce(p_justificativa,''))) not between 10 and 1000 then
 raise exception 'JUSTIFICATIVA_OBRIGATORIA';end if;
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
   justificativa,finalidade,psys,cr,aprovador,saldo_fisico_referencia,div_referencia
 ) values(
   p_id,p_snapshot_id,p_actor,lower(trim(p_email)),p_codigo,left(coalesce(p_descricao,''),500),
   p_quantidade,trim(p_justificativa),p_finalidade,
   case when p_finalidade='GARANTIA' then nullif(trim(coalesce(p_psys,'')),'') end,
   case when p_finalidade='ACERTO_GERENCIAL' then nullif(trim(coalesce(p_cr,'')),'') end,
   case when p_finalidade='ACERTO_GERENCIAL' then nullif(trim(coalesce(p_aprovador,'')),'') end,
   p_saldo,coalesce(p_div,0)
 );
 return jsonb_build_object('id',p_id,'situacao','PENDENTE','repetido',false);
end;$$;

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
 if v_req.situacao<>'PENDENTE' then raise exception 'EXCECAO_JA_TRATADA';end if;
 if p_decisao='RECUSAR' then
   if length(trim(coalesce(p_observacao,'')))<5 then raise exception 'MOTIVO_OBRIGATORIO';end if;
   update public.mrp_avulsas_excecoes set situacao='RECUSADA',decidido_por=p_actor,
     decidido_em=now(),administracao_observacao=left(trim(p_observacao),1000) where id=p_id;
   return jsonb_build_object('id',p_id,'situacao','RECUSADA');
 end if;
 if p_decisao<>'APROVAR' then raise exception 'DECISAO_INVALIDA';end if;
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

create or replace function public.mrp_excecao_regularizar_e_criar_seguro(
 p_id uuid,p_actor uuid,p_referencia text,p_snapshot_id bigint,p_saldo numeric
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_req public.mrp_avulsas_excecoes%rowtype;v_latest bigint;v_normal numeric;v_aprovado numeric;
 v_pedido uuid:=gen_random_uuid();v_item bigint;v_num bigint;
begin
 if not exists(select 1 from public.user_roles where user_id=p_actor and role='ADMIN')
 then raise exception 'ADMIN_REQUIRED';end if;
 perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
 select * into v_req from public.mrp_avulsas_excecoes where id=p_id for update;
 if not found then raise exception 'EXCECAO_NAO_ENCONTRADA';end if;
 if v_req.situacao='EFETIVADA' and v_req.pedido_id is not null then
   return jsonb_build_object('pedido_id',v_req.pedido_id,'situacao','EFETIVADA','repetido',true);
 end if;
 if v_req.situacao<>'APROVADA' then raise exception 'EXCECAO_NAO_APROVADA';end if;
 if length(trim(coalesce(p_referencia,'')))<3 then
 raise exception 'DOCUMENTO_DE_REGULARIZACAO_OBRIGATORIO';end if;
 select id into v_latest from public.mrp_snapshots order by created_at desc,id desc limit 1;
 if v_latest is distinct from p_snapshot_id or v_req.snapshot_id<>v_latest
 then raise exception 'MRP_ALTERADO_REQUER_REVALIDACAO';end if;
 if p_saldo is null or p_saldo<v_req.quantidade then
 raise exception 'SALDO_FISICO_INSUFICIENTE';end if;
 select coalesce(sum(quantidade),0) into v_normal
 from public.mrp_solicitacoes_avulsas
 where codigo=v_req.codigo and (status='ABERTA' or
 (status='ATENDIDA' and snapshot_id=v_latest));
 select coalesce(sum(quantidade),0) into v_aprovado
 from public.mrp_avulsas_excecoes
 where codigo=v_req.codigo and snapshot_id=v_latest
 and situacao='APROVADA' and id<>p_id;
 if v_req.quantidade>p_saldo-v_normal-v_aprovado+0.000001
 then raise exception 'ESTOQUE_COMPROMETIDO_ANTES_DA_REGULARIZACAO';end if;
 insert into public.mrp_avulsas_pedidos(
  id,snapshot_id,solicitante,criado_por,itens_hash,
  finalidade,psys,cr,aprovador,destino,estado,excecao_id
 ) values(
  v_pedido,v_latest,v_req.solicitante,v_req.criado_por,
  md5('EXCECAO|'||v_req.id::text),
  v_req.finalidade,v_req.psys,v_req.cr,v_req.aprovador,
  case when v_req.finalidade='TRANSFERENCIA' then 'ASTEC' end,
  'PENDENTE',v_req.id
 ) returning numero into v_num;
 insert into public.mrp_solicitacoes_avulsas(
  pedido_id,snapshot_id,codigo,descricao,quantidade,div_referencia,
  solicitante,criado_por
 ) values(
  v_pedido,v_latest,v_req.codigo,v_req.descricao,v_req.quantidade,
  v_req.quantidade,  -- Limite da exceção aprovada; DIV real permanece no registro separado.
  v_req.solicitante,v_req.criado_por
 ) returning id into v_item;
 update public.mrp_avulsas_excecoes set situacao='EFETIVADA',
  regularizacao_referencia=left(trim(p_referencia),250),
  regularizado_por=p_actor,regularizado_em=now(),pedido_id=v_pedido
 where id=p_id;
 insert into public.mrp_avulsas_eventos(pedido_id,item_id,evento,autor,observacao)
 values(v_pedido,v_item,'EXCECAO_RESERVA_LIBERADA',p_actor,
 left('Reserva excepcional autorizada: '||v_req.autorizacao_referencia||
  ' | Projeto/OP impactado: '||v_req.projeto_op_impactado||
  ' | Regularização no ERP: '||trim(p_referencia),1000));
 return jsonb_build_object('pedido_id',v_pedido,'numero',v_num,'situacao','EFETIVADA','repetido',false);
end;$$;

revoke all on function public.mrp_excecao_solicitar_seguro(uuid,bigint,uuid,text,text,text,numeric,numeric,numeric,text,text,text,text,text)
 from public,anon,authenticated;
revoke all on function public.mrp_excecao_decidir_seguro(uuid,uuid,text,text,text,text,text,bigint,numeric)
 from public,anon,authenticated;
revoke all on function public.mrp_excecao_regularizar_e_criar_seguro(uuid,uuid,text,bigint,numeric)
 from public,anon,authenticated;
grant execute on function public.mrp_excecao_solicitar_seguro(uuid,bigint,uuid,text,text,text,numeric,numeric,numeric,text,text,text,text,text) to service_role;
grant execute on function public.mrp_excecao_decidir_seguro(uuid,uuid,text,text,text,text,text,bigint,numeric) to service_role;
grant execute on function public.mrp_excecao_regularizar_e_criar_seguro(uuid,uuid,text,bigint,numeric) to service_role;
