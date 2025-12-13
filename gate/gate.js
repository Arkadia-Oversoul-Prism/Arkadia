(function(){
  const statusSummary = document.getElementById('status-summary');
  const cycle = document.getElementById('cycle');
  const ready = document.getElementById('ready');
  const lastUpdated = document.getElementById('last_updated');
  const commits = document.getElementById('commits');

  function showClosed() {
    statusSummary.textContent = 'Gate Closed';
    statusSummary.className = 'closed';
    cycle.textContent = '—';
    ready.textContent = '—';
    lastUpdated.textContent = '—';
    commits.innerHTML = '';
  }

  function render(state) {
    statusSummary.textContent = state.ready ? 'Gate Open' : 'Gate Closed';
    statusSummary.className = state.ready ? 'open' : 'closed';
    cycle.textContent = state.cycle ?? '—';
    ready.textContent = state.ready ? 'Yes' : 'No';
    const ts = state.last_updated_ts ? new Date(state.last_updated_ts * 1000) : null;
    lastUpdated.textContent = ts ? ts.toISOString() : '—';
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
