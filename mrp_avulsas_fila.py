"""Fila de apresentação das S.A.s. Nunca consulta ou escreve no backend."""
import hashlib
import json
import re

import streamlit as st

STATUS = {
    "PENDENTE": ("Aguardando separação", "pendente"),
    "SEPARADA": ("Aguardando entrega", "separada"),
    "ENTREGUE": ("Entregue", "entregue"),
    "RECUSADA": ("Recusada", "recusada"),
    "LEGADO": ("Registro anterior", "neutra"),
    "PARCIAL": ("Tratativa parcial", "neutra"),
    "FINAL_PENDENTE": ("Pendente de conferência", "pendente"),
    "FINAL_CONCLUIDA": ("Conferida", "entregue"),
}

PAGE_CSS = """
<style>
[class*="st-key-mrp_sa_acoes"] button {min-height:40px}
.st-key-mrp_sa_detalhe {background:#fff;border:1px solid #dce3ec;border-radius:8px;padding:.8rem}
.st-key-mrp_sa_detalhe h3 {margin:0;font-size:1.18rem}
@media(max-width:680px){
  [class*="st-key-mrp_sa_acoes"] button,.st-key-mrp_sa_detalhe button {min-height:44px}
  .st-key-mrp_sa_detalhe {padding:.45rem}
}
</style>
"""

HTML = """
<section class="sa" aria-label="Fila de solicitações">
 <table><thead><tr><th scope="col">S.A.</th><th scope="col">Data</th><th scope="col">Solicitante</th>
 <th scope="col">Finalidade</th><th scope="col">Itens</th><th scope="col">Situação</th><th scope="col">Detalhe</th></tr></thead><tbody></tbody></table>
 <p class="sa-empty" hidden>Nenhuma solicitação para os filtros selecionados.</p>
</section>
"""
CSS = """
.sa{font-family:inherit;color:#172437;background:#fff;border:1px solid #dce3ec;border-radius:9px;overflow:hidden;font-size:.86rem}
table{width:100%;border-collapse:collapse;table-layout:fixed}
th,td{padding:10px 8px;text-align:left;border-bottom:1px solid #e2e8f0;overflow-wrap:anywhere}
th{color:#213e60;background:#eaf0f6}
th:first-child{width:15%}th:nth-child(2){width:17%}th:nth-child(5){width:7%}th:nth-child(6){width:18%}th:last-child{width:13%}
tr:last-child td{border-bottom:0}tr:nth-child(even) td{background:#f9fbfd}
.sa-num{font-weight:700;color:#213e60}.sa-empty{padding:12px}
.sa-tag{display:inline-block;border-radius:6px;padding:4px 7px;font-size:.74rem;font-weight:700;background:#eef1f6;color:#465a71}
.sa-tag.pendente{background:#fff1d7;color:#78500c}.sa-tag.separada{background:#e9f0fa;color:#294d72}
.sa-tag.entregue{background:#e9f5ed;color:#245b42}.sa-tag.recusada{background:#fbe9ed;color:#942c3b}
button{min-height:33px;border:1px solid #ccd8e5;border-radius:6px;background:white;color:#213e60;font:inherit;font-weight:650;cursor:pointer;padding:4px 8px}
button:focus-visible{outline:2px solid #315983;outline-offset:2px}
@media(max-width:740px){
 table,tbody{display:block}thead{position:absolute;width:1px;height:1px;clip-path:inset(50%);overflow:hidden}
 tr{display:grid;grid-template-columns:1fr auto;gap:5px 10px;padding:11px 12px;border-bottom:1px solid #e2e8f0}
 td,tr:nth-child(even) td{border:0;padding:0;background:transparent}
 td:first-child{grid-row:1;grid-column:1}td:nth-child(6){grid-row:1;grid-column:2;text-align:right}
 td:nth-child(2),td:nth-child(3),td:nth-child(4){grid-column:1/-1}
 td:nth-child(5){align-self:center}td:last-child{grid-column:2;justify-self:end}
 button{min-height:40px}
}
"""
JS = r"""
export default function({data,parentElement,setTriggerValue}) {
 const t=parentElement.querySelector("tbody"), table=t.closest("table"), empty=parentElement.querySelector(".sa-empty");
 t.replaceChildren(); table.hidden=!data.rows.length; empty.hidden=!!data.rows.length;
 for(const r of data.rows){
   const tr=document.createElement("tr");
   for(const [ix,s] of [r.numero,r.data,r.solicitante,r.finalidade,r.itens,r.rotulo].entries()){
     const td=document.createElement("td");
     if(ix===5){const tag=document.createElement("span");tag.className="sa-tag "+r.classe;tag.textContent=s;td.append(tag);}
     else{if(ix===0)td.className="sa-num";td.textContent=(ix===4?"Itens: ":"")+s;}
     tr.append(td);
   }
   const td=document.createElement("td"), b=document.createElement("button");
   b.type="button";b.textContent="Detalhe ›";b.setAttribute("aria-label","Detalhar "+r.numero);
   b.onclick=()=>setTriggerValue("open",{id:r.id,version:data.version});
   td.append(b);tr.append(td);t.append(tr);
 }
}
"""


def preparar_fila(pedidos, itens, protocolo, hora, finalidades, estados_legados=None, conferencia=None):
    """Recebe somente as solicitações já autorizadas para o perfil pela API."""
    contagens = {}
    for item in itens:
        chave = str(item.get("pedido_id") or "")
        if chave:
            contagens[chave] = contagens.get(chave, 0) + 1
    rows = []
    for p in pedidos:
        id_ = str(p.get("id") or "")
        if not id_:
            continue
        estado = conferencia or (estados_legados or {}).get(id_) or str(p.get("estado") or "LEGADO")
        label, cls = STATUS.get(estado, STATUS["LEGADO"])
        rows.append({
            "id": id_, "numero": protocolo(p), "data": hora(p.get("entregue_em") if conferencia else p.get("criado_em")) or "—",
            "solicitante": str(p.get("solicitante") or "—"),
            "finalidade": str(finalidades.get(str(p.get("finalidade")), "Registro anterior")).capitalize(),
            "itens": contagens.get(id_, 0), "estado": estado, "rotulo": label, "classe": cls,
        })
    return rows


def filtrar_fila(rows, termo="", estado="TODAS"):
    q = re.sub(r"[^\w]", "", termo.strip().casefold())
    if q.isascii() and q.isdigit():
        q = q.lstrip("0") or "0"
    return [r for r in rows if (estado == "TODAS" or r["estado"] == estado)
            and (not q or q in re.sub(r"[^\w]", "", r["numero"].casefold()))]


@st.cache_resource(show_spinner=False)
def _component():
    return st.components.v2.component("setta_solicitacoes_fila", html=HTML, css=CSS, js=JS)


def fila_view(rows, chave, situacoes=(), padrao="TODAS"):
    page_key = chave + "_pagina"
    chosen_key = chave + "_selecionada"
    for suffix in ("_busca", "_status"):
        k = chave + suffix
        if k in st.session_state:
            st.session_state[k] = st.session_state[k]
    allowed = {row["id"] for row in rows}
    chosen = st.session_state.get(chosen_key)
    if chosen in allowed:
        with st.container(key="mrp_sa_acoes_"+chave):
            if st.button("Voltar à fila", key=chave+"_voltar", icon=":material/arrow_back:"):
                st.session_state.pop(chosen_key, None)
                st.rerun()
        return chosen
    if chosen:
        st.session_state.pop(chosen_key, None)
    st.session_state.setdefault(page_key, 1)
    def reset_page():
        st.session_state[page_key] = 1

    with st.container(key="mrp_sa_acoes_filtros_"+chave):
        left, right = st.columns([3,2]) if situacoes else (st, None)
        termo = left.text_input("Buscar por número da S.A.", placeholder="Ex.: SA-000042 ou 42",
                                key=chave+"_busca", on_change=reset_page)
        estado = "TODAS"
        if right is not None:
            opts = ["TODAS", *situacoes]
            counts = {k: sum(row["estado"] == k for row in rows) for k in situacoes}
            estado = right.selectbox("Situação", opts, index=opts.index(padrao) if padrao in opts else 0,
                                     format_func=lambda k: (f"Todas ({len(rows)})" if k == "TODAS" else
                                         f"{STATUS[k][0]} ({counts[k]})"),
                                     key=chave+"_status", on_change=reset_page)
    filtered = filtrar_fila(rows, termo, estado)
    total = len(filtered)
    maxpage = max(1, (total+9)//10)
    page = min(maxpage, max(1, st.session_state[page_key]))
    st.session_state[page_key] = page
    visible = filtered[(page-1)*10:page*10]
    version = hashlib.sha256(json.dumps(visible,ensure_ascii=False).encode()).hexdigest()
    result = _component()(key=chave+"_grade", data={"rows":visible,"version":version})
    event = getattr(result,"open",None)
    if (isinstance(event, dict) and event.get("version") == version
            and isinstance(event.get("id"),str) and any(row["id"] == event["id"] for row in visible)):
        st.session_state[chosen_key] = event["id"]
        st.rerun()
    st.caption(f"{total} {'solicitação' if total == 1 else 'solicitações'} · Página {page} de {maxpage}")
    if maxpage > 1:
        prev,next_ = st.columns(2)
        if prev.button("Anterior", key=chave+"_anterior", disabled=page==1):
            st.session_state[page_key] = page-1
            st.rerun()
        if next_.button("Próxima", key=chave+"_proxima", disabled=page==maxpage):
            st.session_state[page_key] = page+1
            st.rerun()
    return None
