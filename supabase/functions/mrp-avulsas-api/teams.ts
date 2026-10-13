/** Notificação em Teams Workflows via webhook protegido por segredo do servidor. */
export type TeamsItem = { codigo: string; descricao: string; quantidade: number };

export function teamsCard(id: string, solicitante: string, itens: TeamsItem[]) {
  const facts = itens.map((item, i) => ({
    title: String(i + 1).padStart(2, "0") + " · " + item.codigo,
    value: item.descricao.slice(0, 125).replace(/[\r\n]/g, " ") +
      " — Qtd.: " + Number(item.quantidade).toLocaleString("pt-BR", {maximumFractionDigits: 3}),
  }));
  return {
    type: "message",
    attachments: [{
      contentType: "application/vnd.microsoft.card.adaptive",
      content: {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        type: "AdaptiveCard", version: "1.4",
        body: [
          {type: "TextBlock", text: "MRP SETTA · NOVA SOLICITAÇÃO AVULSA",
            weight: "Bolder", size: "Medium", wrap: true},
          {type: "FactSet", facts: [
            {title: "Solicitante", value: solicitante.slice(0,180)},
            {title: "Materiais", value: String(itens.length)},
            {title: "Pedido", value: id.slice(0,8)},
          ]},
          {type: "TextBlock", text: "Materiais solicitados", weight: "Bolder"},
          {type: "FactSet", facts},
          {type: "TextBlock", text: "Aguardando análise e separação no MRP SETTA.",
            wrap: true, isSubtle: true, spacing: "Medium"},
        ],
      },
    }],
  };
}

export async function notifyTeams(
  endpoint: string, id: string, solicitante: string, itens: TeamsItem[],
): Promise<{ok: boolean; error?: string}> {
  return sendCard(endpoint, teamsCard(id, solicitante, itens));
}

/** Mensagem explicitamente de TESTE: não representa uma solicitação de material. */
export function teamsTestCard(actor: string) {
  return {
    type: "message",
    attachments: [{
      contentType: "application/vnd.microsoft.card.adaptive",
      content: {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        type: "AdaptiveCard",
        version: "1.4",
        body: [
          { type: "TextBlock", text: "TESTE DE CONEXÃO · MRP SETTA",
            weight: "Bolder", size: "Medium", wrap: true },
          { type: "TextBlock",
            text: "A integração entre o MRP SETTA e este grupo do Teams está sendo verificada.",
            wrap: true },
          { type: "FactSet", facts: [
            { title: "Iniciado por", value: actor.slice(0, 120) },
            { title: "Origem", value: "MRP SETTA — Solicitações Avulsas" },
          ] },
          { type: "TextBlock",
            text: "Mensagem de teste. Nenhuma solicitação ou reserva de material foi criada.",
            wrap: true, isSubtle: true },
        ],
      },
    }],
  };
}

export async function notifyTeamsTest(
  endpoint: string, actor: string,
): Promise<{ok: boolean; error?: string}> {
  return sendCard(endpoint, teamsTestCard(actor));
}

async function sendCard(
  endpoint: string, card: unknown,
): Promise<{ok: boolean; error?: string}> {
  let parsed: URL;
  try { parsed = new URL(endpoint); }
  catch { return {ok:false,error:"ENDERECO_TEAMS_INVALIDO"}; }
  const host = parsed.hostname.toLowerCase();
  const allowed = ["logic.azure.com", "powerautomate.com", "powerplatform.com", "webhook.office.com"];
  if (parsed.protocol !== "https:" ||
      !allowed.some(domain => host === domain || host.endsWith("." + domain))) {
    return {ok:false,error:"DOMINIO_TEAMS_NAO_AUTORIZADO"};
  }
  const body = JSON.stringify(card);
  if (new TextEncoder().encode(body).length > 27000) {
    return {ok:false,error:"NOTIFICACAO_TEAMS_ACIMA_DO_LIMITE"};
  }
  try {
    const response = await fetch(parsed.toString(), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body,
      signal: AbortSignal.timeout(12000),
    });
    if (!response.ok) return {ok:false,error:"TEAMS_HTTP_" + response.status};
    return {ok:true};
  } catch {
    return {ok:false,error:"TEAMS_CONEXAO_OU_TIMEOUT"};
  }
}
