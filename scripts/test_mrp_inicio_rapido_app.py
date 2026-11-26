"""Smoke da abertura rápida sobre o runtime montado, sem acesso externo ou escrita real."""
import time
from unittest.mock import patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from mrp_engine_extract import montar_fonte_atual
from mrp_inicio_rapido import daily_key
from central_mrp_data import make_refs

projects=pd.DataFrame(columns=["Projeto","OBS"])
products=pd.DataFrame(columns=["Projeto","Produto","OBS"])
day=pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%Y-%m-%d")
key=daily_key(make_refs({"signature":"v1"}),projects,products,day)
src="_header_css = \"<style>body{}</style>\"\n"+montar_fonte_atual()
src = "def _limpar_filtros_mrp(*keys):\n    for key in keys: st.session_state.pop(key,None)\n" + src
src=src.replace('if not _require_login(PUBLIC_LOGIN_CONFIG):','if not st.session_state.get("auth_role"):',1)
src=src.replace('_mrp_use_manual=False\n_central_bundle={}', """
def _fake_lookups(key):
    return [{"id":2}] if st.session_state.get("fixture_saved") else []
def _fake_save(*args, calculation_key=None):
    st.session_state["fixture_saved"] = calculation_key
    st.session_state["fixture_writes"] = st.session_state.get("fixture_writes",0)+1
def _fake_meta():
    if st.session_state.get("fixture_saved"):
        return {"id":2}
    return {"id":1}
_fake_meta.clear=lambda:None
def _fake_snapshot(n):
    return {"id":n,"created_at":pd.Timestamp.now(tz="America/Sao_Paulo").isoformat(),"semana_mrp":202648,
      "calculation_key":st.session_state.get("fixture_saved") if n==2 else st.session_state["fixture_original"],
      "mrp_geral":[{"Código":42,"Descrição":"Material sintético","Tipo":"MP","Demanda":n,"Saldo em Estoque":1,"P.C.":1,"S.C.":0,"Produzindo":1,"DIV":-1,"Status":"OK","Semana de Atendimento":202648}],
      "demanda_projeto":[{"Projeto":"A","Produto":42,"Descrição":"Material sintético","Semana de Necessidade":202648,"Semana de Atendimento":202648,"Necessidade":1}],
      "fabricacao":[], "compras":[], "compra_mrp":[], "projecao_semanal":[]}
def _fake_latest():
    return _fake_snapshot(_fake_meta()["id"])
load_latest_snapshot_meta=_fake_meta
load_latest_snapshot=_fake_latest
load_snapshot=_fake_snapshot
save_snapshot=_fake_save
_mrp_lookup_saved_calculation=_fake_lookups
def _fixture_projects():
    obs=st.session_state.get("fixture_obs","")
    return pd.DataFrame([{"Projeto":"TEST","OBS":obs}]) if obs else pd.DataFrame(columns=["Projeto","OBS"])
def _fixture_products():
    return pd.DataFrame(columns=["Projeto","Produto","OBS"])
_carregar_tratativas_salvas=_fixture_projects
_carregar_tratativas_produto_salvas=_fixture_products
class _FixtureClear:
    def clear(self): pass
_mrp_original_load_projects=_mrp_original_load_products=_FixtureClear()
_mrp_use_manual=False
_central_bundle={}""",1)

def state(force_check=False):
    return {"ready":runner.session_state["fixture_ready"],"signature":"v1","output_stale":False}

def calc(*args):
    time.sleep(0.35)
    return {f:pd.DataFrame() for f in ("macro","proj","demanda_projeto","compras_mrp","cp","fab_det")},202648

for role in ("ADMIN","CONSULTA","OPERADOR"):
    runner=AppTest.from_string(src,default_timeout=12)
    runner.session_state["auth_role"]=role
    runner.session_state["auth_user_id"]="test-fixture"
    runner.session_state["fixture_original"]=key
    runner.session_state["fixture_ready"]=True
    with patch('mrp_operacao_ui.operacao_grade',return_value=None),patch('requests.get',side_effect=RuntimeError('offline fixture')),patch('central_mrp_data.load_visual_config',return_value={}),patch("central_mrp_data.favicon_bytes",return_value=b""),patch("central_mrp_data.inspect_mrp_state",side_effect=state) as probe,patch('central_mrp_data.load_mrp_bundle',side_effect=AssertionError("initial request tried to download")) as download,patch('mrp_inicio_rapido.calculate_validated',side_effect=calc) as worker:
        runner.run()
        assert not runner.exception, runner.exception
        assert any(b.label == "Buscar" for b in runner.button),runner.button
        assert not probe.called and not download.called
        runner.session_state["_mrp_fast_next_check"]=0
        runner.run()
        assert not runner.exception, runner.exception
        assert not worker.called
        assert bool(probe.called)==(role=="ADMIN")
        if role=="ADMIN":
            runner.session_state["fixture_ready"]=False
            runner.session_state["_mrp_fast_next_check"]=0
            runner.run()
            assert any("incompletas" in x.value for x in runner.warning) and not worker.called
            runner.session_state["fixture_ready"]=True
            runner.session_state["fixture_obs"]="resíduo"
            runner.session_state["_mrp_fast_next_check"]=0
            runner.run()
            assert any("Atualizando" in x.value for x in runner.info)
            assert any(b.label=="Buscar" for b in runner.button)
            for _ in range(10):
                time.sleep(0.14)
                runner.session_state["_mrp_fast_next_check"]=0
                runner.run()
                if runner.session_state["_mrp_fast_snapshot"]["id"]==2:
                    break
            assert not runner.exception, runner.exception
            assert runner.session_state["_mrp_fast_snapshot"]["id"]==2
            assert runner.session_state["fixture_writes"]==1
    print(role,"interface disponível, mudança/falha validadas" if role=="ADMIN" else "consulta sem escrita")
