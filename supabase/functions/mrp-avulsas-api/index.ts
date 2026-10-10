import { createClient } from "jsr:@supabase/supabase-js@2";
import { selectMaterial, availableAfterReservations, displayStatus, type MrpMaterial } from "./catalog.ts";
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
    if (roleError || !["ADMIN", "CONSULTA"].includes(String(permission?.role || "").toUpperCase())) {
      return fail("MRP_ACCESS_DENIED", 403);
    }
    const role = String(permission?.role || "").toUpperCase();
    const body = await req.json();
    const action = String(body?.action || "").trim();
    const input = body?.payload || {};
    if (action === "attend") {
      if (role !== "ADMIN") return fail("ADMIN_REQUIRED", 403);
      const id = Number(input.id);
      if (!Number.isSafeInteger(id) || id <= 0) return fail("ID_INVALIDO");
      const { data, error } = await admin.rpc("mrp_avulsa_atender_seguro", {
        p_id: id, p_actor: userId, p_observacao: String(input.observacao || ""),
      });
      if (error) return fail(error.message);
      return json({ ok: true, data });
    }
    if (!["list", "create"].includes(action)) return fail("ACAO_INVALIDA");
    const { data: latest, error: latestError } = await admin.from("mrp_snapshots")
      .select("id,created_at,mrp_geral,compressed_payload")
      .order("created_at", { ascending: false }).order("id", { ascending: false })
      .limit(1).maybeSingle();
    if (latestError) return fail(latestError.message, 500);
    if (!latest) return fail("MRP_AINDA_NAO_SALVO", 409);
    const available = await unpackMrp(latest);
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
      .select("id,snapshot_id,codigo,descricao,quantidade,div_referencia,solicitante,criado_por,criado_em,status,atendido_em,observacao_atendimento");
    if(role!=="ADMIN")query=query.eq("criado_por",userId);
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
    }));
    return json({ ok: true, data: {
      snapshot_id: latest.id, materials, rows: visibleRows, role, user_id:userId,
    }});
  } catch (e) {
    return fail(String(e instanceof Error ? e.message : e), 500);
  }
});
