"""Regressão do novo cabeçalho e das ações de exportação."""
import ast
import unittest

from mrp_engine_extract import montar_fonte_atual
from mrp_interface_visual import cabecalho_html, etapa_compra_html


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

    def test_etapas_com_rotulo_sem_html_injetado(self):
        self.assertIn('>3</span>',etapa_compra_html(3,"Liberar carga oficial"))
        self.assertNotIn("<script>",etapa_compra_html(1,"<script>"))

    def test_acoes_principais_separadas_dos_seis_downloads(self):
        tree = ast.parse(montar_fonte_atual())
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                             and n.func.id == "cabecalho_html" for n in ast.walk(tree)),1)
        grupos = [n for n in ast.walk(tree) if isinstance(n,ast.With) and
                  any(isinstance(i.context_expr,ast.Call) and i.context_expr.args and
                      isinstance(i.context_expr.args[0],ast.Constant) and
                      i.context_expr.args[0].value == "Exportar resultados do MRP" for i in n.items)]
        self.assertEqual(len(grupos),2)
        for grupo in grupos:
            self.assertEqual(sum(isinstance(n,ast.Attribute) and n.attr == "download_button"
                                 for n in ast.walk(grupo)),3)
            self.assertNotIn("ANÁLISE DE COMPRA",ast.unparse(grupo))
        botoes = [n for n in ast.walk(tree) if isinstance(n,ast.Call) and
                  isinstance(n.func,ast.Attribute) and n.func.attr == "button" and
                  n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value == "ANÁLISE DE COMPRA"]
        self.assertEqual(len(botoes),2)
        self.assertTrue(all(any(k.arg == "type" and k.value.value == "primary" for k in n.keywords)
                            for n in botoes))
