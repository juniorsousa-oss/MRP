(() => {
  if (window.__mrpTabTransitionV1) return;
  window.__mrpTabTransitionV1 = true;
  const html = document.documentElement;
  const mainSelector = '[data-testid="stMainBlockContainer"]';
  const navSelector = '[class*="st-key-mrp_nav_btn_"]';
  const kpiSelector = '[class*="st-key-mrp_operacao_kpis_"]';
  const header = () => document.querySelector('.mrp-v2-header[data-mrp-route]');
  const scriptState = () => document.querySelector('[data-testid="stApp"]')?.getAttribute('data-test-script-state');
  let stable = header()?.dataset.mrpRoute ?? null;
  let pending = null;
  let frame = 0;
  const maxMaskMs = 12_000;

  const finish = (route) => {
    stable = route;
    pending = null;
    delete html.dataset.mrpNavigating;
  };
  const begin = (route) => {
    if (pending?.target === route) return;
    pending = {target: route, since: performance.now(), seenRun: false};
    html.dataset.mrpNavigating = 'true';
    tick();
  };
  const boundary = (heading) => {
    const main = heading.closest(mainSelector);
    let marker = heading.closest('[data-testid="stElementContainer"]');
    if (!main || !marker) return;
    while (marker.parentElement?.matches('[data-testid="stLayoutWrapper"]')) {
      marker = marker.parentElement;
    }
    if (!marker.hasAttribute('data-mrp-tab-boundary')) {
      marker.setAttribute('data-mrp-tab-boundary', '');
    }
  };
  const tick = () => {
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      const heading = header();
      if (!heading) {
        if (pending) finish(null); // logout ou tela no lugar do workspace
        stable = null;
        return;
      }
      boundary(heading);
      const route = heading.dataset.mrpRoute;
      const appState = scriptState();
      const running = ['running', 'rerunRequested', 'stopRequested'].includes(appState);
      const stale = !!heading.closest(mainSelector)?.querySelector('[data-stale="true"]');
      if (stable === null) stable = route;
      // Atende também navegação programática, fora do clique no menu.
      if (!pending && stable !== route && (running || stale)) begin(route);
      if (!pending) {
        stable = route;
        return;
      }
      if (running || stale) pending.seenRun = true;
      const elapsed = performance.now() - pending.since;
      if (elapsed >= maxMaskMs || appState === 'compilationError' || (!running && !stale &&
          ((route === pending.target && (pending.seenRun || route !== stable)) ||
           (elapsed > 1500 && !pending.seenRun) ||
           (elapsed > 2500 && pending.seenRun && route !== pending.target)))) {
        finish(route);
        return;
      }
      tick();
    });
  };
  document.addEventListener('click', (event) => {
    const button = event.target instanceof Element ? event.target.closest('button') : null;
    const heading = header();
    if (!button || button.disabled || !heading) return;
    boundary(heading); // mascara o painel antes do próximo frame
    const item = button.closest(navSelector);
    if (item) {
      const match = String(item.className).match(/(?:^|\s)st-key-mrp_nav_btn_(\d+)(?=\s|$)/);
      if (match && (pending || heading.dataset.mrpRoute !== match[1])) begin(match[1]);
    } else if (heading.dataset.mrpRoute === '0' && button.closest(kpiSelector)) {
      begin('1');
    }
  }, true);
  const root = document.getElementById('root');
  if (root) new MutationObserver(tick).observe(root, {
    childList: true, subtree: true, attributes: true,
    attributeFilter: ['data-test-script-state', 'data-stale', 'data-mrp-route'],
  });
  tick();
})();
