import {montarEmail,type PedidoMail,type ItemMail} from "./email.ts";
const pedido:PedidoMail={
  id:"f3333333-3333-4333-8333-333333333333",
  numero:1002,solicitante:"nome.sobrenome@gruposetta.com",
  finalidade:"GARANTIA",psys:"26012301001, 26012301002",
  cr:null,aprovador:null,destino:"ASTEC",
};
const itens:ItemMail[]=[
  {codigo:"00000001",descricao:"RELE <TESTE>",quantidade:2,valor_unitario_ref:15.50},
  {codigo:"00000002",descricao:"CABO",quantidade:3,valor_unitario_ref:1.75},
];
function valid(check:boolean,m:string){if(!check)throw Error(m);}
Deno.test("separação vai apenas para solicitante",()=>{
  const mail=montarEmail(pedido,itens,"SEPARADA");
  valid(mail.to===pedido.solicitante,"destinatario");
  valid(mail.cc.length===0,"nao copiar gestao ou jessica na separacao");
  valid(!mail.cc.includes("jessica.samara@gruposetta.com"),"jessica fora da separacao");
  valid(mail.subject.includes("SA-001002"),"protocolo");
  valid(mail.texto.includes("disponíveis para retirada"),"orientacao");
});
Deno.test("garantia entrega para gestao, cc solicitante, tabela e total",()=>{
  const mail=montarEmail(pedido,itens,"ENTREGUE");
  valid(mail.to==="almoxarifado.energy@gruposetta.com","gestao");
  valid(mail.cc.length===2&&mail.cc.includes(pedido.solicitante),"copia solicitante");
  valid(mail.cc.includes("jessica.samara@gruposetta.com"),"jessica apenas na entrega");
  valid(mail.subject==="ENTREGA DE PEÇAS AVULSAS - GARANTIA","titulo");
  valid(mail.texto.includes("OP(s): 26012301001"),"OP(s) de origem");
  valid(mail.total===36.25,"total (2*15,50 + 3*1,75)");
  valid(mail.html.includes("R$"),"moeda");
  valid(mail.html.includes("RELE &lt;TESTE&gt;"),"escape html");
  valid(!mail.html.includes("RELE <TESTE>"),"injection prevention");
});
Deno.test("entrega nao duplica destinatario quando solicitante e jessica",()=>{
  const mail=montarEmail({...pedido,solicitante:"jessica.samara@gruposetta.com"},itens,"ENTREGUE");
  valid(mail.cc.length===1&&mail.cc[0]==="jessica.samara@gruposetta.com","sem duplicacao");
});
Deno.test("acerto gerencial inclui CR e aprovador",()=>{
  const mail=montarEmail({
    ...pedido,finalidade:"ACERTO_GERENCIAL",
    psys:null,cr:"600307",aprovador:"Compras SETTA",
  },itens,"ENTREGUE");
  valid(mail.subject.endsWith("ACERTO GERENCIAL"),"assunto");
  valid(mail.texto.includes("CR: 600307"),"CR");
  valid(mail.texto.includes("APROVADOR: Compras SETTA"),"aprovador");
  valid(mail.texto.includes("VALOR TOTAL:"),"total");
});
Deno.test("transferencia ASTEC solicita NF",()=>{
  const mail=montarEmail({...pedido,finalidade:"TRANSFERENCIA",psys:null},
    itens,"ENTREGUE");
  valid(mail.subject.endsWith("TRANSFERÊNCIA DE ARMAZÉM"),"assunto");
  valid(mail.texto.includes("EMISSÃO DA NF"),"orientacao NF");
});
Deno.test("email de entrega aceita valor nulo como zero",()=>{
  const mail=montarEmail(pedido,[{...itens[0],valor_unitario_ref:null}],"ENTREGUE");
  valid(mail.total===0,"total zero");
  valid(mail.texto.includes("0,00"),"moeda BR");
});
Deno.test("nao aceitar destinatario externo",()=>{
  let falhou=false;
  try{montarEmail({...pedido,solicitante:"fora@gmail.com"},itens,"ENTREGUE");}
  catch{falhou=true;}
  valid(falhou,"nao enviar fora do dominio corporativo");
});
