VALIDACAO_COMPRA_PATCH = r"""
# MRP | COMPRA: previa, exclusoes recuperaveis, lead time e CSV Protheus.
def _compra_replace(old, new, label, count=1):
    global _source
    if _source.count(old) < count:
        raise RuntimeError(f"Compra MRP: local nao encontrado: {label}")
    _source = _source.replace(old, new, count)

# AL = 38a coluna da planilha CADASTROS (indice 37).
# Mesmo criterio no carregamento manual e na Central de Dados.
_cad_old = '    cad=cad[_cad_ok].copy()'
_cad_new = '''    _col_entrega = (
        _cad_raw.iloc[:, 37] if _cad_raw.shape[1] > 37
        else next(
            (_cad_raw[col] for col in _cad_raw.columns
             if str(col).strip().upper() == "ENTREGA"),
            pd.Series(0, index=_cad_raw.index),
        )
    )
    _texto_entrega = _col_entrega.fillna("").astype(str).str.replace(",", ".", regex=False)
    _numero_entrega = _texto_entrega.str.extract(r"^\\s*(\\d+(?:\\.\\d+)?)", expand=False)
    cad["Lead Time (dias)"] = pd.to_numeric(_numero_entrega, errors="coerce").fillna(0).clip(lower=0)
    cad=cad[_cad_ok].copy()'''
# Ha dois carregadores: planilha local e Central de Dados.
if _source.count(_cad_old) != 2:
    raise RuntimeError("Compra MRP: os dois carregadores de CADASTROS nao foram encontrados.")
_source = _source.replace(_cad_old, _cad_new)

_compra_replace(
    'cols=["produto","qnt","data","psy","cc","op","obs","prioridade"]',
    'cols=["produto","qnt","data","psy","cc","op","obs","prioridade","prj"]',
    "Coluna PRJ no normalizador",
)
_compra_replace(
    'for c in ["psy","cc","op","obs","prioridade"]:',
    'for c in ["psy","cc","op","obs","prioridade","prj"]:',
    "Normalizacao da PRJ",
)

_helpers_anchor = 'def zip_bytes(files):'
_helpers = '''def _compra_codigo(valor):
    texto=str(valor or "").strip().replace(".0", "")
    return texto.zfill(8) if texto.isdigit() and len(texto)<=8 else texto

def _preparar_compra_prioridades(df, cad):
    out=normalizar_compra_mrp(df)
    if out.empty:
        return out
    if "Lead Time (dias)" in cad.columns:
        lookup=cad.assign(_codigo=cad["Código"].map(_compra_codigo)).drop_duplicates("_codigo").set_index("_codigo")["Lead Time (dias)"].to_dict()
    else:
        lookup={}
    hoje=pd.Timestamp(date.today()).normalize()
    for idx,linha in out.iterrows():
        lead=max(0.0,float(pd.to_numeric(lookup.get(_compra_codigo(linha["produto"]),0),errors="coerce") or 0))
        data_necessidade=pd.to_datetime(linha["data"],errors="coerce",dayfirst=True)
        if pd.isna(data_necessidade):
            # Nao inventar prioridade se nao houver data de necessidade.
            out.at[idx,"prioridade"]=""
        else:
            # 2 = EMERGENCIAL quando a chegada prevista ultrapassa a necessidade;
            # 1 = NORMAL quando chega no prazo (inclusive igualdade).
            chegada=hoje+pd.Timedelta(days=lead)
            out.at[idx,"prioridade"]="2" if chegada>data_necessidade else "1"
        out.at[idx,"prj"]=""
    return out

def _compra_excel_protheus(df):
    # Carga XLSX do STSUP25: C = texto DD/MM/AAAA; prioridade = J.
    # A rotina converte XLSX em CSV. Datas numericas podem ser
    # convertidas em MM/DD/YYYY; C deve ser texto real.
    from xml.etree import ElementTree as ET
    from zipfile import ZipFile, ZIP_DEFLATED

    base=normalizar_compra_mrp(df).copy()
    if not base.empty:
        if not base["produto"].astype(str).str.fullmatch(r"\d{8}").all():
            raise ValueError("Compra MRP: existem codigos invalidos.")
        if not base["prioridade"].astype(str).isin(["1","2"]).all():
            raise ValueError("Compra MRP: existem prioridades invalidas.")
        datas=base["data"].astype(str).str.strip()
        if not datas.str.fullmatch(r"\d{2}/\d{2}/\d{4}").all():
            raise ValueError("Compra MRP: data deve estar no formato DD/MM/AAAA.")
        if pd.to_datetime(datas,format="%d/%m/%Y",errors="coerce").isna().any():
            raise ValueError("Compra MRP: existem datas de necessidade invalidas.")

    # Layout validado: H sem cabecalho, I vunit, J prioridade, K justificativa.
    # A coluna 'data' e propositalmente STRING, nunca datetime ou serial do Excel.
    colunas=["produto","qnt","data","psy","cc","op","obs","","vunit","prioridade","justificativa"]
    export=pd.DataFrame({
        "produto":base["produto"].astype(str),
        "qnt":base["qnt"],
        "data":base["data"].astype(str),
        "psy":base["psy"],
        "cc":base["cc"],
        "op":base["op"],
        "obs":base["obs"],
        "": [""] * len(base),
        "vunit": [""] * len(base),
        "prioridade":base["prioridade"].astype(str),
        "justificativa": [""] * len(base),
    })[colunas]
    original=excel_bytes({"Compra_MRP":export})

    ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ET.register_namespace("",ns)
    ET.register_namespace("r","http://schemas.openxmlformats.org/officeDocument/2006/relationships")
    folha="xl/worksheets/sheet1.xml"
    estilo="xl/styles.xml"
    destino=BytesIO()
    with ZipFile(BytesIO(original),"r") as entrada:
        raiz=ET.fromstring(entrada.read(folha))
        estilos=ET.fromstring(entrada.read(estilo))
        formatos=estilos.find(f"{{{ns}}}cellXfs")
        if formatos is None:
            raise ValueError("Compra MRP: estilos do Excel ausentes.")
        # Formato 49 e o formato interno de TEXTO do Excel ('@').
        texto_xf=ET.Element(f"{{{ns}}}xf",{
            "numFmtId":"49","fontId":"0","fillId":"0","borderId":"0",
            "xfId":"0","applyNumberFormat":"1",
        })
        formatos.append(texto_xf)
        formatos.set("count",str(len(formatos)))
        estilo_texto=str(len(formatos)-1)

        sheet_data=raiz.find(f"{{{ns}}}sheetData")
        if sheet_data is None:
            raise ValueError("Compra MRP: folha de dados ausente.")
        linhas=sheet_data.findall(f"{{{ns}}}row")
        if len(linhas)!=len(export)+1:
            raise ValueError("Compra MRP: quantidade de linhas inconsistente.")
        for idx,linha in enumerate(linhas):
            numero=linha.get("r")
            celulas={c.get("r"):c for c in linha.findall(f"{{{ns}}}c")}
            for letra in "ABCDEFGHIJK":
                referencia=f"{letra}{numero}"
                celula=celulas.get(referencia)
                if celula is None:
                    celula=ET.Element(f"{{{ns}}}c",{"r":referencia})
                    celulas[referencia]=celula
                if not any(celula.find(f"{{{ns}}}{tag}") is not None for tag in ("v","f","is")):
                    celula.set("t","inlineStr")
                    interno=ET.SubElement(celula,f"{{{ns}}}is")
                    ET.SubElement(interno,f"{{{ns}}}t").text=""
            if idx>0:
                # Escrever explicitamente como string inline + formato @.
                # Isso impede serial numerico 46360 -> 12/4/2026 no Protheus.
                data_c=celulas[f"C{numero}"]
                for filho in list(data_c):
                    data_c.remove(filho)
                data_c.set("t","inlineStr")
                data_c.set("s",estilo_texto)
                interno=ET.SubElement(data_c,f"{{{ns}}}is")
                ET.SubElement(interno,f"{{{ns}}}t").text=export.iloc[idx-1]["data"]
            linha[:]=[celulas[f"{col}{numero}"] for col in "ABCDEFGHIJK"]
        dimensao=raiz.find(f"{{{ns}}}dimension")
        if dimensao is not None:
            dimensao.set("ref",f"A1:K{len(export)+1}")
        conteudo_folha=ET.tostring(raiz,encoding="utf-8",xml_declaration=True)
        conteudo_estilo=ET.tostring(estilos,encoding="utf-8",xml_declaration=True)
        with ZipFile(destino,"w",ZIP_DEFLATED) as saida:
            for info in entrada.infolist():
                if info.filename==folha:
                    conteudo=conteudo_folha
                elif info.filename==estilo:
                    conteudo=conteudo_estilo
                else:
                    conteudo=entrada.read(info.filename)
                saida.writestr(info,conteudo)
    return destino.getvalue()

def _compra_exclusoes_ler():
    token=st.session_state.get("auth_access_token")
    if not token:
        raise RuntimeError("Sessao de acesso expirada: faca login novamente.")
    response=requests.get(
        f"{SUPABASE_URL}/rest/v1/mrp_compra_exclusoes",
        headers=_auth_headers(token),
        params={"select":"produto,excluido,motivo,updated_by,updated_at","order":"produto.asc"},
        timeout=20,
    )
    response.raise_for_status()
    return {_compra_codigo(x["produto"]):x for x in response.json()}

def _compra_exclusoes_salvar(alteracoes):
    if st.session_state.get("auth_role")!="ADMIN":
        raise PermissionError("Somente ADMIN pode alterar exclusoes de compra.")
    token=st.session_state.get("auth_access_token")
    if not token:
        raise RuntimeError("Sessao expirada.")
    from datetime import datetime, timezone
    registros=[{
        "produto":_compra_codigo(codigo),
        "excluido":bool(excluido),
        "motivo":"RETIRADO DA COMPRA" if excluido else "RESTAURADO NA COMPRA",
        "updated_by":str(st.session_state.get("auth_nome") or "ADMIN"),
        "updated_at":datetime.now(timezone.utc).isoformat(),
    } for codigo,excluido in alteracoes.items()]
    if not registros:
        return
    r=requests.post(
        f"{SUPABASE_URL}/rest/v1/mrp_compra_exclusoes",
        headers={**_auth_headers(token),"Prefer":"resolution=merge-duplicates,return=minimal"},
        params={"on_conflict":"produto"},
        json=registros,timeout=25,
    )
    r.raise_for_status()

def _compra_abrir(prefixo):
    # Aprovacoes sao por sessao de analise: reabrir sempre exige confirmar.
    if not st.session_state.get(f"{prefixo}_compra_aberta",False):
        st.session_state.pop(f"{prefixo}_compra_confirmada",None)
    st.session_state[f"{prefixo}_compra_aberta"]=True

def _compra_fechar(prefixo):
    # Excluidos persistem no Supabase; fecha somente a analise e a liberacao.
    st.session_state[f"{prefixo}_compra_aberta"]=False
    st.session_state.pop(f"{prefixo}_compra_confirmada",None)

def _compra_botao_finalizar(prefixo):
    if st.button(
        "FINALIZAR ANÁLISE DE COMPRA",
        key=f"{prefixo}_compra_finalizar",
        use_container_width=True,
    ):
        _compra_fechar(prefixo)
        st.rerun()

def render_validacao_compra_mrp(df, prefixo="admin", cad=None):
    st.markdown("### VALIDAÇÃO DA COMPRA MRP")
    st.caption("Retire produtos que nao devem ser comprados; a decisao fica salva e podera ser revertida. Nao altera a demanda calculada no MRP.")
    try:
        exclusoes=_compra_exclusoes_ler()
    except Exception as exc:
        st.error(f"Nao foi possivel verificar as exclusoes: {exc}. Exportacao de compra bloqueada.")
        _compra_botao_finalizar(prefixo)
        return
    base=normalizar_compra_mrp(df)
    base=base[base["produto"].ne("")].copy()
    if cad is not None and not cad.empty and "Código" in cad.columns:
        _descs=cad.assign(_p=cad["Código"].map(_compra_codigo)).drop_duplicates("_p").set_index("_p")["Descrição"].to_dict()
    else:
        _descs={}
    por_produto=base.groupby("produto",sort=True,as_index=False).agg(
        Qtd=("qnt","sum"),Linhas=("qnt","size"),
        Prioridade=("prioridade",lambda s: "2" if (s=="2").any() else ("1" if (s=="1").any() else "")),
    ) if not base.empty else pd.DataFrame(columns=["produto","Qtd","Linhas","Prioridade"])
    por_produto["Descrição"]=por_produto["produto"].map(lambda c:_descs.get(c,""))
    por_produto["Incluir na compra"]=por_produto["produto"].map(lambda c:not bool(exclusoes.get(c,{}).get("excluido",False)))
    por_produto=por_produto[["Incluir na compra","produto","Descrição","Qtd","Linhas","Prioridade"]]
    excluidos={c for c,v in exclusoes.items() if bool(v.get("excluido"))}
    aptos=base[~base["produto"].isin(excluidos)].copy()
    n_excluidos=len(set(base["produto"])&excluidos)
    k1,k2,k3=st.columns(3)
    k1.metric("Produtos sugeridos",len(por_produto))
    k2.metric("Produtos excluidos",n_excluidos)
    k3.metric("Linhas para exportar",len(aptos))
    if not por_produto.empty:
        st.caption("A seleção vale para o código do material, inclusive em MRP futuros.")
        if st.session_state.get("auth_role")=="ADMIN":
            editado=st.data_editor(
                por_produto,hide_index=True,use_container_width=True,num_rows="fixed",
                disabled=["produto","Descrição","Qtd","Linhas","Prioridade"],
                column_config={
                    "Incluir na compra":st.column_config.CheckboxColumn("INCLUIR",help="Desmarque para armazenar o material na lista de exclusoes."),
                    "produto":st.column_config.TextColumn("PRODUTO"),
                },
                key=f"{prefixo}_revisao_editor",
            )
            mudancas={}
            for _,item in editado.iterrows():
                cod=_compra_codigo(item["produto"])
                futuro=not bool(item["Incluir na compra"])
                atual=bool(exclusoes.get(cod,{}).get("excluido",False))
                if futuro!=atual:
                    mudancas[cod]=futuro
            if mudancas:
                st.warning(f"{len(mudancas)} alteracao(oes) pendente(s). Salve as decisoes antes de exportar.")
                if st.button("SALVAR INCLUSOES / EXCLUSOES",type="primary",key=f"{prefixo}_compra_salvar",use_container_width=True):
                    try:
                        _compra_exclusoes_salvar(mudancas)
                        st.session_state.pop(f"{prefixo}_compra_confirmada",None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Falha ao salvar as decisoes: {exc}")
                _compra_botao_finalizar(prefixo)
                return
        else:
            st.dataframe(por_produto,hide_index=True,use_container_width=True)
    with st.expander(f"CADASTRO DE ITENS EXCLUIDOS / RESTAURACAO ({len(excluidos)})"):
        if not excluidos:
            st.caption("Nenhum material excluido cadastrado.")
        else:
            todos=pd.DataFrame([
                {"Produto":cod,"Descrição":_descs.get(cod,""),"Motivo":exclusoes[cod].get("motivo") or "",
                 "Alterado por":exclusoes[cod].get("updated_by") or ""}
                for cod in sorted(excluidos)
            ])
            st.dataframe(todos,hide_index=True,use_container_width=True)
            if st.session_state.get("auth_role")=="ADMIN":
                para_voltar=st.multiselect("Produtos a restaurar", sorted(excluidos),key=f"{prefixo}_compra_restaurar")
                if st.button("RESTAURAR SELECIONADOS",disabled=not para_voltar,key=f"{prefixo}_compra_repor"):
                    try:
                        _compra_exclusoes_salvar({c:False for c in para_voltar})
                        st.session_state.pop(f"{prefixo}_compra_confirmada",None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Falha ao restaurar: {exc}")
    st.markdown("**PREVIA DA CARGA APROVAVEL**")
    st.dataframe(aptos,hide_index=True,use_container_width=True)
    if aptos.empty:
        st.info("Nenhum item apto para gerar a carga.")
        _compra_botao_finalizar(prefixo)
        return
    if aptos["prioridade"].isin(["1","2"]).sum()!=len(aptos):
        st.error("Existem itens sem prioridade valida. Processe novamente o MRP com o cadastro contendo a coluna AL (Entrega).")
        _compra_botao_finalizar(prefixo)
        return
    # Exige aprovacao explicita antes de disponibilizar qualquer arquivo de compra.
    import hashlib
    assinatura=hashlib.sha256((aptos.to_json(orient="records")+",".join(sorted(excluidos))).encode("utf-8")).hexdigest()
    # O Protheus importa XLSX e converte internamente para CSV.
    # Exibir apenas a planilha compatibilizada com a rotina STSUP25.
    col_confirmar,col_excel,col_finalizar=st.columns([1.8,1.45,1.6])
    with col_confirmar:
        if st.button("CONFIRMAR ANÁLISE E LIBERAR ARQUIVOS",key=f"{prefixo}_compra_confirmar",type="primary",use_container_width=True):
            st.session_state[f"{prefixo}_compra_confirmada"]=assinatura

    aprovado=st.session_state.get(f"{prefixo}_compra_confirmada")==assinatura
    xlsx_valido=None
    if aprovado:
        try:
            xlsx_valido=_compra_excel_protheus(aptos)
        except Exception as exc:
            aprovado=False
            st.error(f"Falha na validação da carga Excel: {exc}")
            st.session_state.pop(f"{prefixo}_compra_confirmada",None)

    with col_excel:
        if aprovado:
            st.download_button(
                "BAIXAR COMPRA MRP — EXCEL",xlsx_valido,"Compra_MRP_Protheus.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{prefixo}_compra_xlsx",use_container_width=True,
            )
        else:
            st.button("BAIXAR COMPRA MRP — EXCEL",disabled=True,key=f"{prefixo}_compra_excel_inativo",use_container_width=True)
    with col_finalizar:
        _compra_botao_finalizar(prefixo)
    if not aprovado:
        st.caption("Confirme a análise para habilitar a planilha Excel do Protheus.")

'''
_compra_replace(_helpers_anchor,_helpers+_helpers_anchor,"Funcoes de compra/CSV")

_fab_anchor='fab_det=op[["ORDEM DE PRODUÇÃO","Código Produto","Semana Entrega"]]'
_compra_replace(_fab_anchor,'compras_mrp=_preparar_compra_prioridades(compras_mrp,cad)\n    '+_fab_anchor,"Prioridades antes de salvar no historico")

# O resultado do MRP pode ser exportado livremente, mas a Compra MRP deve
# passar pela aprovacao. Removemos caminhos alternativos de exportacao direta.
_compra_replace('        "Compra_MRP": comp,\n','',"Remover compra do ZIP da consulta")
_compra_replace('"Compra_MRP":compras_mrp_export,','',"Remover compra do ZIP e Excel geral ADMIN")
_compra_replace(
    'c4.download_button("BAIXAR COMPRA MRP", data=compra_excel_consulta, file_name="Compra_MRP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)',
    '''if c4.button("ANÁLISE DE COMPRA",key="consulta_compra_abrir",use_container_width=True):
        _compra_abrir("consulta")
    if st.session_state.get("consulta_compra_aberta",False):
        render_validacao_compra_mrp(comp,"consulta")''',
    "Bloqueio download direto CONSULTA",
)
_compra_replace(
    'with b4: st.download_button("BAIXAR COMPRA MRP",compra_excel_data,"Compra_MRP.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)',
    '''with b4:
    if st.button("ANÁLISE DE COMPRA",key="admin_compra_abrir",use_container_width=True):
        _compra_abrir("admin")
if st.session_state.get("admin_compra_aberta",False):
    render_validacao_compra_mrp(compras_mrp_export,"admin",cad)''',
    "Bloqueio download direto ADMIN",
)
# Recalcular a compra e prioridades nas sessoes ainda abertas.
_source=_source.replace("MRP-CALC-V2","MRP-CALC-V4-COMPRA-TCTP-GRUPO",1)
_source=_source.replace(
    'MRP-SNAPSHOT-V7-COMPRA-TCTP',
    'MRP-SNAPSHOT-V9-COMPRA-TCTP-GRUPO-OP-OBS',
    1,
)
"""