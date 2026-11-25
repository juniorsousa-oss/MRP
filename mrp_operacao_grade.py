"""Grade paginada: somente visualização, ordenação local e seleção de material."""
import hashlib
import json
import re
from numbers import Integral

import streamlit as st

METRICAS_DEMANDA = (
    ("Demanda", "Necessidade"), ("Saldo em Estoque", "Estoque"),
    ("P.C.", "P.C."), ("S.C.", "S.C."),
    ("Produzindo", "Produzindo"), ("Falta", "Falta"),
)

HTML = """
<section class="op-grid" aria-label="Materiais do MRP">
  <div class="op-scroll" tabindex="0" aria-label="Tabela de materiais, com rolagem horizontal">
    <table><thead></thead><tbody></tbody></table>
    <div class="op-mobile"></div>
  </div>
  <footer>
    <span class="op-range" aria-live="polite"></span>
    <div class="op-pages">
      <label>Por página <select aria-label="Materiais por página"><option>10</option><option>20</option><option>50</option></select></label>
      <button type="button" data-step="-1" aria-label="Página anterior">‹</button>
      <span class="op-page" aria-label="Página atual"></span>
      <button type="button" data-step="1" aria-label="Próxima página">›</button>
    </div>
  </footer>
</section>
"""

CSS = """
:host{display:block}
.op-grid{font-family:inherit;color:#172437;background:#fff;border:1px solid #dce3ec;
  border-radius:9px;overflow:hidden;width:100%;box-sizing:border-box;font-size:13px}
.op-scroll{container-type:inline-size;overflow:auto;max-height:66vh;min-height:48px}
table{border-collapse:separate;border-spacing:0;width:100%;min-width:715px}
th,td{padding:0 12px;height:43px;border-bottom:1px solid #e2e8f0;vertical-align:middle;text-align:left}
th{position:sticky;top:0;background:#f4f7fb;color:#213e60;z-index:1;height:36px;white-space:nowrap}
th button{padding:0;color:inherit;background:transparent;border:0;font:inherit;font-weight:700;text-align:inherit;cursor:pointer}
th button .op-arrow{color:#4e637d;margin-left:5px}
tr:nth-child(even) td{background:#fff}
tr:hover td{background:#eef4fb}
td.op-id{color:#213e60;font:600 12px ui-monospace,monospace;white-space:nowrap}
td.op-name{min-width:218px;max-width:440px}
td.op-name span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.op-num{text-align:center;font-variant-numeric:tabular-nums;white-space:nowrap}
.op-center,.op-action{text-align:center}
.op-status{display:inline-flex;gap:5px;align-items:center;white-space:nowrap;
  padding:3px 8px;border-radius:5px;background:#edf1f6;color:#465a71;font-size:11px;font-weight:650}
.op-status.risk{background:#fbe9ec;color:#9e293b}.op-status.ok{background:#e8f3ed;color:#246549}
.op-status:before{content:"";background:currentColor;width:5px;height:5px;border-radius:50%}
.op-detail,.op-pages button{background:#fff;color:#213e60;border:1px solid #dce3ec;
  border-radius:5px;font:inherit;font-weight:700;min-width:29px;height:28px;cursor:pointer}
.op-detail{font-size:12px;line-height:20px;padding:0 8px;white-space:nowrap}.op-detail:hover,.op-pages button:hover{background:#e9f0fa}
.op-grid button:focus-visible,.op-grid select:focus-visible,.op-scroll:focus-visible{outline:2px solid #315983;outline-offset:-1px}
footer,.op-pages,footer label{display:flex;align-items:center;gap:10px}
footer{padding:10px 12px;justify-content:space-between;flex-wrap:wrap;color:#4d6075;min-height:25px}
footer select{font:inherit;color:#213e60;background:#fff;border:1px solid #dce3ec;padding:3px;border-radius:4px}
.op-pages button:disabled{opacity:.45;cursor:default}
.op-empty{text-align:center;color:#4d6075;height:85px}
td.op-missing{color:#a92631;font-weight:750}
.op-mobile{display:none}
@container (max-width:700px){
  table{display:none}
  .op-mobile{display:block}
  .op-item{padding:10px 12px;border-bottom:1px solid #e5eaf1;overflow:hidden}
  .op-item-top,.op-item-bottom{display:flex;gap:7px;align-items:center;justify-content:space-between}
  .op-item-name{font-weight:750;font-size:13px;margin:4px 0;word-break:break-word}
  .op-item-values{flex:1;min-width:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
    gap:5px 4px;font-size:11px;color:#4d6077}
  .op-item-value{text-align:center;overflow-wrap:anywhere}
  .op-item-value b{display:block;color:#172435;font-variant-numeric:tabular-nums}
  .op-item-value.alert b{color:#a92631}
  .op-item .op-detail{flex:none;min-height:32px;min-width:55px;font-size:12px}
  footer{gap:7px;padding:8px}
}

"""

JS = r"""
const states = new WeakMap();
const count = new Intl.NumberFormat("pt-BR"), lex = new Intl.Collator("pt-BR",{numeric:true,sensitivity:"base"});
const numbers = new Set(["Saldo em Estoque","Demanda","P.C.","S.C.","Produzindo","SF","Falta"]);
function columnClass(key) {
  return numbers.has(key) ? "op-num" : key==="Código" || key==="Descrição" ? "" : "op-center";
}
function make(tag,value,cls) {
  const el = document.createElement(tag);
  if (value !== undefined) el.textContent = value;
  if (cls) el.className=cls;
  return el;
}
export default function({data,parentElement,setTriggerValue}) {
  const root=parentElement.querySelector(".op-grid");
  const rows=data.rows, columns=data.columns, previous=states.get(root);
  const s=previous?.version===data.version ? previous
    : {version:data.version,page:0,size:10,sort:null,desc:false};
  if(s.sort!==null && s.sort>=columns.length) s.sort=null;
  states.set(root,s);
  const header=root.querySelector("thead"), body=root.querySelector("tbody"), mobile=root.querySelector(".op-mobile");
  const size=root.querySelector("select");size.value=String(s.size);
  const pages=[...root.querySelectorAll("[data-step]")];
  function render() {
    const ordered=rows.map((row,i)=>({row,i}));
    if(s.sort!==null) {
      const numeric=numbers.has(columns[s.sort].key);
      ordered.sort((a,b)=>{
        const first=a.row[s.sort], second=b.row[s.sort];
        const aNum=Number(first.replace(",", ".")), bNum=Number(second.replace(",", "."));
        const v=numeric && first!=="" && second!=="" && Number.isFinite(aNum) && Number.isFinite(bNum)
                  ? aNum-bNum : lex.compare(first,second);
        return (s.desc ? -v : v)||a.i-b.i;
      });
    }
    const last=Math.max(0,Math.ceil(ordered.length/s.size)-1);
    s.page=Math.min(last,Math.max(0,s.page));
    const start=s.page*s.size, view=ordered.slice(start,start+s.size);
    const h=make("tr");
    columns.forEach((col,i)=>{
      const th=make("th",undefined,columnClass(col.key));
      th.scope="col";
      if(s.sort===i) th.setAttribute("aria-sort",s.desc?"descending":"ascending");
      const b=make("button",col.label);b.type="button";
      if(s.sort===i) b.append(make("span",s.desc?"↓":"↑","op-arrow"));
      b.onclick=()=>{
        s.desc=s.sort===i?!s.desc:false;s.sort=i;s.page=0;render();
        header.querySelectorAll("button")[i]?.focus({preventScroll:true});
      };
      th.append(b);h.append(th);
    });
    const details=make("th","Detalhe","op-action");details.scope="col";h.append(details);
    header.replaceChildren(h);
    const content=document.createDocumentFragment();
    if(!view.length) {
      const tr=make("tr"), td=make("td","Nenhum material encontrado.","op-empty");
      td.colSpan=columns.length+1;tr.append(td);content.append(tr);
    }
    for(const {row,i} of view) {
      const tr=make("tr");
      columns.forEach((col,j)=>{
        const value=row[j]||"—", td=make("td");
        if(col.key==="Código") td.className="op-id";
        else td.className=columnClass(col.key);
        if(col.key==="Falta" && Number(value.replace(",", "."))>0) td.classList.add("op-missing");
        if(col.key==="Descrição") {
          td.className="op-name";const label=make("span",value);label.title=value;td.append(label);
        } else if(col.key==="Status" && row[j]) {
          td.append(make("span",value,(value==="CRIAR S.C."?"op-status risk":value==="OK"?"op-status ok":"op-status")));
        } else td.textContent=value;
        tr.append(td);
      });
      const cell=make("td",undefined,"op-action"), detail=make("button","Detalhe ›","op-detail");
      detail.type="button";detail.setAttribute("aria-label","Detalhar material "+row[0]);
      detail.onclick=()=>setTriggerValue("detail",{index:i,version:data.version});
      cell.append(detail);tr.append(cell);content.append(tr);
    }
    body.replaceChildren(content);
    const cards=document.createDocumentFragment();
    if(!view.length) cards.append(make("p","Nenhum material encontrado.","op-empty"));
    for(const {row,i} of view){
      const item=make("article",undefined,"op-item"), top=make("div",undefined,"op-item-top");
      const bottom=make("div",undefined,"op-item-bottom"), meds=make("div",undefined,"op-item-values");
      const display=data.mobile[i];
      top.append(make("span",row[0],"op-id"));
      const status=display.at(-1);
      if(status) top.append(make("span",status,status==="CRIAR S.C."?"op-status risk":status==="OK"?"op-status ok":"op-status"));
      data.metrics.forEach(({key,label},j)=>{
        const value=display[j]||"—";
        const chip=make("span",label,"op-item-value"+(key==="Falta" && Number(value.replace(",", "."))>0?" alert":""));
        chip.append(make("b",value));meds.append(chip);
      });
      const detail=make("button","Detalhe ›","op-detail");
      detail.type="button";detail.setAttribute("aria-label","Detalhar material "+row[0]);
      detail.onclick=()=>setTriggerValue("detail",{index:i,version:data.version});
      bottom.append(meds,detail);
      item.append(top,make("div",row[1]||"—","op-item-name"),bottom);cards.append(item);
    }
    mobile.replaceChildren(cards);
    root.querySelector(".op-range").textContent=ordered.length ?
      count.format(start+1)+"–"+count.format(start+view.length)+" de "+count.format(ordered.length)+" materiais" : "0 materiais";
    root.querySelector(".op-page").textContent=(s.page+1)+" / "+(last+1);
    pages[0].disabled=s.page===0;pages[1].disabled=s.page===last;
  }
  size.onchange=()=>{s.size=Number(size.value)||10;s.page=0;render()};
  pages.forEach(b=>b.onclick=()=>{s.page+=Number(b.dataset.step);render()});
  render();
}
"""


@st.cache_resource(show_spinner=False)
def _component():
    # Não reutilizar os ativos do componente anterior após atualização no Streamlit Cloud.
    assets = hashlib.blake2s((HTML + CSS + JS).encode(), digest_size=8).hexdigest()
    return st.components.v2.component(f"setta_materiais_grade_{assets}", html=HTML, css=CSS, js=JS)


def grade_resultado(frame, colunas, base_key):
    colunas = ["SF" if c == "DIV" else c for c in colunas]
    labels = dict(METRICAS_DEMANDA)
    fixed = [c for c in ("Código", "Descrição") if c in colunas]
    colunas = fixed + [c for c in labels if c in colunas] + [
        c for c in colunas if c not in fixed and c not in labels
    ]
    visual = frame.rename(columns={"DIV":"SF"}).reindex(columns=colunas)
    rows = visual.fillna("").astype(str).values.tolist()
    for row in rows:
        if re.fullmatch(r"[0-9]+(?:\.0+)?", row[0]):
            row[0] = row[0].split(".")[0].zfill(8)
    # O evento carrega a versão da grade para não selecionar outra linha
    # se a sessão tiver recebido bases ou filtros novos nesse intervalo.
    mobile = frame.reindex(columns=[*labels, "Status"]).fillna("").astype(str).values.tolist()
    version=hashlib.blake2s(json.dumps([colunas,rows,mobile],ensure_ascii=False).encode(),digest_size=8).hexdigest()
    data={"columns":[{"key":c,"label":labels.get(c,"Atendimento" if c=="Semana de Atendimento" else c)}
                     for c in colunas], "rows":rows, "mobile":mobile, "version":version,
          "metrics":[{"key":k,"label":label} for k,label in METRICAS_DEMANDA]}
    result=_component()(key=f"{base_key}_operacao", data=data)
    event=getattr(result,"detail",None)
    if not isinstance(event,dict) or event.get("version")!=version:
        return None
    index=event.get("index")
    return int(index) if isinstance(index,Integral) and not isinstance(index,bool) and 0<=index<len(rows) else None
