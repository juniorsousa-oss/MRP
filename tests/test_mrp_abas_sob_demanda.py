"""Testa as abas, filtros e callbacks montados pelo entrypoint do MRP."""
import ast
import unittest

from streamlit.testing.v1 import AppTest

from mrp_engine_extract import montar_fonte_atual
from mrp_ui_adequacoes_patch import UI_ADEQUACOES_PATCH


def _nome_chamada(node, nome):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == nome


def _guarda_aba(node):
    return isinstance(node, ast.If) and any(
        isinstance(child, ast.Attribute) and child.attr == "open"
        for child in ast.walk(node.test)
    )


def _extrair_interface(tree, *, consulta):
    if consulta:
        func = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "render_consulta_view")
        corpo = func.body
        chave = "_mrp_sidebar_page"
    else:
        corpo = tree.body
        chave = "_mrp_sidebar_page"
    inicio = next(i for i, node in enumerate(corpo)
                  if isinstance(node, ast.Expr) and _nome_chamada(node.value, "_mrp_manter_filtros_de_abas"))
    controles = []
    for node in corpo[inicio:]:
        if sum(_guarda_aba(n) for n in controles) >= 5:
            break
        if _guarda_aba(node):
            contexto = node.body[0]
            assert isinstance(contexto, ast.With)
            if not isinstance(contexto.items[0].context_expr,ast.Name):
                controles.append(node)
                continue
            nome = contexto.items[0].context_expr.id
            contexto.body = [
                stmt for stmt in contexto.body if isinstance(stmt, ast.With)
                and (any(isinstance(item.context_expr, ast.Call)
                         and isinstance(item.context_expr.func, ast.Attribute)
                         and item.context_expr.func.attr == "form" for item in stmt.items)
                     or any(isinstance(item.context_expr, ast.Name)
                            and item.context_expr.id in {"_busca_area","_filtro_area","_colunas_area"}
                            for item in stmt.items))
            ]
            contexto.body += ast.parse(f"st.text({nome!r})").body
            controles.append(node)
        elif sum(_guarda_aba(n) for n in controles) >= 5:
            break
        elif not isinstance(node,ast.If) or ast.unparse(node.test) not in {'_mrp_page == "ANÁLISE DE COMPRA"', '_mrp_page == "EXCEDENTES"', "_mrp_page == 'ANÁLISE DE COMPRA'", "_mrp_page == 'EXCEDENTES'"}:
            controles.append(node)
    assert len([node for node in controles if _guarda_aba(node)]) == 5
    return chave, ast.unparse(ast.Module(body=controles, type_ignores=[]))


class AbasSobDemandaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = montar_fonte_atual()

    def _app(self, consulta, role):
        tree = ast.parse(self.source)
        nomes = {"_mrp_manter_filtros_de_abas", "_limpar_filtros_mrp",
                 "_mrp_dashboard_navigate", "_mrp_consulta_navigate", "_mrp_set_sidebar_page", "_compra_fechar"}
        fontes = [tree, ast.parse(UI_ADEQUACOES_PATCH)]
        helpers = "\n".join(ast.unparse(n) for fonte in fontes for n in fonte.body
                            if isinstance(n, ast.FunctionDef) and n.name in nomes)
        chave, controles = _extrair_interface(tree, consulta=consulta)
        callback = "_mrp_consulta_navigate" if consulta else "_mrp_dashboard_navigate"
        app = AppTest.from_string(
            """
import pandas as pd
import streamlit as st
from mrp_workspace import WorkspaceSection, workspace_pages
UI_CONFIG = {"title_demanda_geral":"DEMANDA GERAL","title_demanda_projeto":"DEMANDA POR PROJETO"}
mg = pd.DataFrame({"Código":[42],"Status":["OK"],"Tipo":["MP"]})
macro = mg
MRP_COLS = ["Código","Descrição","Tipo","Status","Demanda"]
cad = mg
tipos = ["MP"]
semanas = [202644]
dem = pd.DataFrame({"Projeto":["1001"],"Produto":[42],"Semana de Necessidade":[202644]})
demanda_projeto = dem
def formatar_semana(x): return str(x)
"""
            + f'\nst.session_state["auth_role"]={role!r}\n'
            + '\n_mrp_page=st.session_state.get("_mrp_sidebar_page","MRP ATUAL")\nif _mrp_page not in workspace_pages(st.session_state.auth_role): _mrp_page="MRP ATUAL"\n'
            + helpers
            + f'\nst.button("Atalho KPI",on_click={callback},args=("🟡 ATENÇÃO AO PRAZO",False))\n'
            + controles
            + '\nst.button("ANÁLISE DE COMPRA")\n'
        ).run()
        self.assertFalse(app.exception)
        return app, chave

    def test_admin_ativa_so_uma_aba_preserva_filtros_e_atalho(self):
        app, chave = self._app(consulta=False, role="ADMIN")
        self.assertEqual([x.value for x in app.text], ["tab1"])
        app.text_input(key="admin_descricao_geral").set_value("cabo")
        next(b for b in app.button if b.label == "Buscar").click().run()
        app.session_state[chave] = "COMPARATIVO MRP"
        app.run()
        self.assertEqual([x.value for x in app.text], ["tab4"])
        self.assertFalse(app.text_input)
        app.session_state[chave] = "TRATATIVA DE PROJETOS"
        app.run()
        self.assertEqual([x.value for x in app.text], ["tab3"])
        app.button[0].click().run()
        self.assertEqual([x.value for x in app.text], ["tab2"])
        self.assertEqual(app.selectbox(key="admin_status_atendimento").value,"🟡 ATENÇÃO AO PRAZO")
        app.session_state[chave] = "MRP ATUAL"
        app.run()
        self.assertEqual(app.text_input(key="admin_descricao_geral").value,"cabo")
        self.assertTrue(any(b.label == "ANÁLISE DE COMPRA" for b in app.button))
        next(b for b in app.button if b.label == "Limpar").click().run()
        self.assertEqual(app.text_input(key="admin_descricao_geral").value,"")
        self.assertFalse(app.exception)

    def test_consulta_preserva_filtros_sem_expor_comparativo(self):
        for role in ("CONSULTA","OPERADOR"):
            with self.subTest(role=role):
                self._verificar_consulta(role)

    def _verificar_consulta(self, role):
        app, chave = self._app(consulta=True, role=role)
        self.assertEqual([x.value for x in app.text], ["tab_geral"])
        app.session_state[chave] = "COMPARATIVO MRP"
        app.run()
        self.assertEqual([x.value for x in app.text], ["tab_geral"])
        app.button[0].click().run()
        self.assertEqual([x.value for x in app.text], ["tab_projeto"])
        app.text_input(key="consulta_projeto_descricao").set_value("motor")
        next(b for b in app.button if b.label == "INICIAR PESQUISA").click().run()
        app.session_state[chave] = "MRP ATUAL"
        app.run()
        self.assertFalse(any(x.key == "consulta_projeto_descricao" for x in app.text_input))
        app.session_state[chave] = "DEMANDA POR PROJETO"
        app.run()
        self.assertEqual(app.text_input(key="consulta_projeto_descricao").value,"motor")
        self.assertFalse(app.exception)
