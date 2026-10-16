import { createClient } from "jsr:@supabase/supabase-js@2";
import { selectMaterial, availableAfterReservations, displayStatus, type MrpMaterial } from "./catalog.ts";
import { notifyTeams, notifyTeamsTest, type TeamsItem } from "./teams.ts";
import { notificarEmail } from "./email.ts";
import { carregarCustos, type CustoCadastro } from "./custos.ts";
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { ...cors, "Content-Type": "application/json" } });
const fail = (message: string, status = 400) => json({ ok: false, error: message }, status);

async function unpackMrp(snapshot: Record<string, unknown>): Promise<Map<string, MrpMaterial>> {
  let rows: any[] = Array.isArray(snapshot.mrp_geral) ? snapshot.mrp_geral as any[] : [];
  if (typeof snapshot.compressed_payload === "string" && snapshot.compressed_payload) {
    const encoded = snapshot.compressed_payload;
    const binary = atob(encoded);
    const compressed = Uint8Array.from(binary, c => c.charCodeAt(0));
    const inflated = new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream("gzip")));
    const payload = JSON.parse(await inflated.text());
    if (!Array.isArray(payload?.mrp_geral)) throw Error("MRP_COMPACTADO_INVALIDO");
    rows = payload.mrp_geral;
  }
  const result = new Map<string, MrpMaterial>();
  for (const row of rows) {
    const material=selectMaterial(row);
    if (!material) continue;
    if (result.has(material.codigo)) throw Error("MRP_CODIGO_DUPLICADO:" + material.codigo);
    result.set(material.codigo,material);
  }
  return result;
}


type PendingBatchItem = TeamsItem & { limite: number; valor_unitario: number | null };
async function sendBatchTeams(
  admin: any, pedidoId: string, actingUserId: string, actingRole: string,
): Promise<string> {
  const { data: pedido, error: pedidoError } = await admin.from("mrp_avulsas_pedidos")
    .select("id,solicitante,criado_por,teams_status,teams_tentativas")
    .eq("id", pedidoId).maybeSingle();
  if (pedidoError || !pedido) throw Error("PEDIDO_NAO_ENCONTRADO");
  if (pedido.criado_por !== actingUserId && actingRole !== "ADMIN") {
    throw Error("PEDIDO_ACESSO_NEGADO");
  }
  const status = String(pedido.teams_status || "PENDENTE");
  if (status === "ENVIADO" || status === "ENVIANDO") return status;

  const url = String(Deno.env.get("MRP_TEAMS_WORKFLOW_URL") || "").trim();
  if (!url) {
    await admin.from("mrp_avulsas_pedidos").update({
      teams_status: "NAO_CONFIGURADO", teams_erro: "Integração Teams aguardando configuração."
    }).eq("id", pedidoId).neq("teams_status", "ENVIADO");
    return "NAO_CONFIGURADO";
  }
  const attempts = Number(pedido.teams_tentativas || 0);
  const { data: claimed, error: claimError } = await admin.from("mrp_avulsas_pedidos")
    .update({ teams_status: "ENVIANDO", teams_tentativas: attempts + 1, teams_erro: null })
    .eq("id", pedidoId).eq("teams_status", status)
    .eq("teams_tentativas", attempts).select("id").maybeSingle();
  if (claimError) throw Error("NAO_FOI_POSSIVEL_AGENDAR_NOTIFICACAO");
  if (!claimed) return "ENVIANDO";

  const { data: children, error: childrenError } = await admin
    .from("mrp_solicitacoes_avulsas").select("codigo,descricao,quantidade")
    .eq("pedido_id", pedidoId).order("id", { ascending: true });
  let outcome: { ok: boolean; error?: string };
  if (childrenError || !children?.length) {
    outcome = {ok: false, error: "ITENS_DO_PEDIDO_INDISPONIVEIS"};
  } else {
    outcome = await notifyTeams(url, pedidoId, String(pedido.solicitante),
      children.map((r: any) => ({
        codigo: String(r.codigo), descricao: String(r.descricao),
        quantidade: Number(r.quantidade),
      })));
  }
  const update = outcome.ok
    ? { teams_status: "ENVIADO", teams_enviado_em: new Date().toISOString(), teams_erro: null }
    : { teams_status: "FALHA", teams_erro: String(outcome.error || "FALHA_NO_TEAMS").slice(0, 350) };
  const { error: updateError } = await admin.from("mrp_avulsas_pedidos")
    .update(update).eq("id", pedidoId).eq("teams_status", "ENVIANDO");
  if (updateError) return "FALHA";
  return outcome.ok ? "ENVIADO" : "FALHA";
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });
  if (req.method !== "POST") return fail("METHOD_NOT_ALLOWED", 405);
  try {
    const url = Deno.env.get("SUPABASE_URL");
    const secret = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!url || !secret) return fail("SERVIDOR_NAO_CONFIGURADO", 500);
    const token = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "").trim();
    if (!token) return fail("AUTH_REQUIRED", 401);
    const admin = createClient(url, secret, { auth: { persistSession: false, autoRefreshToken: false } });
    const { data: identity, error: identityError } = await admin.auth.getUser(token);
    if (identityError || !identity?.user?.id) return fail("SESSION_INVALID_OR_EXPIRED", 401);
    const userId = identity.user.id;
    const { data: permission, error: roleError } = await admin.from("user_roles")
      .select("role,nome").eq("user_id", userId).maybeSingle();
    if (roleError || !["ADMIN", "CONSULTA", "OPERADOR"].includes(String(permission?.role || "").toUpperCase())) {
      return fail("MRP_ACCESS_DENIED", 403);
    }
    const role = String(permission?.role || "").toUpperCase();
    const body = await req.json();
    const action = String(body?.action || "").trim();
    const input = body?.payload || {};
    if (action === "test_teams") {
      // Ação explícita do administrador, sem reserva ou gravação de materiais.
      if (role !== "ADMIN") return fail("ADMIN_REQUIRED", 403);
      const destination = String(Deno.env.get("MRP_TEAMS_WORKFLOW_URL") || "").trim();
      if (!destination) {
        return json({ ok: true, data: {
          status: "NAO_CONFIGURADO",
          message: "Webhook do Teams não encontrado nas variáveis da função.",
        } });
      }
      const { data: last, error: lastError } = await admin.from("mrp_teams_testes")
        .select("criado_em").eq("user_id", userId)
        .order("criado_em", { ascending: false }).limit(1).maybeSingle();
      if (lastError) return fail("NAO_FOI_POSSIVEL_VALIDAR_LIMITE_DE_TESTE", 500);
      if (last?.criado_em &&
          Date.now() - new Date(last.criado_em).getTime() < 60000) {
        return fail("AGUARDE_60_SEGUNDOS_PARA_REPETIR_O_TESTE", 429);
      }
      const { data: attempt, error: insertError } = await admin
        .from("mrp_teams_testes").insert({ user_id: userId, status: "EM_ANDAMENTO" })
        .select("id").single();
      if (insertError || !attempt) return fail("REGISTRO_TESTE_INDISPONIVEL", 500);
      const actor = String(permission?.nome || "Administrador SETTA");
      const response = await notifyTeamsTest(destination, actor);
      const result = response.ok ? "ACEITO" : "FALHA";
      await admin.from("mrp_teams_testes").update({
        status: result, erro: response.ok ? null : (response.error || "ERRO_NAO_IDENTIFICADO"),
      }).eq("id", attempt.id);
      return json({ ok: true, data: {
        status: result,
        // Não expor URL, query ou token do webhook na resposta.
        error: response.ok ? null : (response.error || "ERRO_NAO_IDENTIFICADO"),
        message: response.ok
          ? "Webhook aceitou o teste. Confirme a chegada no chat do Teams."
          : "Falha no envio de teste. Consulte o código do erro.",
      } });
    }
    if (action === "notify_batch") {
      const id = String(input.pedido_id || "");
      if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(id)) return fail("PEDIDO_INVALIDO");
      const status = await sendBatchTeams(admin, id, userId, role);
      return json({ ok: true, data: { pedido_id: id, teams_status: status } });
    }
    if (action === "batch_status") {
      const id = String(input.pedido_id || "");
      if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(id)) return fail("PEDIDO_INVALIDO");
      const {data: pedido, error} = await admin.from("mrp_avulsas_pedidos")
        .select("id,criado_por,teams_status").eq("id",id).maybeSingle();
      if (error || !pedido || (pedido.criado_por!==userId && role!=="ADMIN"))
        return fail("PEDIDO_NAO_ENCONTRADO",404);
      return json({ok:true,data:{pedido_id:id,teams_status:pedido.teams_status}});
    }
    if (action === "pedido_tratar") {
      if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED",403);
      const pedidoId=String(input.pedido_id||"").trim();
      const acao=String(input.acao||"").toUpperCase();
      const observacao=String(input.observacao||"").trim();
      if(!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(pedidoId))
        return fail("PEDIDO_INVALIDO");
      if(!["SEPARAR","RECUSAR","ENTREGAR"].includes(acao))
        return fail("ACAO_INVALIDA");
      const {data,error}=await admin.rpc("mrp_avulsa_pedido_tratar_seguro",{
        p_pedido_id:pedidoId,p_actor:userId,p_acao:acao,p_obs:observacao,
      });
      if(error)return fail(error.message,409);
      let emailStatus:string|null=null;
      if(acao==="SEPARAR"||acao==="ENTREGAR"){
        try{emailStatus=await notificarEmail(admin,pedidoId,
          acao==="SEPARAR"?"SEPARADA":"ENTREGUE");}
        catch {emailStatus="FALHA";}
      }
      return json({ok:true,data:{...data,email_status:emailStatus}});
    }
    if (action === "garantia_resultado") {
      if(role!=="CONSULTA")return fail("CONSULTA_REQUIRED",403);
      const itemId=Number(input.id);
      const resultado=String(input.resultado||"");
      if(!Number.isSafeInteger(itemId)||itemId<1 || !["UTILIZADO","DEVOLVIDO"].includes(resultado))
        return fail("DADOS_DA_GARANTIA_INVALIDOS");
      const {data,error}=await admin.rpc("mrp_avulsa_garantia_resultado_seguro",{
        p_item:itemId,p_actor:userId,p_resultado:resultado,
      });
      if(error)return fail(error.message,409);
      return json({ok:true,data});
    }
    if(action==="email_retry"){
      if(role!=="OPERADOR"&&role!=="ADMIN")return fail("OPERADOR_OU_ADMIN_REQUIRED",403);
      const id=String(input.pedido_id||"");
      const tipo=String(input.tipo||"");
      if(!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(id)||
         !["SEPARADA","ENTREGUE"].includes(tipo))return fail("DADOS_NOTIFICACAO_INVALIDOS");
      const status=await notificarEmail(admin,id,tipo as "SEPARADA"|"ENTREGUE");
      return json({ok:true,data:{pedido_id:id,tipo,email_status:status}});
    }
    if (action === "reject") {
      if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED", 403);
      const id = Number(input.id);
      if (!Number.isSafeInteger(id) || id <= 0) return fail("ID_INVALIDO");
      const motivo = String(input.motivo || "").trim();
      if (motivo.length < 5 || motivo.length > 1000)
        return fail("MOTIVO_RECUSA_OBRIGATORIO_5_A_1000_CARACTERES");
      const { data, error } = await admin.rpc("mrp_avulsa_recusar_seguro", {
        p_id: id, p_actor: userId, p_motivo: motivo,
      });
      if (error) return fail(error.message);
      return json({ ok: true, data });
    }
    if (action === "attend") {
      if (role !== "OPERADOR") return fail("OPERADOR_REQUIRED", 403);
      const id = Number(input.id);
      if (!Number.isSafeInteger(id) || id <= 0) return fail("ID_INVALIDO");
      const { data, error } = await admin.rpc("mrp_avulsa_atender_seguro", {
        p_id: id, p_actor: userId, p_observacao: String(input.observacao || ""),
      });
      if (error) return fail(error.message);
      return json({ ok: true, data });
    }
    if (!["list", "create", "create_batch"].includes(action)) return fail("ACAO_INVALIDA");
    // A autorizacao e validada no servidor; ocultar controles nao basta.
    if (action !== "list" && role !== "CONSULTA") return fail("CONSULTA_REQUIRED", 403);
    const { data: latest, error: latestError } = await admin.from("mrp_snapshots")
      .select("id,created_at,mrp_geral,compressed_payload")
      .order("created_at", { ascending: false }).order("id", { ascending: false })
      .limit(1).maybeSingle();
    if (latestError) return fail(latestError.message, 500);
    if (!latest) return fail("MRP_AINDA_NAO_SALVO", 409);
    const available = await unpackMrp(latest);
    // O CADASTROS e a referencia de custo; nunca substituir o saldo do MRP.
    let custos:CustoCadastro={valorPorCodigo:new Map(),coluna:null,referencia:"",
      status:"FONTE_INDISPONIVEL"};
    try{custos=await carregarCustos(admin);}catch{
      // Sem custo, preserva-se a solicitacao. O valor nulo bloqueia a entrega.
    }
    for(const material of available.values()){
      material.valor_unitario=custos.valorPorCodigo.get(material.codigo) ?? 0;
    }
    if (action === "create_batch") {
      const requested = input.itens;
      const solicitante = String(input.solicitante || "").trim().toLowerCase();
      const finalidade = String(input.finalidade || "");
      const psys = String(input.psys || "").trim();
      const cr = String(input.cr || "").trim();
      const aprovador = String(input.aprovador || "").trim();
      const pedidoId = String(input.pedido_id || "").trim();
      if (!Array.isArray(requested) || requested.length < 1 || requested.length > 30)
        return fail("PEDIDO_DEVE_CONTER_1_A_30_MATERIAIS");
      if (!solicitante || solicitante.length > 180) return fail("SOLICITANTE_OBRIGATORIO");
      if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(pedidoId))
        return fail("IDENTIFICADOR_DE_PEDIDO_INVALIDO");
      const selected: PendingBatchItem[] = [];
      const codes = new Set<string>();
      for (const row of requested) {
        const raw = String(row?.codigo ?? "").trim().replace(/\.0$/, "");
        if (!/^\d+$/.test(raw)) return fail("CODIGO_INVALIDO");
        const code = raw.padStart(8, "0");
        if (codes.has(code)) return fail("MATERIAL_DUPLICADO_NO_PEDIDO");
        codes.add(code);
        const material = available.get(code);
        if (!material) return fail("MATERIAL_SEM_SALDO_OU_SOBRA:" + code);
        const quantity = Number(row?.quantidade);
        if (!Number.isFinite(quantity) || quantity <= 0
          || Math.abs(Math.round(quantity * 1000) / 1000 - quantity) > 1e-8)
          return fail("QUANTIDADE_INVALIDA:" + code);
        if (quantity > material.limite + 1e-9)
          return fail("QUANTIDADE_SUPERIOR_AO_LIMITE:" + code);
        selected.push({
          codigo: code, descricao: material.descricao,
          quantidade: quantity, limite: material.limite,
          valor_unitario: material.valor_unitario,
        });
      }
      const { data, error } = await admin.rpc("mrp_avulsa_criar_lote_v2_seguro", {
        p_snapshot_id: latest.id, p_pedido_id: pedidoId,
        p_itens: selected, p_email: solicitante, p_criado_por: userId,
        p_finalidade: finalidade, p_psys: psys, p_cr: cr, p_aprovador: aprovador,
      });
      if (error) return fail(error.message, 409);
      // O pedido já está gravado de forma atômica. Uma falha de Teams não
      // reverte os itens nem repete o lançamento.
      let teamsStatus = String(data?.teams_status || "PENDENTE");
      if (teamsStatus !== "ENVIADO") {
        try { teamsStatus = await sendBatchTeams(admin, pedidoId, userId, role); }
        catch { teamsStatus = "FALHA"; }
      }
      return json({ok:true,data:{...data,teams_status:teamsStatus}});
    }
    if (action === "create") {
      const codeRaw = String(input.codigo || "").trim().replace(/\.0$/, "");
      if (!/^\d+$/.test(codeRaw)) return fail("CODIGO_INVALIDO");
      const code = codeRaw.padStart(8, "0");
      const item = available.get(code);
      if (!item) return fail("MATERIAL_SEM_SALDO_OU_SOBRA_POSITIVA");
      const quantidade = Number(input.quantidade);
      if (!Number.isFinite(quantidade) || quantidade <= 0 || Math.round(quantidade * 1000) / 1000 !== quantidade) {
        return fail("QUANTIDADE_INVALIDA (ATE_3_CASAS_DECIMAIS)");
      }
      const solicitante = String(input.solicitante || "").trim();
      if (!solicitante || solicitante.length > 180) return fail("SOLICITANTE_OBRIGATORIO");
      const { data, error } = await admin.rpc("mrp_avulsa_criar_seguro", {
        p_snapshot_id: latest.id, p_codigo: code, p_descricao: item.descricao,
        // A capacidade física permitida é a menor entre estoque e DIV.
        p_div: item.limite, p_quantidade: quantidade,
        p_solicitante: solicitante, p_criado_por: userId,
      });
      if (error) return fail(error.message);
      return json({ ok: true, data });
    }
    // A reserva considera TODOS os pedidos, inclusive os de outros usuários,
    // independentemente das permissões de visualização do solicitante.
    const { data: ledger, error: ledgerError } = await admin.from("mrp_solicitacoes_avulsas")
      .select("snapshot_id,codigo,quantidade,status")
      .in("status",["ABERTA","ATENDIDA"])
      .limit(10000);
    if (ledgerError) return fail(ledgerError.message, 500);

    let query = admin.from("mrp_solicitacoes_avulsas")
      .select("id,pedido_id,snapshot_id,codigo,descricao,quantidade,div_referencia,solicitante,criado_por,criado_em,status,atendido_em,observacao_atendimento,recusado_em,valor_unitario_ref,destino_garantia,destino_garantia_em");
    if(role==="CONSULTA")query=query.eq("criado_por",userId);
    const { data: rows, error: listError } = await query
      .order("criado_em", { ascending: false }).limit(2000);
    if (listError) return fail(listError.message, 500);
    const reserved = new Map<string, number>();
    for (const r of ledger || []) {
      // Baixa lógica apenas quando uma nova fotografia MRP substituir a anterior.
      const consumesDiv = r.status === "ABERTA" ||
        (r.status === "ATENDIDA" && Number(r.snapshot_id) === Number(latest.id));
      if (consumesDiv) {
        reserved.set(String(r.codigo), (reserved.get(String(r.codigo)) || 0) + Number(r.quantidade || 0));
      }
    }
    const materials = [...available.values()].sort((a,b) => a.codigo.localeCompare(b.codigo))
      .map(item => ({
        ...item,
        disponivel: availableAfterReservations(item.limite, reserved.get(item.codigo) || 0),
      }))
      .filter(x => x.disponivel > 0 && x.saldo > 0 && x.div > 0);
    const visibleRows = (rows || []).map((r:any) => ({
      ...r, status_exibicao: displayStatus(r.status),
      valor_ultima_compra_atual: custos.valorPorCodigo.get(String(r.codigo)) ?? 0,
    }));
    // Cabeçalho de pedidos: número único, finalidade, separação e entrega.
    let pedidosQuery=admin.from("mrp_avulsas_pedidos").select(
      "id,numero,solicitante,criado_por,criado_em,finalidade,psys,cr,aprovador,destino,estado,separado_em,entregue_em,observacao_operador,teams_status"
    );
    if(role==="CONSULTA")pedidosQuery=pedidosQuery.eq("criado_por",userId);
    const {data:pedidos,error:pedidosError}=await pedidosQuery
      .order("criado_em",{ascending:false}).limit(2000);
    if(pedidosError)return fail(pedidosError.message,500);
    const ids=(pedidos||[]).map((p:any)=>p.id);
    const avisos:any[]=[];
    if(ids.length){
      const {data,eventos,error:emailError}=await (async ()=>{
        const q=await admin.from("mrp_avulsas_email_eventos")
          .select("pedido_id,tipo,status").in("pedido_id",ids);
        return {data:q.data,eventos:q.data,error:q.error};
      })();
      if(emailError)return fail("NOTIFICACOES_INDISPONIVEIS",500);
      avisos.push(...(eventos||[]));
    }
    return json({ ok: true, data: {
      pedidos:pedidos||[], email_eventos:avisos,
      custo_referencia:{status:custos.status,coluna:custos.coluna,
        versao:custos.referencia,codigos_com_valor:custos.valorPorCodigo.size},
      snapshot_id: latest.id, materials: role === "CONSULTA" ? materials : [],
      rows: visibleRows, role, user_id:userId,
    }});
  } catch (e) {
    return fail(String(e instanceof Error ? e.message : e), 500);
  }
});
