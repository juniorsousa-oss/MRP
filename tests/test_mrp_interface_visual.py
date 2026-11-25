"""Regressão do novo cabeçalho e das ações de exportação."""
import ast
import unittest

from mrp_engine_extract import montar_fonte_atual
from mrp_interface_visual import cabecalho_html, etapa_compra_html
from mrp_workspace import workspace_header, workspace_pages, workspace_falta
import pandas as pd


class InterfaceVisualTests(unittest.TestCase):
    def test_cabecalho_titulo_e_dados_por_pagina(self):
        for pagina, titulo in (
            ("MRP ATUAL","MRP atual"),
            ("SOLICITAÇÕES AVULSAS","Solicitações avulsas"),
            ("CONFIGURAÇÕES","Configurações"),
        ):
            html = cabecalho_html(pagina,"data:image/png;base64,UE5H","ATUALIZADO","25/11/2026 07:58")
            self.assertEqual(html.count("<h1>"),1)
            self.assertIn(f"<h1>{titulo}</h1>",html)
            self.assertIn('alt="SETTA"',html)
            self.assertIn("25/11/2026 07:58",html)
        html = cabecalho_html("MRP ATUAL",'x" onerror="alert(1)',"ERRO","<script>")
        self.assertNotIn("<img",html)
        self.assertNotIn("<script>",html)
        self.assertIn("&lt;script&gt;",html)

    def test_cabecalho_mostra_semana_bases_e_alertas_sem_html_injetado(self):
        html = cabecalho_html("MRP ATUAL", None, "ATENÇÃO", "—",
                              semana="2026-47", bases=(4,5), registros="800 REGISTROS",
                              alertas=["Estoque <pendente>"])
        for rotulo in ("Semana atual: 2026-47", "Bases: 4/5", "800 registros",
                       "Estoque &lt;pendente&gt;", "Atenção"):
            self.assertIn(rotulo, html)
        self.assertNotIn("<pendente>", html)

    def test_etapas_com_rotulo_sem_html_injetado(self):
        self.assertIn('>3</span>',etapa_compra_html(3,"Liberar carga oficial"))
        self.assertNotIn("<script>",etapa_compra_html(1,"<script>"))

    def test_acoes_principais_separadas_dos_seis_downloads(self):
        tree = ast.parse(montar_fonte_atual())
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                             and n.func.id == "workspace_header" for n in ast.walk(tree)),1)
        grupos = [n for n in ast.walk(tree) if isinstance(n,ast.With) and
                  any(isinstance(i.context_expr,ast.Call) and i.context_expr.args and
                      isinstance(i.context_expr.args[0],ast.Constant) and
                      i.context_expr.args[0].value == "Exportar" for i in n.items)]
        self.assertEqual(len(grupos),2)
        for grupo in grupos:
            self.assertEqual(sum(isinstance(n,ast.Attribute) and n.attr == "download_button"
                                 for n in ast.walk(grupo)),3)
            self.assertNotIn("ANÁLISE DE COMPRA",ast.unparse(grupo))
        self.assertEqual(len([
            n for n in ast.walk(tree) if isinstance(n,ast.If) and
            ast.unparse(n.test) == "_mrp_page == 'ANÁLISE DE COMPRA'"
            and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name)
                    and c.func.id == "render_validacao_compra_mrp" for c in ast.walk(n))
        ]),2)

    def test_marca_usa_configuracao_e_preserva_perfis(self):
        original="data:image/png;base64,UE5H"
        html=workspace_header("MRP ATUAL",original,"ATUALIZADO","08:10",semana="2026-47",
                              bases=(5,5),registros="",alertas=[],nome="<Conta>",perfil="ADMIN")
        self.assertIn(f'src="{original}"',html)
        self.assertIn("&lt;Conta&gt; · Admin",html)
        for role in ("CONSULTA","OPERADOR"):
            self.assertNotIn("CONFIGURAÇÕES",workspace_pages(role))
            self.assertNotIn("COMPARATIVO MRP",workspace_pages(role))
            self.assertIn("ANÁLISE DE COMPRA",workspace_pages(role))
            self.assertIn("EXCEDENTES",workspace_pages(role))

    def test_falta_e_apenas_apresentacao_do_saldo_final(self):
        src=pd.DataFrame({"DIV":[-4.5,10,""]})
        res=workspace_falta(src)
        self.assertNotIn("Falta",src.columns)
        self.assertEqual(res["Falta"].iloc[:2].tolist(),[4.5,0])
        self.assertTrue(pd.isna(res["Falta"].iloc[2]))
