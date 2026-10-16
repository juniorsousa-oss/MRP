/** Consulta somente leitura ao CADASTROS normalizado na Central SETTA.
 *  O estoque/divisão continua vindo exclusivamente do último snapshot MRP.
 */
export type CustoCadastro = {
  valorPorCodigo: Map<string,number>;
  coluna: string | null;
  referencia: string;
  status: "ATUALIZADO" | "SEM_COLUNA" | "FONTE_INDISPONIVEL";
};
export const norm = (v: unknown) => String(v??"").normalize("NFKD")
  .replace(/[\u0300-\u036f]/g,"").toUpperCase().trim()
  .replace(/[^A-Z0-9]+/g," ").trim();
/** Preco da ultima compra = coluna M (indice 12), independente do cabecalho.
 *  Codigo = coluna B (indice 1), dados apos o cabecalho da linha 2.
 *  Vazio, invalido, nao cadastrado e nao numerico equivalem a R$ 0,00.
 */
export function precoUltimaCompra(v:unknown):number{
  if(typeof v==="number")return Number.isFinite(v)&&v>=0?Math.round(v*10000)/10000:0;
  const raw=String(v??"").trim().replace(/R\$/gi,"").replace(/\s/g,"");
  if(!raw)return 0;
  const numeric=raw.includes(",")?raw.replace(/\./g,"").replace(",","."):raw;
  // Nao aceitar "1abc" ou tokens com separadores invalidos.
  if(!/^\+?(?:\d+(?:\.\d+)?|\.\d+)$/.test(numeric))return 0;
  const price=Number(numeric);
  return Number.isFinite(price)&&price>=0?Math.round(price*10000)/10000:0;
}
export function parseCadastroCustos(payload: unknown,referencia:string):CustoCadastro {
  const rows=(payload as any)?.sheets?.[0]?.rows;
  if((payload as any)?.format!=="SETTA_SOURCE_V1"||!Array.isArray(rows)||rows.length<2)
    throw Error("CADASTROS_NORMALIZADO_INVALIDO");
  const colCodigo=1, colPreco=12; // B e M do modelo original SETTA.
  const header=Array.isArray(rows[1])?rows[1]:[];
  const colName=String(header[colPreco]??"COLUNA M");
  const values=new Map<string,number>();
  for(const row of rows.slice(2)){
    if(!Array.isArray(row))continue;
    const raw=String(row[colCodigo]??"").trim().replace(/\s/g,"").replace(/\.0$/,"");
    if(!/^\d{1,8}$/.test(raw))continue;
    values.set(raw.padStart(8,"0"),precoUltimaCompra(row[colPreco]));
  }
  return {valorPorCodigo:values,coluna:"M · "+colName,referencia,status:"ATUALIZADO"};
}

let cache:{until:number;version:number;result:CustoCadastro}|null=null;
export async function carregarCustos(admin:any):Promise<CustoCadastro>{
  const {data:meta,error}=await admin.from("setta_normalized_sources")
    .select("source_version,status,storage_path")
    .eq("source_key","cadastros").maybeSingle();
  if(error||!meta||meta.status!=="ATUALIZADO"||!meta.storage_path){
    return {valorPorCodigo:new Map(),coluna:null,referencia:"",status:"FONTE_INDISPONIVEL"};
  }
  const ver=Number(meta.source_version||0);
  if(cache&&cache.until>Date.now()&&cache.version===ver)return cache.result;
  const {data:blob,error:downloadError}=await admin.storage.from("setta-data")
    .download(String(meta.storage_path));
  if(downloadError||!blob){
    return {valorPorCodigo:new Map(),coluna:null,referencia:"",status:"FONTE_INDISPONIVEL"};
  }
  const expanded=new Response(blob.stream().pipeThrough(new DecompressionStream("gzip")));
  const parsed=JSON.parse(await expanded.text());
  const result=parseCadastroCustos(parsed,"CADASTROS · versão "+ver);
  cache={until:Date.now()+600000,version:ver,result};
  return result;
}
