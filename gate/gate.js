(function(){
  const statusSummary = document.getElementById('status-summary');
  const cycle = document.getElementById('cycle');
  const ready = document.getElementById('ready');
  const lastUpdated = document.getElementById('last_updated');
  const commits = document.getElementById('commits');
  const sysPhase = document.getElementById('system_phase');
  const govMode = document.getElementById('governance_mode');
  const autonomy = document.getElementById('autonomy_enabled');
  const uptime = document.getElementById('uptime_cycles');
  const lastCycleSummary = document.getElementById('last_cycle_summary');
  const governanceVersion = document.getElementById('governance_version');
  const bannerEl = document.getElementById('gate-banner');

  function showClosed() {
    statusSummary.textContent = 'Gate Closed';
    statusSummary.className = 'closed';
    cycle.textContent = '—';
    ready.textContent = '—';
    lastUpdated.textContent = '—';
    commits.innerHTML = '';
    sysPhase.textContent = '—';
    govMode.textContent = '—';
    autonomy.textContent = '—';
    uptime.textContent = '—';
    lastCycleSummary.textContent = '—';
    governanceVersion.textContent = '—';
    if (bannerEl) { bannerEl.textContent = '—'; bannerEl.className = 'banner'; }
  }

  function render(state) {
    statusSummary.textContent = state.ready ? 'Gate Open' : 'Gate Closed';
    statusSummary.className = state.ready ? 'open' : 'closed';
    cycle.textContent = state.cycle ?? '—';
    ready.textContent = state.ready ? 'Yes' : 'No';
    const ts = state.last_updated_ts ? new Date(state.last_updated_ts * 1000) : null;
    lastUpdated.textContent = ts ? ts.toISOString() : '—';
    sysPhase.textContent = state.system_phase ?? '—';
    govMode.textContent = state.governance_mode ?? '—';
    autonomy.textContent = typeof state.autonomy_enabled === 'boolean' ? (state.autonomy_enabled ? 'Yes' : 'No') : '—';
    uptime.textContent = (typeof state.uptime_cycles === 'number') ? state.uptime_cycles : '—';
    lastCycleSummary.textContent = state.last_cycle_summary ?? '—';
    governanceVersion.textContent = state.governance_version ?? '—';
    // Determine a human-friendly banner and class
    if (bannerEl) {
      let text = 'Arkadia';
      let cls = 'banner';
      if (state.governance_mode === 'manual') {
        text = 'Arkadia is Paused';
        cls = 'banner paused';
      } else if (state.governance_mode === 'autonomous') {
        text = 'Arkadia is Autonomous';
        cls = 'banner autonomous';
      } else if (state.governance_mode === 'scheduled') {
        text = 'Arkadia is Scheduled';
        cls = 'banner scheduled';
      } else {
        switch ((state.system_phase || '').toLowerCase()) {
          case 'foundation':
            text = 'Arkadia — Foundation';
            cls = 'banner foundation';
            break;
          case 'stabilization':
            text = 'Arkadia is Stable';
            cls = 'banner stable';
            break;
          case 'expansion':
            text = 'Arkadia is Evolving';
            cls = 'banner evolving';
            break;
          default:
            text = 'Arkadia — Unknown State';
            cls = 'banner';
        }
      }
      bannerEl.textContent = text;
      bannerEl.className = cls;
    }
    commits.innerHTML = '';
    if (Array.isArray(state.commits)) {
      state.commits.slice(0,5).forEach(c => {
        const li = document.createElement('li');
        li.textContent = c;
        commits.appendChild(li);
      });
    }
  }

  // The gate is read-only and must not trigger recursion. It will only fetch a file
  // from the same origin and will not write or call any APIs.

  fetch('/sanctum/status.json', {cache: 'no-store'})
    .then(r => {
      if (!r.ok) throw new Error('Missing status');
      return r.json();
    })
    .then(json => {
      // sanitize: expect simple object with cycle, ready, commits, metrics and ts
      if (!json || typeof json !== 'object' || !('cycle' in json)) throw new Error('Invalid status');
      render(json);
    })
    .catch(e => {
      console.warn('Gate fetch failed', e);
      showClosed();
    });
})();
