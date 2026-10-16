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
const money = (v:unknown):number|null => {
  if(v===null||v===undefined||v==="")return null;
  if(typeof v==="number")return Number.isFinite(v)&&v>=0?v:null;
  const s=String(v).trim().replace(/R\$/ig,"").replace(/\s/g,"");
  if(!s)return null;
  const t=s.includes(",")?s.replace(/\./g,"").replace(",","."):s;
  const n=Number(t);
  return Number.isFinite(n)&&n>=0?n:null;
};
export function parseCadastroCustos(payload: unknown,referencia:string):CustoCadastro {
  const rows=(payload as any)?.sheets?.[0]?.rows;
  if((payload as any)?.format!=="SETTA_SOURCE_V1"||!Array.isArray(rows)||rows.length<3)
    throw Error("CADASTROS_NORMALIZADO_INVALIDO");
  const headers=(rows[1] as unknown[]).map(norm);
  const codigoCol=headers.findIndex(h=>h==="CODIGO"||h==="COD MATERIAL"||h==="COD MATERIAL PRODUTO");
  if(codigoCol<0)throw Error("CADASTROS_SEM_CODIGO");
  const forte=new Set([
    "VALOR DA ULTIMA COMPRA","VALOR ULTIMA COMPRA",
    "VALOR ULT COMPRA","VALOR UNITARIO ULTIMA COMPRA",
    "PRECO DA ULTIMA COMPRA","PRECO ULTIMA COMPRA",
    "ULTIMO PRECO DE COMPRA","ULTIMO VALOR DE COMPRA",
    "CUSTO ULTIMA COMPRA","VLR ULT COMPRA","VLR ULTIMA COMPRA",
    "PRC ULT COMPRA","PRC ULTIMA COMPRA",
  ]);
  const strict=headers.map((h,i)=>forte.has(h)?i:-1).filter(i=>i>=0);
  const possible=headers.map((h,i)=> {
    const ultima=/\bULT(?:IMA|IMO)?\b/.test(h);
    const compra=/\bCOMPR(?:A|AS)?\b/.test(h);
    const financeiro=/\b(VALOR|PRECO|PRC|VLR|CUSTO|UNITARIO|V UNIT)\b/.test(h);
    const data=/\b(DATA|DT|QTD|QTDE)\b/.test(h);
    return ultima&&compra&&financeiro&&!data?i:-1;
  }).filter(i=>i>=0);
  const matches=strict.length?strict:possible;
  if(matches.length>1)throw Error("CADASTROS_COLUNA_ULTIMA_COMPRA_AMBIGUA");
  if(matches.length===0)return {valorPorCodigo:new Map(),coluna:null,
    referencia,status:"SEM_COLUNA"};
  const col=matches[0];
  const values=new Map<string,number>();
  for(const r of rows.slice(2)){
    if(!Array.isArray(r))continue;
    const raw=String(r[codigoCol]??"").trim().replace(/\.0$/,"");
    if(!/^\d{1,8}$/.test(raw))continue;
    const v=money(r[col]);
    if(v!==null)values.set(raw.padStart(8,"0"),Math.round(v*10000)/10000);
  }
  return {valorPorCodigo:values,coluna:String(rows[1][col]??""),referencia,
    status:"ATUALIZADO"};
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
