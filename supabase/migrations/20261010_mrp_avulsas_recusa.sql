-- Inclusão de RECUSADA sem alterar solicitações anteriores.
-- Recusa libera imediatamente a reserva lógica da requisição ABERTA.
alter table public.mrp_solicitacoes_avulsas
  drop constraint if exists mrp_solicitacoes_avulsas_status_check;

alter table public.mrp_solicitacoes_avulsas
  add constraint mrp_solicitacoes_avulsas_status_check
  check (status in ('ABERTA','ATENDIDA','RECUSADA'));

alter table public.mrp_solicitacoes_avulsas
  add column if not exists recusado_por uuid,
  add column if not exists recusado_em timestamptz;

create or replace function public.mrp_avulsa_recusar_seguro(
  p_id bigint, p_actor uuid, p_motivo text
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
  v_status text;
  v_motivo text := trim(coalesce(p_motivo, ''));
begin
  if p_actor is null then
    raise exception 'IDENTIFICACAO_OBRIGATORIA';
  end if;
  if length(v_motivo) < 5 or length(v_motivo) > 1000 then
    raise exception 'MOTIVO_RECUSA_OBRIGATORIO_5_A_1000_CARACTERES';
  end if;
  -- Usa a mesma trava da criação para impedir corrida com reservas.
  perform pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
  update public.mrp_solicitacoes_avulsas
     set status = 'RECUSADA',
         recusado_por = p_actor,
         recusado_em = now(),
         observacao_atendimento = v_motivo
   where id = p_id
     and status = 'ABERTA'
   returning status into v_status;
  if v_status is null then
    raise exception 'SOLICITACAO_INEXISTENTE_OU_JA_TRATADA';
  end if;
  return jsonb_build_object('id', p_id, 'status', v_status,
                            'status_exibicao', 'RECUSADA');
end;
$$;

revoke all on function public.mrp_avulsa_recusar_seguro(bigint,uuid,text)
  from public, anon, authenticated;
grant execute on function public.mrp_avulsa_recusar_seguro(bigint,uuid,text)
  to service_role;
