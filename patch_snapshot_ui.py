from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')

old = '''if not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):
    st.info("Envie as 5 planilhas tratadas para calcular um novo MRP. O último MRP salvo fica disponível para consulta e comparação.")
    try:
        snap=load_latest_snapshot()
        if snap:
            st.success(f"Último MRP compartilhado: semana {snap.get('semana_mrp') or '-'} | {formatar_data_br(snap.get('created_at'))} | {snap.get('usuario') or '-'}")
            latest_df=snapshot_df(snap,"mrp_geral")
            st.dataframe(latest_df,use_container_width=True,hide_index=True)
            if st.session_state.get("auth_role") == "ADMIN":
                render_mrp_history()
        else: st.info("Ainda não há MRP salvo no banco compartilhado.")
    except Exception as e: st.warning(f"Não foi possível carregar o último MRP: {e}")
    st.stop()
'''

new = '''if not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):
    st.info("Envie as 5 planilhas tratadas para calcular um novo MRP. O último MRP salvo fica disponível para consulta e comparação.")
    try:
        snap=load_latest_snapshot()
        if snap:
            # Quando as bases locais não estão carregadas, o último MRP deve ser
            # apresentado pelo MESMO layout operacional da consulta, nunca por uma
            # tabela simplificada. Isso garante que uma atualização automática do
            # Streamlit não faça desaparecer filtros, abas ou seleção de linha.
            render_consulta_view()
            if st.session_state.get("auth_role") == "ADMIN":
                render_mrp_history()
        else:
            st.info("Ainda não há MRP salvo no banco compartilhado.")
    except Exception as e:
        st.warning(f"Não foi possível carregar o último MRP: {e}")
    st.stop()
'''

if old not in s:
    raise SystemExit('snapshot branch marker not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('snapshot UI branch fixed - trigger')
