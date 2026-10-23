import {selectMaterial,selectStockMaterial,availableAfterReservations} from "./catalog.ts";
function ok(b:boolean,msg:string){if(!b)throw Error(msg)}
Deno.test("saldo reservado apenas no fluxo excepcional",()=>{
 const row={"Código":"50590","Descrição":"TC 15KV","Saldo em Estoque":3,"DIV":0};
 ok(selectMaterial(row)===null,"convencional preservado");
 const ex=selectStockMaterial(row);
 ok(ex!==null&&ex.codigo==="00050590"&&ex.saldo===3&&ex.div===0,"catálogo excepcional");
});
Deno.test("não permite consultar produto sem saldo físico",()=>{
 ok(selectStockMaterial({"Código":"50590","Saldo em Estoque":0,"DIV":0})===null,"saldo zero");
});
Deno.test("conserva limite de sobra convencional",()=>{
 const m=selectMaterial({"Código":"50590","Saldo em Estoque":3,"DIV":2});
 ok(m!==null&&m.limite===2&&availableAfterReservations(2,1)===1,"normal");
});