-- A versão antiga não exige responsável informado; impedir novas gravações
-- por aquela rota. A versão identificada permanece disponível para service_role.
revoke execute on function public.mrp_excecao_solicitar_seguro(
 uuid,bigint,uuid,text,text,text,numeric,numeric,numeric,text,text,text,text,text
) from service_role;
