import hashlib
import json
import unittest
from threading import Event
from unittest.mock import patch

import pandas as pd

from central_mrp_data import make_refs
from mrp_engine_extract import montar_fonte_atual
from mrp_inicio_rapido import SingleCalculation, calculate_validated, daily_key, snapshot_is_usable, update_needed


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.projects = pd.DataFrame([{"Projeto":"A","OBS":"Normal"}])
        self.products = pd.DataFrame([{"Projeto":"A","Produto":"00000042","OBS":"Normal"}])
        self.day = "2026-11-26"

    def key(self, sig="v1", project=None, product=None):
        return daily_key(make_refs({"signature":sig}), self.projects if project is None else project,
                         self.products if product is None else product, self.day)

    def test_matches_legacy_confirmed_snapshot_key(self):
        refs = make_refs({"signature":"v1"})
        enc = lambda d: json.dumps(d,ensure_ascii=False,sort_keys=True).encode("utf-8")
        legacy = hashlib.sha256(b"MRP-SNAPSHOT-V9-COMPRA-TCTP-GRUPO-OP-OBS"
            + b"".join(x.getvalue() for x in refs)
            + enc(self.projects[["Projeto","OBS"]].sort_values("Projeto").to_dict("records"))
            + enc(self.products[["Projeto","Produto","OBS"]].sort_values(["Projeto","Produto"]).to_dict("records"))).hexdigest()
        self.assertEqual(self.key(),hashlib.sha256(f"MRP-DIARIO|{self.day}|{legacy}".encode()).hexdigest())

    def test_inputs_and_treatments_both_invalidate(self):
        key = self.key()
        state = {"ready":True,"output_stale":False}
        self.assertFalse(update_needed(state,key,key))
        self.assertTrue(update_needed(state,key,self.key(sig="v2")))
        self.assertTrue(update_needed(state,key,self.key(project=self.projects.assign(OBS="Resíduo"))))
        self.assertTrue(update_needed(state,key,self.key(product=self.products.assign(OBS="Resíduo"))))
        self.assertFalse(update_needed(state,key,self.key(project=self.projects.assign(**{"Atualizado em":"10:30"}))))
        self.assertTrue(update_needed({**state,"output_stale":True},key,key))
        self.assertFalse(update_needed({"ready":False,"output_stale":True},key,self.key(sig="v2")))

    def test_accept_only_nonempty_snapshot(self):
        self.assertFalse(snapshot_is_usable({"id":1,"mrp_geral":[{}]}))
        self.assertFalse(snapshot_is_usable({"id":1,"mrp_geral":[],"demanda_projeto":[{}]}))
        self.assertTrue(snapshot_is_usable({"id":1,"mrp_geral":[{}],"demanda_projeto":[{}]}))

    def test_worker_is_single_and_original_view_need_not_wait(self):
        pool, release, started = SingleCalculation(), Event(), Event()
        def slow():
            started.set()
            release.wait(2)
            return 99
        try:
            work = pool.request("V1",slow)
            self.assertTrue(started.wait(1))
            self.assertFalse(work.done())
            self.assertIs(pool.request("V1",lambda: 1),work)
            self.assertIsNone(pool.request("V2",lambda: 2))
            release.set()
            self.assertEqual(work.result(1),99)
            self.assertEqual(pool.request("V2",lambda: 2).result(1),2)
        finally:
            release.set()
            pool._pool.shutdown(wait=True)

    def test_changed_during_download_is_not_calculated(self):
        for bundle in ({"ready":False},{"ready":True,"signature":"v2"}):
            with self.assertRaisesRegex(ValueError,"mudaram"):
                calculate_validated(lambda:bundle,lambda *_:self.fail("unexpected prepare"),"v1",self.projects,self.products)

    def test_invalid_results_are_rejected_before_publication(self):
        material = pd.DataFrame([{"Código":42,"Descrição":"Material"}])
        result = {"macro":material,"demanda_projeto":material,
                  "compras_mrp":pd.DataFrame([{"produto":"00000099"}])}
        with patch("mrp_engine_headless.calcular_mrp",return_value=(result,202648)):
            with self.assertRaisesRegex(ValueError,"obrigatória"):
                calculate_validated(lambda:{"ready":True,"signature":"v1"},lambda *_:(material,),
                                    "v1",self.projects,self.products)

    def test_composed_runtime_preserves_admin_gate_and_snapshot_render(self):
        src = montar_fonte_atual()
        compile(src,"runtime","exec")
        monitor = src[src.index('def _fast_monitor_snapshot(snapshot):'):src.index('    _fast_monitor_snapshot(_fast_snapshot)')]
        self.assertLess(monitor.index('!= "ADMIN"'),monitor.index('_central_mrp.inspect_mrp_state()'))
        self.assertLess(monitor.index('_today_now'),monitor.index('save_snapshot('))
        self.assertIn('render_consulta_view(snapshot_inicial=_fast_snapshot)',src)
        self.assertIn('st.session_state.get("_mrp_manual_active")',src)
