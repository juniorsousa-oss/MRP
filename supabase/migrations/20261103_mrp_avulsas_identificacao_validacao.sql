-- Correspondente à migração já aplicada na produção em 03/11/2026.
-- Não altera os pedidos históricos existentes.

CREATE OR REPLACE FUNCTION public.mrp_avulsa_campo_identificacao_valido(p_valor text, p_minimo integer DEFAULT 1)
 RETURNS boolean
 LANGUAGE plpgsql
 IMMUTABLE
 SET search_path TO 'public'
AS $function$
DECLARE v text;
BEGIN
  v := lower(btrim(regexp_replace(coalesce(p_valor, ''), '[[:space:]]+', ' ', 'g')));
  IF length(v) < greatest(coalesce(p_minimo, 1), 1) THEN RETURN false; END IF;
  IF v IN ('n/a','na','n.a.','não se aplica','nao se aplica','s/n','sem dados','sem informação',
           'sem informacao','não informado','nao informado','não sei','nao sei',
           'aguardando','pendente','a definir','a preencher','teste','test','xxx','xxxx','xxxxx',
           'preencher depois','preencher na entrega','a preencher na entrega',
           'será informado','sera informado','informar depois') THEN RETURN false; END IF;
  IF v ~ '^(a preencher|preencher na entrega|preencher depois|a definir|aguardando|pendente de|informar depois|ser[aá] informado|n[aã]o informado)([[:space:][:punct:]]|$)'
     OR v ~ '^[-_./[:space:]x]+$' THEN RETURN false; END IF;
  RETURN true;
END;
$function$;

CREATE OR REPLACE FUNCTION public.mrp_avulsa_regularizar_identificacao_seguro(p_pedido_id uuid, p_actor uuid, p_cr text DEFAULT NULL::text, p_aprovador text DEFAULT NULL::text, p_psys text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_pedido public.mrp_avulsas_pedidos%rowtype;
  v_role text;
  v_cr text := btrim(coalesce(p_cr,''));
  v_aprovador text := btrim(coalesce(p_aprovador,''));
  v_psys text := btrim(coalesce(p_psys,''));
  v_rotulo text;
BEGIN
  SELECT role INTO v_role FROM public.user_roles WHERE user_id=p_actor;
  IF coalesce(v_role,'') NOT IN ('ADMIN','CONSULTA') THEN
    RAISE EXCEPTION 'PERFIL_SEM_PERMISSAO_PARA_REGULARIZAR';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext('mrp_avulsas:reservas'));
  SELECT * INTO v_pedido FROM public.mrp_avulsas_pedidos WHERE id=p_pedido_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'PEDIDO_NAO_ENCONTRADO'; END IF;
  IF v_role <> 'ADMIN' AND v_pedido.criado_por IS DISTINCT FROM p_actor THEN
    RAISE EXCEPTION 'ACESSO_NEGADO_SOLICITACAO';
  END IF;
  IF v_pedido.estado NOT IN ('PENDENTE','SEPARADA') THEN
    RAISE EXCEPTION 'SOLICITACAO_NAO_PERMITE_REGULARIZACAO';
  END IF;

  IF v_pedido.finalidade='ACERTO_GERENCIAL' THEN
    IF length(v_cr)>150 OR length(v_aprovador)>180
       OR NOT public.mrp_avulsa_campo_identificacao_valido(v_cr,1)
       OR NOT public.mrp_avulsa_campo_identificacao_valido(v_aprovador,2) THEN
      RAISE EXCEPTION 'INFORME_CR_E_APROVADOR_VALIDOS';
    END IF;
    UPDATE public.mrp_avulsas_pedidos
      SET cr=v_cr, aprovador=v_aprovador WHERE id=p_pedido_id;
    v_rotulo := 'CR e aprovador regularizados';
  ELSIF v_pedido.finalidade='GARANTIA' THEN
    IF length(v_psys)>1000
       OR NOT public.mrp_avulsa_campo_identificacao_valido(v_psys,2) THEN
      RAISE EXCEPTION 'INFORME_OP_GARANTIA_VALIDA';
    END IF;
    UPDATE public.mrp_avulsas_pedidos SET psys=v_psys WHERE id=p_pedido_id;
    v_rotulo := 'OP da garantia regularizada';
  ELSE
    RAISE EXCEPTION 'FINALIDADE_SEM_CAMPOS_PENDENTES';
  END IF;

  INSERT INTO public.mrp_avulsas_eventos
      (pedido_id,evento,autor,observacao)
    VALUES (p_pedido_id,'DADOS_REGULARIZADOS',p_actor,v_rotulo);
  RETURN jsonb_build_object(
    'pedido_id',p_pedido_id,'estado',v_pedido.estado,
    'regularizado',true,'mensagem',v_rotulo
  );
END;
$function$;

CREATE OR REPLACE FUNCTION public.mrp_avulsa_validar_identificacao_operacional()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
DECLARE v_verificar boolean := false;
BEGIN
  IF NEW.estado NOT IN ('PENDENTE','SEPARADA','ENTREGUE') THEN RETURN NEW; END IF;
  IF TG_OP = 'INSERT' THEN
    v_verificar := true;
  ELSE
    v_verificar :=
      NEW.estado IS DISTINCT FROM OLD.estado
      OR NEW.finalidade IS DISTINCT FROM OLD.finalidade
      OR NEW.cr IS DISTINCT FROM OLD.cr
      OR NEW.aprovador IS DISTINCT FROM OLD.aprovador
      OR NEW.psys IS DISTINCT FROM OLD.psys;
  END IF;
  IF NOT v_verificar THEN RETURN NEW; END IF;
  IF NEW.finalidade='ACERTO_GERENCIAL' AND
      (NOT public.mrp_avulsa_campo_identificacao_valido(NEW.cr,1) OR
       NOT public.mrp_avulsa_campo_identificacao_valido(NEW.aprovador,2)) THEN
    RAISE EXCEPTION 'CR_E_APROVADOR_VALIDOS_OBRIGATORIOS';
  ELSIF NEW.finalidade='GARANTIA' AND
      NOT public.mrp_avulsa_campo_identificacao_valido(NEW.psys,2) THEN
    RAISE EXCEPTION 'OP_GARANTIA_VALIDA_OBRIGATORIA';
  END IF;
  RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS mrp_avulsa_validar_identificacao_no_fluxo ON public.mrp_avulsas_pedidos;
CREATE TRIGGER mrp_avulsa_validar_identificacao_no_fluxo
BEFORE INSERT OR UPDATE ON public.mrp_avulsas_pedidos
FOR EACH ROW EXECUTE FUNCTION public.mrp_avulsa_validar_identificacao_operacional();

REVOKE ALL ON FUNCTION public.mrp_avulsa_regularizar_identificacao_seguro(uuid,uuid,text,text,text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.mrp_avulsa_regularizar_identificacao_seguro(uuid,uuid,text,text,text)
  TO service_role;
