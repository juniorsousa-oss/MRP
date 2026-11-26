"""Integra o snapshot publicado ao acesso inicial sem substituir o motor."""
INICIO_RAPIDO_PATCH = r"""
def _fast_replace(old, new):
    if _source.count(old) != 1:
        raise RuntimeError("Âncora da abertura rápida mudou: " + old[:85])
    return _source.replace(old, new, 1)

_source = _fast_replace(
    'def _logout():\n',
    'def _logout():\n    for name in tuple(st.session_state):\n'
    '        if name.startswith("_mrp_fast_"):\n            st.session_state.pop(name,None)\n')
_source = _fast_replace(
    'def render_consulta_view():',
    'def render_consulta_view(snapshot_inicial=None):')
_source = _fast_replace(
    '        snap = load_latest_snapshot()\n    except Exception as e:\n        st.error(f"Não foi possível carregar o MRP compartilhado:',
    '        snap = snapshot_inicial if snapshot_inicial is not None else load_latest_snapshot()\n'
    '    except Exception as e:\n        st.error(f"Não foi possível carregar o MRP compartilhado:')
_source = _fast_replace(
    '"select":"id,created_at,semana_mrp,usuario","order":"created_at.desc","limit":"1"',
    '"select":"id,created_at,semana_mrp,usuario,calculation_key","order":"created_at.desc,id.desc","limit":"1"')

_boot_a = _source.index('try:\n    _mrp_cached_bundle=st.session_state.get("_mrp_central_bundle")')
_boot_b = _source.index('_manual_store=',_boot_a)
from textwrap import indent as _fast_indent
_source = _source[:_boot_a]+'''
from mrp_inicio_rapido import daily_key as _fast_daily_key, update_needed as _fast_update_needed, snapshot_is_usable as _fast_snapshot_ok
_fast_snapshot = None
_fast_access = (st.session_state.get("auth_user_id"), _mrp_role)
if st.session_state.get("_mrp_fast_owner") != _fast_access:
    for _fast_k in ("_mrp_fast_snapshot","_mrp_fast_next_check","_mrp_fast_notice"):
        st.session_state.pop(_fast_k,None)
    st.session_state["_mrp_fast_owner"] = _fast_access

if (_mrp_page == "MRP ATUAL" and not st.session_state.get("_mrp_manual_active")
        and not st.session_state.get("_mrp_force_central_refresh")):
    # Mantém a versão já verificada por esta sessão mesmo se a rede oscilar.
    _fast_snapshot = st.session_state.get("_mrp_fast_snapshot")
    if not _fast_snapshot_ok(_fast_snapshot):
        try:
            _fast_candidate = load_latest_snapshot()
            if _fast_snapshot_ok(_fast_candidate):
                _fast_snapshot = _fast_candidate
                st.session_state["_mrp_fast_snapshot"] = _fast_candidate
        except Exception:
            _fast_snapshot = None
    if not _fast_snapshot_ok(_fast_snapshot):
        _fast_snapshot = None

if _fast_snapshot is None:
'''+_fast_indent(_source[_boot_a:_boot_b].rstrip(),'    ')+'''
else:
    # A data do cabeçalho é a do resultado exibido, nunca a de uma base nova.
    _central_bundle={}
    st.session_state.pop("_mrp_central_error",None)

'''+_source[_boot_b:]

_source = _fast_replace(
    'from mrp_interface_visual import WORKSPACE_CSS,cabecalho_html',
    '''if _fast_snapshot is not None:
    _mrp_status="MRP SALVO"
    _mrp_when=_central_mrp.format_dt(_fast_snapshot.get("created_at"))
    _mrp_sidebar_week=formatar_semana(_fast_snapshot.get("semana_mrp"))
    _mrp_base_ok=5
    _mrp_rows_text=f'{len(_fast_snapshot["demanda_projeto"]):,}'.replace(",", ".")+" registros"
    _mrp_alertas=[]

from mrp_interface_visual import WORKSPACE_CSS,cabecalho_html''')

_fast_monitor = r'''
if _fast_snapshot is not None:
    from time import monotonic as _fast_clock
    from mrp_inicio_rapido import SingleCalculation, calculate_validated

    @st.cache_resource
    def _fast_calculation_pool():
        return SingleCalculation()

    # O primeiro passe sempre desenha a tela. As próximas verificações são
    # isoladas em um fragmento; o download e o cálculo não usam a thread da UI.
    st.session_state.setdefault("_mrp_fast_next_check", _fast_clock()+4.0)
    @st.fragment(run_every="5s")
    def _fast_monitor_snapshot(snapshot):
        def _notice(kind, message):
            st.session_state["_mrp_fast_notice"]=(kind,message)
            getattr(st,kind)(message)
        if _fast_clock() < st.session_state.get("_mrp_fast_next_check",0.0):
            _message=st.session_state.get("_mrp_fast_notice")
            if _message:
                getattr(st,_message[0])(_message[1])
            return
        st.session_state["_mrp_fast_next_check"]=_fast_clock()+12.0
        try:
            _latest = load_latest_snapshot_meta()
            if _latest and _latest.get("id") != snapshot.get("id"):
                _candidate=load_snapshot(_latest["id"])
                if _fast_snapshot_ok(_candidate):
                    st.session_state["_mrp_fast_snapshot"]=_candidate
                    st.session_state.pop("_mrp_fast_notice",None)
                    st.rerun()
                _notice("warning","A nova versão não pôde ser aberta. O último MRP validado continua em exibição.")
                return
            if st.session_state.get("auth_role") != "ADMIN":
                return
            _state=_central_mrp.inspect_mrp_state()
            if not _state.get("ready"):
                _notice("warning","Bases em atualização ou incompletas. O último MRP validado continua em exibição.")
                return
            _day=pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%Y-%m-%d")
            _mrp_read_cache_this_run.clear()
            _tr_projects=_carregar_tratativas_salvas()
            _tr_products=_carregar_tratativas_produto_salvas()
            _refs=_central_mrp.make_refs(_state)
            # A chave histórica inclui a data em que o resultado foi salvo.
            # Compare pela data da versão exibida, senão a meia-noite pareceria
            # uma mudança das bases. Uma gravação nova usa o dia corrente.
            try:
                _saved_day=pd.to_datetime(snapshot.get("created_at"),utc=True).tz_convert(
                    "America/Sao_Paulo").strftime("%Y-%m-%d")
            except (ValueError,TypeError,AttributeError):
                _saved_day=_day
            _key_for_saved_day=_fast_daily_key(_refs,_tr_projects,_tr_products,_saved_day)
            if not _fast_update_needed(_state,snapshot.get("calculation_key"),_key_for_saved_day):
                _notice("caption","Consulta com o último MRP validado.")
                return
            _key=_fast_daily_key(_refs,_tr_projects,_tr_products,_day)
            _pool=_fast_calculation_pool()
            _work_key=(_state.get("signature"),_key)
            _future=_pool.request(_work_key,lambda: calculate_validated(
                _central_mrp.load_mrp_bundle,_mrp_load_sources_from_central,
                _state.get("signature"),_tr_projects,_tr_products))
            if _future is None or not _future.done():
                _notice("info","Atualizando o MRP. A versão validada continua disponível para consulta.")
                st.session_state["_mrp_fast_next_check"]=_fast_clock()+4.0
                return
            try:
                _result,_week=_future.result()
            except Exception:
                _pool.discard(_work_key)
                st.session_state["_mrp_fast_next_check"]=_fast_clock()+45.0
                raise
            if not _pool.publish_lock.acquire(blocking=False):
                _notice("info","Atualizando o MRP. A versão validada continua disponível para consulta.")
                st.session_state["_mrp_fast_next_check"]=_fast_clock()+4.0
                return
            try:
                # Reconfirma bases e tratativas antes de persistir. A leitura
                # deste fragmento não reutiliza as tabelas de outro rerun.
                _fresh=_central_mrp.inspect_mrp_state(force_check=True)
                _mrp_original_load_projects.clear()
                _mrp_original_load_products.clear()
                _mrp_read_cache_this_run.clear()
                _projects_now=_carregar_tratativas_salvas()
                _products_now=_carregar_tratativas_produto_salvas()
                _today_now=pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%Y-%m-%d")
                if (not _fresh.get("ready")
                        or _fast_daily_key(_central_mrp.make_refs(_fresh),_projects_now,_products_now,_today_now)!=_key):
                    _pool.discard(_work_key)
                    _notice("warning","As bases ou tratativas mudaram durante a atualização. Mantendo a versão validada.")
                    return
                if _fresh.get("output_stale"):
                    _central_mrp.publish_relatorio_mrp_if_changed(
                        _result["demanda_projeto"],_fresh.get("dependency_versions") or {},
                        _fresh.get("output_meta") or {})
                if not _mrp_lookup_saved_calculation(_key):
                    save_snapshot(_week,usuario_mrp,_result["macro"],_result["proj"],
                                  _result["demanda_projeto"],_result["compras_mrp"],
                                  _result["cp"],_result["fab_det"],calculation_key=_key)
                _pool.discard(_work_key)
                load_latest_snapshot_meta.clear()
                _next=load_latest_snapshot()
                if _fast_snapshot_ok(_next) and _next.get("id")!=snapshot.get("id"):
                    st.session_state["_mrp_fast_snapshot"]=_next
                    st.session_state.pop("_mrp_fast_notice",None)
                    st.rerun()
                _notice("caption","Consulta com o último MRP validado.")
            finally:
                _pool.publish_lock.release()
        except Exception:
            import logging as _fast_logging
            _fast_logging.getLogger(__name__).exception("Falha na atualização assíncrona do MRP.")
            st.session_state["_mrp_fast_next_check"]=_fast_clock()+45.0
            _notice("warning","Não foi possível atualizar agora. O último MRP validado continua em exibição.")

    _fast_notice_slot=st.container(key="mrp_inicio_rapido_estado")
    render_consulta_view(snapshot_inicial=_fast_snapshot)
    with _fast_notice_slot:
        _fast_monitor_snapshot(_fast_snapshot)
    st.stop()

'''
_source = _fast_replace(
    'if not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):',
    _fast_monitor+'if not all([cadastro_file,estoque_file,geral_file,compras_file,mt_file]):')
"""
