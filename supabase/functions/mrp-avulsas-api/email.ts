/** Mensagens do MRP SETTA para envio pelo fluxo corporativo configurado no servidor. */
export type PedidoMail = {
  id: string; numero: number|null; solicitante: string;
  finalidade: string|null; psys: string|null; cr: string|null;
  aprovador: string|null; destino: string|null;
};
export type ItemMail = {
  codigo: string; descricao: string; quantidade: number;
  valor_unitario_ref: number|null;
};
export type TipoEmail = "SEPARADA" | "ENTREGUE";
const gestão = "almoxarifado.energy@gruposetta.com";
const escapar = (v: unknown) => String(v ?? "").replace(/[&<>"']/g,(c)=>({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;",
}[c] ?? c));
const brl = (v: number) => new Intl.NumberFormat("pt-BR",{
  style:"currency",currency:"BRL",minimumFractionDigits:2,maximumFractionDigits:2,
}).format(v);
const numero = (n:number) => new Intl.NumberFormat("pt-BR",{maximumFractionDigits:3}).format(n);
export function montarEmail(pedido: PedidoMail,itens: ItemMail[],tipo:TipoEmail) {
  if(!itens.length)throw Error("PEDIDO_SEM_ITENS");
  const referencia = "SA-"+String(pedido.numero??pedido.id.slice(0,8)).padStart(6,"0");
  const usuario = String(pedido.solicitante||"").trim().toLowerCase();
  if(!/^[a-z0-9][a-z0-9._%+-]*[.][a-z0-9._%+-]+@gruposetta[.]com$/.test(usuario))
    throw Error("SOLICITANTE_SEM_EMAIL_CORPORATIVO_VALIDO");
  const finalidades:Record<string,string>={
    "GARANTIA":"GARANTIA",
    "ACERTO_GERENCIAL":"ACERTO GERENCIAL",
    "TRANSFERENCIA":"TRANSFERÊNCIA DE ARMAZÉM",
  };
  const nomeFinalidade=finalidades[String(pedido.finalidade||"")];
  if(!nomeFinalidade)throw Error("FINALIDADE_NAO_DEFINIDA");
  const to = tipo==="ENTREGUE"?gestão:usuario;
  const cc = tipo==="ENTREGUE"?[usuario]:[];
  const subject=tipo==="ENTREGUE"
    ? "ENTREGA DE PEÇAS AVULSAS - "+nomeFinalidade
    : "MRP SETTA - MATERIAIS SEPARADOS - "+referencia;
  let orientacao="";
  if(tipo==="ENTREGUE"){
    if(pedido.finalidade==="GARANTIA"){
      orientacao = "GARANTIA, FAVOR TRANSFERIR OS MATERIAIS INFORMADOS PARA O ENDEREÇO ASTEC."
        +"\nOPS: "+String(pedido.psys||"");
    }else if(pedido.finalidade==="ACERTO_GERENCIAL"){
      orientacao = "ACERTO, FAVOR REALIZAR O ACERTO GERENCIAL PARA:"
        +"\nCR: "+String(pedido.cr||"")
        +"\nAPROVADOR: "+String(pedido.aprovador||"");
    }else{
      orientacao="TRANSFERÊNCIA DE ARMAZÉM: FAVOR REALIZAR A EMISSÃO DA NF DE TRANSFERÊNCIA DOS ITENS INFORMADOS.";
    }
  }else{
    orientacao="Os materiais da solicitação "+referencia+" foram separados pelo almoxarifado e estão disponíveis para retirada.";
  }
  let total=0;
  const lines:string[]=[];
  const rows=itens.map((item)=>{
    const q=Number(item.quantidade);
    if(!Number.isFinite(q)||q<=0)throw Error("QUANTIDADE_DO_ITEM_INVALIDA");
    const u=item.valor_unitario_ref===null||item.valor_unitario_ref===undefined
      ? null:Number(item.valor_unitario_ref);
    if(tipo==="ENTREGUE" && (u===null||!Number.isFinite(u)||u<0))
      throw Error("VALOR_ULTIMA_COMPRA_AUSENTE_PARA_"+item.codigo);
    const subtotal=u===null?null:Math.round(q*u*100)/100;
    if(subtotal!==null)total+=subtotal;
    lines.push([item.codigo,item.descricao,numero(q),
      u===null?"—":brl(u),subtotal===null?"—":brl(subtotal)].join(" | "));
    return "<tr>"+[item.codigo,item.descricao,numero(q),
      u===null?"—":brl(u),subtotal===null?"—":brl(subtotal)]
      .map(v=>"<td style='border:1px solid #dce6ed;padding:9px'>"+escapar(v)+"</td>").join("")+"</tr>";
  }).join("");
  total=Math.round(total*100)/100;
  const intro=tipo==="ENTREGUE"?"Entrega confirmada.":"Separação confirmada.";
  const complementos=tipo==="ENTREGUE" && pedido.finalidade==="ACERTO_GERENCIAL"
    ? "\nVALOR TOTAL: "+brl(total):"";
  const texto=intro+"\nSolicitação: "+referencia+"\nSolicitante: "+usuario+
    "\nFinalidade: "+nomeFinalidade+"\n\n"+orientacao+complementos+
    "\n\nCÓDIGO | DESCRIÇÃO | QTD | VALOR UNITÁRIO | TOTAL\n"+lines.join("\n")+
    (tipo==="ENTREGUE"?"\nTOTAL DA SOLICITAÇÃO: "+brl(total):"");
  const html="<div style='font-family:Arial,sans-serif;color:#15334a;max-width:900px'>"
    +"<h2 style='color:#173c57'>"+escapar(subject)+"</h2>"
    +"<p><b>Solicitação:</b> "+escapar(referencia)+"<br><b>Solicitante:</b> "+escapar(usuario)
    +"<br><b>Finalidade:</b> "+escapar(nomeFinalidade)+"</p>"
    +"<p style='white-space:pre-line'>"+escapar(orientacao+complementos)+"</p>"
    +"<table style='border-collapse:collapse;width:100%;font-size:13px'>"
    +"<thead><tr>"+["Código","Descrição","Quantidade","Valor unitário","Valor total"]
       .map(v=>"<th style='text-align:left;padding:10px;background:#173c57;color:white'>"+v+"</th>").join("")
    +"</tr></thead><tbody>"+rows+"</tbody></table>"
    +(tipo==="ENTREGUE"?"<p style='text-align:right;font-weight:bold;font-size:17px'>TOTAL: "+escapar(brl(total))+"</p>":"")
    +"<p style='color:#637888;font-size:11px'>MRP SETTA · Registro de controle interno. "
    +"O atendimento não realiza baixa de estoque no Protheus.</p></div>";
  return {to,cc,subject,html,texto,total,referencia};
}

/** Requer MRP_EMAIL_WORKFLOW_URL configurado nas secrets do Supabase. */
export async function notificarEmail(admin:any,pedidoId:string,tipo:TipoEmail):Promise<string>{
  const {data:event,error:evtErr}=await admin.from("mrp_avulsas_email_eventos")
    .select("id,status,tentativas,ultima_tentativa")
    .eq("pedido_id",pedidoId).eq("tipo",tipo).maybeSingle();
  if(evtErr||!event)throw Error("EVENTO_DE_EMAIL_NAO_ENCONTRADO");
  if(event.status==="ACEITO")return "ACEITO";
  if(event.status==="ENVIANDO" && event.ultima_tentativa &&
     Date.now()-new Date(event.ultima_tentativa).getTime()<180000)return "ENVIANDO";

  const url=String(Deno.env.get("MRP_EMAIL_WORKFLOW_URL")||"").trim();
  if(!url){
    await admin.from("mrp_avulsas_email_eventos").update({
      status:"NAO_CONFIGURADO",erro:"MRP_EMAIL_WORKFLOW_URL nao configurada",
    }).eq("id",event.id).neq("status","ACEITO");
    return "NAO_CONFIGURADO";
  }
  if(!url.startsWith("https://"))throw Error("EMAIL_WEBHOOK_URL_HTTPS_OBRIGATORIO");
  const {data:pedido,error:pedidoError}=await admin.from("mrp_avulsas_pedidos")
    .select("id,numero,solicitante,finalidade,psys,cr,aprovador,destino,estado")
    .eq("id",pedidoId).maybeSingle();
  if(pedidoError||!pedido)throw Error("PEDIDO_NAO_ENCONTRADO");
  if((tipo==="SEPARADA"&&!["SEPARADA","ENTREGUE"].includes(String(pedido.estado))) ||
     (tipo==="ENTREGUE"&&pedido.estado!=="ENTREGUE"))
    throw Error("PEDIDO_NAO_ESTA_NO_STATUS_DA_NOTIFICACAO");
  const {data:itens,error:itemsError}=await admin.from("mrp_solicitacoes_avulsas")
    .select("codigo,descricao,quantidade,valor_unitario_ref").eq("pedido_id",pedidoId)
    .order("id",{ascending:true});
  if(itemsError||!itens)throw Error("ITENS_DO_PEDIDO_INDISPONIVEIS");
  const mensagem=montarEmail(pedido,itens,tipo);
  const tentativas=Number(event.tentativas||0);
  const {data:claimed,error:claimError}=await admin.from("mrp_avulsas_email_eventos")
    .update({
      status:"ENVIANDO",tentativas:tentativas+1,ultima_tentativa:new Date().toISOString(),erro:null,
    }).eq("id",event.id).eq("status",event.status).eq("tentativas",tentativas)
    .select("id").maybeSingle();
  if(claimError)throw Error("EMAIL_NAO_AGENDADO");
  if(!claimed)return "ENVIANDO";
  let status="ACEITO",erro:string|null=null;
  try{
    const response=await fetch(url,{
      method:"POST",headers:{"content-type":"application/json"},
      body:JSON.stringify({
        notificacao_id:event.id,pedido_id:pedidoId,tipo,
        para:mensagem.to,copia:mensagem.cc,assunto:mensagem.subject,
        html:mensagem.html,texto:mensagem.texto,
      }),
      signal:AbortSignal.timeout(15000),
    });
    if(!response.ok){status="FALHA";erro="EMAIL_WORKFLOW_HTTP_"+response.status;}
  }catch{status="FALHA";erro="EMAIL_WORKFLOW_INDISPONIVEL";}
  await admin.from("mrp_avulsas_email_eventos").update({
    status,erro,aceito_em:status==="ACEITO"?new Date().toISOString():null,
  }).eq("id",event.id).eq("status","ENVIANDO");
  return status;
}
