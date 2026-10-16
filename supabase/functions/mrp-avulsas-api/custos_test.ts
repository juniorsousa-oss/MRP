import {parseCadastroCustos,norm,precoUltimaCompra} from "./custos.ts";
function eq(a:unknown,b:unknown,m:string){
  if(a!==b)throw Error(m+": "+a+" esperado "+b);
}
function sample(lines:[string,unknown][],headerM="Ult. Preco"){
  const headers=new Array(13).fill("");
  headers[1]="Codigo";headers[11]="Ex-NBM";headers[12]=headerM;
  const rows:any[][]=[new Array(13).fill(null),headers];
  for(const [code,price] of lines){
    const row=new Array(13).fill(null);row[1]=code;row[12]=price;rows.push(row);
  }
  return {format:"SETTA_SOURCE_V1",sheets:[{rows}]};
}
Deno.test("CADASTROS: codigo B, Ult. Preco M e cabecalho linha 2",()=>{
  const p=sample([
    ["00000001",19.54],
    ["00000002","1.234,56"],
    ["00000003",null],
    ["00000004","N/D"],
    ["00000005",""],
    ["00000006","R$ 25,90"],
    ["00000007",-5],
    ["00  0008",12.3],
  ]);
  const r=parseCadastroCustos(p,"CADASTROS v11");
  eq(r.status,"ATUALIZADO","status");
  eq(r.coluna,"M · Ult. Preco","coluna");
  eq(r.valorPorCodigo.get("00000001"),19.54,"preco numerico");
  eq(r.valorPorCodigo.get("00000002"),1234.56,"preco brasileiro");
  eq(r.valorPorCodigo.get("00000003"),0,"vazio");
  eq(r.valorPorCodigo.get("00000004"),0,"invalido");
  eq(r.valorPorCodigo.get("00000005"),0,"texto vazio");
  eq(r.valorPorCodigo.get("00000006"),25.9,"BRL");
  eq(r.valorPorCodigo.get("00000007"),0,"custo negativo invalido");
  eq(r.valorPorCodigo.get("00000008"),12.3,"codigo com espacos de origem");
  eq(r.valorPorCodigo.get("00000099")??0,0,"codigo nao encontrado");
});
Deno.test("posicao M prevalece sobre cabecalhos concorrentes",()=>{
  const p=sample([["00000042","320.50"]],"CAMPO COM NOME DIFERENTE");
  const r=parseCadastroCustos(p,"v11");
  eq(r.valorPorCodigo.get("00000042"),320.5,"preco sempre M");
  eq(r.coluna,"M · CAMPO COM NOME DIFERENTE","usar indice 12");
});
Deno.test("celula nao numerica, vazia ou fora do arquivo recebe zero",()=>{
  const p=sample([["00000020",undefined],["00000021","SEM PRECO"]]);
  const r=parseCadastroCustos(p,"v11");
  eq(r.valorPorCodigo.get("00000020"),0,"sem celula");
  eq(r.valorPorCodigo.get("00000021"),0,"texto");
  eq(precoUltimaCompra(undefined),0,"indefinido");
  eq(precoUltimaCompra("12 bananas"),0,"texto misturado");
  eq(precoUltimaCompra(""),0,"vazio");
  eq(precoUltimaCompra("0"),0,"zero explicito");
  eq(precoUltimaCompra("1.234,56"),1234.56,"decimal br");
  eq(precoUltimaCompra("Infinity"),0,"nao finito");
});
Deno.test("cabecalho Codigo acentuado",()=>eq(norm("Código"),"CODIGO","normalizacao"));
