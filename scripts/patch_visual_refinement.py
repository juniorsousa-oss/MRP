from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')

# 1) Expand the shared visual configuration with every visible title/description.
old = '''DEFAULT_UI_CONFIG = {
    "logo_data": "",
    "logo_width": 220,
    "app_title": "MRP | SETTA",
    "objective": "Planejamento de necessidades de materiais e acompanhamento da demanda.",
    "title_demanda_geral": "DEMANDA GERAL",
    "title_demanda_projeto": "DEMANDA POR PROJETO",
    "color_primary": "#1F4E78",
    "color_title": "#1F4E78",
    "color_header": "#FFFFFF",
    "color_background": "#F5F7FA",
    "color_text": "#1F2937",
}'''
new = '''DEFAULT_UI_CONFIG = {
    "logo_data": "",
    "logo_width": 220,
    "app_title": "MRP | SETTA",
    "objective": "Planejamento de necessidades de materiais e acompanhamento da demanda.",
    "title_demanda_geral": "DEMANDA GERAL",
    "title_demanda_projeto": "DEMANDA POR PROJETO",
    "section_main_title": "MRP — Planejamento de Necessidades de Materiais",
    "section_main_description": "Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. Projeção calculada semana a semana.",
    "section_upload_title": "Bases do MRP",
    "section_upload_description": "Carregue as 5 planilhas tratadas para gerar um novo MRP.",
    "section_consulta_title": "Consulta do MRP",
    "section_consulta_description": "Consulte o último MRP salvo, filtre os materiais e visualize seus detalhes.",
    "section_detail_title": "Detalhamento do material",
    "section_detail_description": "Selecione um material para consultar projeção, demanda, compras e demais informações.",
    "subsection_projection_title": "Projeção semanal",
    "subsection_projection_description": "Evolução semanal do saldo, entradas, produção e demanda.",
    "subsection_demand_title": "S.A. — projetos que geram a demanda",
    "subsection_demand_description": "Projetos e necessidades que compõem a demanda do material selecionado.",
    "subsection_purchases_title": "Compras",
    "subsection_purchases_description": "Pedidos de compra e solicitações de compra vinculados ao material.",
    "section_export_title": "Exportação de relatórios",
    "section_export_description": "Exporte os resultados do MRP nos formatos disponíveis.",
    "section_access_title": "Acesso",
    "section_access_description": "Usuário e perfil atualmente conectados ao sistema.",
    "section_history_title": "Histórico e comparativo de MRP",
    "section_history_description": "Compare versões salvas do MRP e acompanhe as alterações encontradas.",
    "history_current_label": "MRP atual",
    "history_previous_label": "MRP anterior",
    "main_notice": "Envie as 5 planilhas tratadas para calcular um novo MRP. O último MRP salvo fica disponível para consulta e comparação.",
    "color_primary": "#1F4E78",
    "color_title": "#1F4E78",
    "color_header": "#FFFFFF",
    "color_background": "#F5F7FA",
    "color_text": "#1F2937",
}'''
assert old in s
s = s.replace(old, new, 1)

# 2) Replace the incomplete visual editor with a complete text/description editor.
start = s.index('def _render_visual_settings(cfg):')
end = s.index('\ndef _apply_visual_theme(cfg):', start)
new_func = '''def _render_visual_settings(cfg):
    if st.session_state.get("auth_role") != "ADMIN":
        return
    with st.sidebar.expander("CONFIGURAÇÃO VISUAL", expanded=False):
        st.caption("As alterações são salvas no banco compartilhado e aparecem para todos os usuários.")

        logo = st.file_uploader("Cabeçalho / logotipo da empresa", type=["png", "jpg", "jpeg", "webp"], key="ui_logo_upload")
        if cfg.get("logo_data"):
            st.image(cfg["logo_data"], width=int(cfg.get("logo_width") or 220))
            remover_logo = st.checkbox("Remover cabeçalho atual", key="ui_remove_logo")
        else:
            remover_logo = False
        logo_width = st.slider("Largura do logotipo", min_value=120, max_value=500, value=max(120, min(500, int(cfg.get("logo_width") or 220))), step=10)

        st.markdown("**TEXTOS E ORIENTAÇÕES**")
        text_specs = [
            ("section_main_title", "Título principal", "text", 1),
            ("section_main_description", "Descrição do título principal", "area", 2),
            ("main_notice", "Aviso de carregamento / processamento", "area", 2),
            ("section_upload_title", "Título — Bases do MRP", "text", 1),
            ("section_upload_description", "Descrição — Bases do MRP", "area", 2),
            ("section_consulta_title", "Título — Consulta do MRP", "text", 1),
            ("section_consulta_description", "Descrição — Consulta do MRP", "area", 2),
            ("section_detail_title", "Título — Detalhamento do material", "text", 1),
            ("section_detail_description", "Descrição — Detalhamento do material", "area", 2),
            ("subsection_projection_title", "Subtítulo — Projeção semanal", "text", 1),
            ("subsection_projection_description", "Descrição — Projeção semanal", "area", 2),
            ("subsection_demand_title", "Subtítulo — S.A. / projetos", "text", 1),
            ("subsection_demand_description", "Descrição — S.A. / projetos", "area", 2),
            ("subsection_purchases_title", "Subtítulo — Compras", "text", 1),
            ("subsection_purchases_description", "Descrição — Compras", "area", 2),
            ("section_export_title", "Título — Exportação de relatórios", "text", 1),
            ("section_export_description", "Descrição — Exportação de relatórios", "area", 2),
            ("section_history_title", "Título — Histórico e comparativo", "text", 1),
            ("section_history_description", "Descrição — Histórico e comparativo", "area", 2),
            ("history_current_label", "Rótulo — MRP atual", "text", 1),
            ("history_previous_label", "Rótulo — MRP anterior", "text", 1),
            ("section_access_title", "Título — Acesso", "text", 1),
            ("section_access_description", "Descrição — Acesso", "area", 2),
        ]
        edited = {}
        for key, label, kind, height in text_specs:
            value = str(cfg.get(key) or DEFAULT_UI_CONFIG[key])
            if kind == "area":
                edited[key] = st.text_area(label, value=value, height=70 if height == 2 else 50, key=f"ui_{key}")
            else:
                edited[key] = st.text_input(label, value=value, key=f"ui_{key}")

        st.markdown("**TÍTULOS DAS ABAS**")
        edited["title_demanda_geral"] = st.text_input("Aba — Demanda Geral", value=str(cfg.get("title_demanda_geral") or DEFAULT_UI_CONFIG["title_demanda_geral"]), key="ui_title_geral")
        edited["title_demanda_projeto"] = st.text_input("Aba — Demanda por Projeto", value=str(cfg.get("title_demanda_projeto") or DEFAULT_UI_CONFIG["title_demanda_projeto"]), key="ui_title_projeto")

        st.markdown("**IDENTIDADE**")
        edited["app_title"] = st.text_input("Título da marca / aplicação", value=str(cfg.get("app_title") or DEFAULT_UI_CONFIG["app_title"]), key="ui_app_title")
        edited["objective"] = st.text_area("Objetivo da aplicação", value=str(cfg.get("objective") or DEFAULT_UI_CONFIG["objective"]), height=70, key="ui_objective")

        st.markdown("**CORES**")
        edited["color_primary"] = st.color_picker("Cor principal", value=_hex_ok(cfg.get("color_primary"), DEFAULT_UI_CONFIG["color_primary"]), key="ui_color_primary")
        edited["color_title"] = st.color_picker("Cor dos títulos", value=_hex_ok(cfg.get("color_title"), DEFAULT_UI_CONFIG["color_title"]), key="ui_color_title")
        edited["color_header"] = st.color_picker("Cor do cabeçalho", value=_hex_ok(cfg.get("color_header"), DEFAULT_UI_CONFIG["color_header"]), key="ui_color_header")
        edited["color_background"] = st.color_picker("Cor de fundo", value=_hex_ok(cfg.get("color_background"), DEFAULT_UI_CONFIG["color_background"]), key="ui_color_background")
        edited["color_text"] = st.color_picker("Cor do texto", value=_hex_ok(cfg.get("color_text"), DEFAULT_UI_CONFIG["color_text"]), key="ui_color_text")

        if st.button("SALVAR CONFIGURAÇÃO", use_container_width=True, type="primary", key="save_ui_config"):
            new_cfg = {**cfg}
            new_cfg["logo_data"] = "" if remover_logo else cfg.get("logo_data", "")
            new_cfg["logo_width"] = logo_width
            for key, value in edited.items():
                new_cfg[key] = str(value).strip()
            if logo is not None:
                import base64
                mime = logo.type or "image/png"
                new_cfg["logo_data"] = f"data:{mime};base64,{base64.b64encode(logo.getvalue()).decode('ascii')}"
            try:
                _config_save(new_cfg)
                st.session_state["ui_config"] = _config_get()
                st.success("Configuração visual salva.")
                st.rerun()
            except Exception as e:
                st.error(f"Não foi possível salvar a configuração visual: {e}")

'''
s = s[:start] + new_func + s[end:]

# 3) Replace brand CSS and renderer: logo stays at left, application name is centered.
old = '''      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 22px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); }}
      .setta-brand-title {{ color: var(--setta-title); font-size: 2rem; font-weight: 750; line-height: 1.15; margin: 0; }}
      .setta-brand-objective {{ color: var(--setta-text); font-size: 1rem; line-height: 1.5; margin-top: 6px; opacity: .82; }}
      .setta-brand img {{ display: block; max-width: 100%; height: auto; margin-bottom: 12px; }}'''
new = '''      .setta-brand {{ background: var(--setta-header); border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); min-height: 130px; display: grid; grid-template-columns: 1fr 2.2fr 1fr; align-items: center; gap: 12px; }}
      .setta-brand-logo {{ grid-column: 1; justify-self: start; align-self: center; }}
      .setta-brand-logo img {{ display: block; max-width: 100%; height: auto; margin: 0; }}
      .setta-brand-center {{ grid-column: 2; text-align: center; }}
      .setta-brand-title {{ color: var(--setta-title); font-size: 2rem; font-weight: 750; line-height: 1.15; margin: 0; }}
      .setta-brand-objective {{ color: var(--setta-text); font-size: .95rem; line-height: 1.5; margin-top: 7px; opacity: .82; }}'''
assert old in s
s = s.replace(old, new, 1)
old = '''def _render_brand_header(cfg):
    title = str(cfg.get("app_title") or DEFAULT_UI_CONFIG["app_title"])
    objective = str(cfg.get("objective") or "")
    logo = cfg.get("logo_data") or ""
    width = max(120, min(900, int(cfg.get("logo_width") or 220)))
    logo_html = f'<img src="{logo}" style="width:{width}px;" />' if logo else ""
    st.markdown(f'<div class="setta-brand">{logo_html}<div class="setta-brand-title">{title}</div><div class="setta-brand-objective">{objective}</div></div>', unsafe_allow_html=True)'''
new = '''def _render_brand_header(cfg):
    title = str(cfg.get("app_title") or DEFAULT_UI_CONFIG["app_title"])
    objective = str(cfg.get("objective") or "")
    logo = cfg.get("logo_data") or ""
    width = max(120, min(500, int(cfg.get("logo_width") or 220)))
    logo_html = f'<div class="setta-brand-logo"><img src="{logo}" style="width:{width}px;" /></div>' if logo else '<div class="setta-brand-logo"></div>'
    st.markdown(f'<div class="setta-brand">{logo_html}<div class="setta-brand-center"><div class="setta-brand-title">{title}</div><div class="setta-brand-objective">{objective}</div></div><div></div></div>', unsafe_allow_html=True)'''
assert old in s
s = s.replace(old, new, 1)

# 4) History and section text must come from the visual configuration.
s = s.replace('st.subheader("Histórico e comparativo de MRP")', 'st.subheader(UI_CONFIG["section_history_title"])', 1)
s = s.replace('''    try: history=load_snapshot_history()''', '''    if UI_CONFIG.get("section_history_description"):
        st.caption(UI_CONFIG["section_history_description"])
    try: history=load_snapshot_history()''', 1)
s = s.replace('c1,c2=st.columns(2); new_id=c1.selectbox("MRP atual",ids,index=0,format_func=lambda x:labels[x],key="mrp_history_current"); old_ids=[x for x in ids if x!=new_id]', 'c1,c2=st.columns(2); new_id=c1.selectbox(UI_CONFIG["history_current_label"],ids,index=0,format_func=lambda x:labels[x],key="mrp_history_current"); old_ids=[x for x in ids if x!=new_id]', 1)
s = s.replace('old_id=c2.selectbox("MRP anterior",old_ids,index=0,format_func=lambda x:labels[x],key="mrp_history_previous")', 'old_id=c2.selectbox(UI_CONFIG["history_previous_label"],old_ids,index=0,format_func=lambda x:labels[x],key="mrp_history_previous")', 1)

# 5) Consulta/detail/subsections use editable titles and descriptions.
s = s.replace('''    st.subheader("Consulta do MRP")
    st.caption(f"Último MRP salvo — semana {snap.get('semana_mrp') or '-'} | {formatar_data_br(snap.get('created_at'))} | {snap.get('usuario') or '-'}")''', '''    st.subheader(UI_CONFIG["section_consulta_title"])
    if UI_CONFIG.get("section_consulta_description"):
        st.caption(UI_CONFIG["section_consulta_description"])
    st.caption(f"Último MRP salvo — semana {snap.get('semana_mrp') or '-'} | {formatar_data_br(snap.get('created_at'))} | {snap.get('usuario') or '-'}")''', 1)
s = s.replace('''                st.markdown("### Detalhamento do material")
                st.caption(f"Material selecionado: {selecionado} — {desc}")
                st.markdown("**Projeção semanal**")''', '''                st.markdown(f"### {UI_CONFIG['section_detail_title']}")
                if UI_CONFIG.get("section_detail_description"):
                    st.caption(UI_CONFIG["section_detail_description"])
                st.caption(f"Material selecionado: {selecionado} — {desc}")
                st.markdown(f"**{UI_CONFIG['subsection_projection_title']}**")
                if UI_CONFIG.get("subsection_projection_description"):
                    st.caption(UI_CONFIG["subsection_projection_description"])''', 1)
s = s.replace('''                st.markdown("**S.A. — projetos que geram a demanda**")
                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)

                d_comp''', '''                st.markdown(f"**{UI_CONFIG['subsection_demand_title']}**")
                if UI_CONFIG.get("subsection_demand_description"):
                    st.caption(UI_CONFIG["subsection_demand_description"])
                st.dataframe(d_dem, use_container_width=True, hide_index=True, column_order=DEM_COLS)

                d_comp''', 1)
s = s.replace('''                    st.markdown("**Compras**")
                    st.dataframe(d_comp[compras_cols], use_container_width=True, hide_index=True, column_order=compras_cols)''', '''                    st.markdown(f"**{UI_CONFIG['subsection_purchases_title']}**")
                    if UI_CONFIG.get("subsection_purchases_description"):
                        st.caption(UI_CONFIG["subsection_purchases_description"])
                    st.dataframe(d_comp[compras_cols], use_container_width=True, hide_index=True, column_order=compras_cols)''', 1)

# 6) Main ADMIN page, sidebar, notice and export/history labels.
s = s.replace('''st.title("MRP — Planejamento de Necessidades de Materiais"); st.caption("Cadastro + Estoque + Relatório Geral + Compras + MRP TC/TP. Projeção calculada semana a semana.")''', '''st.title(UI_CONFIG["section_main_title"])
if UI_CONFIG.get("section_main_description"):
    st.caption(UI_CONFIG["section_main_description"])''', 1)
s = s.replace('''        st.header("Acesso")
    st.success''', '''        st.header(UI_CONFIG["section_access_title"])
        if UI_CONFIG.get("section_access_description"):
            st.caption(UI_CONFIG["section_access_description"])
    st.success''', 1)
s = s.replace('''        st.header("Bases do MRP")''', '''        st.header(UI_CONFIG["section_upload_title"])
        if UI_CONFIG.get("section_upload_description"):
            st.caption(UI_CONFIG["section_upload_description"])''', 1)
s = s.replace('''    st.info("Envie as 5 planilhas tratadas para calcular um novo MRP. O último MRP salvo fica disponível para consulta e comparação.")''', '''    st.info(UI_CONFIG["main_notice"])''', 1)
s = s.replace('''with tab1:
    st.subheader("Demanda Geral");''', '''with tab1:
    st.subheader(UI_CONFIG["title_demanda_geral"]);''', 1)
s = s.replace('''        st.divider(); st.subheader("Detalhamento do material");''', '''        st.divider(); st.subheader(UI_CONFIG["section_detail_title"])
        if UI_CONFIG.get("section_detail_description"):
            st.caption(UI_CONFIG["section_detail_description"])''', 1)
s = s.replace('''            st.markdown("**Projeção semanal**");''', '''            st.markdown(f"**{UI_CONFIG['subsection_projection_title']}**")
            if UI_CONFIG.get("subsection_projection_description"):
                st.caption(UI_CONFIG["subsection_projection_description"]);''', 1)
s = s.replace('''        if len(d): st.markdown("**S.A. — projetos que geram a demanda**");''', '''        if len(d):
            st.markdown(f"**{UI_CONFIG['subsection_demand_title']}**")
            if UI_CONFIG.get("subsection_demand_description"):
                st.caption(UI_CONFIG["subsection_demand_description"]);''', 1)
s = s.replace('''        if len(compras): st.markdown("**Compras**");''', '''        if len(compras):
            st.markdown(f"**{UI_CONFIG['subsection_purchases_title']}**")
            if UI_CONFIG.get("subsection_purchases_description"):
                st.caption(UI_CONFIG["subsection_purchases_description"]);''', 1)
s = s.replace('''with tab2:
    st.subheader("Demanda por Projeto");''', '''with tab2:
    st.subheader(UI_CONFIG["title_demanda_projeto"]);''', 1)
s = s.replace('''st.divider(); st.subheader("Exportação de relatórios"); st.caption("Os relatórios são exportados com os mesmos dados calculados na tela.")''', '''st.divider(); st.subheader(UI_CONFIG["section_export_title"])
if UI_CONFIG.get("section_export_description"):
    st.caption(UI_CONFIG["section_export_description"])''', 1)

p.write_text(s, encoding='utf-8')
print('visual refinement applied')
