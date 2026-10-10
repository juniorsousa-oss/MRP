import {selectMaterial,availableAfterReservations,displayStatus,numeric} from "./catalog.ts";

function equal(actual:unknown,expected:unknown,message:string){
  if(actual!==expected)throw new Error(message+" (actual="+actual+", expected="+expected+")");
}
Deno.test("stock and surplus must both be positive",()=>{
  const row={"Código":"123","Descrição":"CABO","Saldo em Estoque":5,DIV:7};
  equal(selectMaterial(row)?.limite,5,"Stock is the physical limit");
  equal(selectMaterial({...row,"Saldo em Estoque":0}),null,"Projected surplus alone cannot be requested");
  equal(selectMaterial({...row,DIV:0}),null,"No surplus: must hide material");
  equal(selectMaterial({...row,DIV:-2}),null,"Negative surplus excluded");
  equal(selectMaterial({...row,"Saldo em Estoque":-1}),null,"Negative stock excluded");
  equal(selectMaterial({...row,DIV:3})?.limite,3,"Surplus can be the tighter limit");
  equal(selectMaterial({...row,DIV:3})?.codigo,"00000123","Normalize TOTVS code");
});
Deno.test("reserved quantities are subtracted from physical cap",()=>{
  equal(availableAfterReservations(5,0),5,"Unreserved stock");
  equal(availableAfterReservations(5,3.5),1.5,"Open requests consume cap");
  equal(availableAfterReservations(5,5.1),0,"No negative offer");
  equal(availableAfterReservations(5,0.345),4.655,"Keep 3 decimal positions");
});
Deno.test("parse localized values without inflating decimals",()=>{
  equal(numeric("1.234,500"),1234.5,"BR number");
  equal(numeric("2.5"),2.5,"JS decimal");
  equal(selectMaterial({"Código":"99","Saldo em Estoque":"2,500",DIV:"1,500"})?.limite,1.5,"BR decimals");
});
Deno.test("display persisted legacy status with new workflow",()=>{
  equal(displayStatus("ABERTA"),"PENDENTE","Pending persisted legacy");
  equal(displayStatus("ATENDIDA"),"SEPARADA","Completed separation");
  equal(displayStatus("PENDENTE"),"PENDENTE","New pending");
  equal(displayStatus("SEPARADA"),"SEPARADA","New separated");
  equal(displayStatus("RECUSADA"),"RECUSADA","Refused remains distinct from pending");
});
console.log("MRP_AVULSAS_CATALOG_OK");
