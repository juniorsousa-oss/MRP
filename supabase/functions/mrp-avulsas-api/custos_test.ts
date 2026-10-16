import {parseCadastroCustos,norm} from "./custos.ts";
function eq(a:unknown,b:unknown,m:string){if(a!==b)throw Error(m+": "+a+" esperado "+b);}
Deno.test("cabecalho na segunda linha do CADASTROS e custo com virgula",()=>{
 const pack={format:"SETTA_SOURCE_V1",sheets:[{rows:[
   [null,null,null,null],
   ["SEM USO","Código","Descrição","VALOR DA ÚLTIMA COMPRA"],
   [null,123,"CABO","1.234,56"],
   [null,42,"RELE",250.5],
   [null,58,"SEM COMPRA",""],
 ]}]};
 const r=parseCadastroCustos(pack,"v11");
 eq(r.status,"ATUALIZADO","status");
 eq(r.coluna,"VALOR DA ÚLTIMA COMPRA","coluna");
 eq(r.valorPorCodigo.get("00000123"),1234.56,"decimal BR");
 eq(r.valorPorCodigo.get("00000042"),250.5,"decimal");
 eq(r.valorPorCodigo.has("00000058"),false,"sem valor nao vira zero");
});
Deno.test("coluna ultimo preco de compra",()=>{
 const r=parseCadastroCustos({format:"SETTA_SOURCE_V1",sheets:[{rows:[
   [],["CODIGO","ULTIMO PREÇO DE COMPRA"],[1,7.5],
 ]}]},"v11");
 eq(r.valorPorCodigo.get("00000001"),7.5,"ultimo preco");
});
Deno.test("ausencia de custo se expressa, nao simula valor",()=>{
 const r=parseCadastroCustos({format:"SETTA_SOURCE_V1",sheets:[{rows:[
   [],["CODIGO","DATA ULTIMA COMPRA"],[1,"2026-10-15"],
 ]}]},"v11");
 eq(r.status,"SEM_COLUNA","status");
 eq(r.valorPorCodigo.size,0,"nao estimar preco");
});
Deno.test("chaves acentuadas",()=>{eq(norm("Código"),"CODIGO","codigo");});
