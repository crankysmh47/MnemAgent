export async function requestJson(path, { signal } = {}) {
  const response = await fetch(path, { signal });
  const data = await response.json();
  if (!response.ok) throw new Error(data?.error || `Request failed with HTTP ${response.status}`);
  return data;
}

export async function resolveUserId(locationSearch = '', storage) {
  const query = new URLSearchParams(locationSearch).get('user')?.trim();
  if (query) return query;
  const storedValue = storage?.getItem?.('mnemos_user_id');
  const stored = typeof storedValue === 'string' ? storedValue.trim() : '';
  if (stored) return stored;
  for (const path of ['/api/user/whoami', '/api/setup/default-user-id']) {
    try {
      const data = await requestJson(path);
      if (typeof data?.user_id === 'string' && data.user_id.trim()) return data.user_id.trim();
    } catch { /* try next identity source */ }
  }
  return '';
}

export async function loadArchiveSnapshot(userId, { since, signal } = {}) {
  const encoded = encodeURIComponent(userId);
  const eventsQuery = since == null ? '' : `?since=${encodeURIComponent(since)}`;
  const entries = [
    ['graph', `/api/graph/${encoded}`],
    ['metrics', `/api/metrics/${encoded}`],
    ['events', `/api/events/${encoded}${eventsQuery}`],
  ];
  const settled = await Promise.allSettled(entries.map(([, path]) => requestJson(path, { signal })));
  const snapshot = { graph: null, metrics: null, events: null, failures: {}, status: 'ok' };
  settled.forEach((result, index) => {
    const key = entries[index][0];
    if (result.status === 'fulfilled') snapshot[key] = result.value;
    else snapshot.failures[key] = result.reason?.message || 'Request failed';
  });
  const failed = Object.keys(snapshot.failures);
  snapshot.status = snapshot.failures.graph ? 'error' : failed.length ? 'degraded' : 'ok';
  return snapshot;
}
