export async function requestJson(path, { signal } = {}) {
  const response = await fetch(path, { signal });
  const data = await response.json();
  if (!response.ok) throw new Error(data?.error || `Request failed with HTTP ${response.status}`);
  return data;
}

export async function resolveUserId(locationSearch = '', storage) {
  const query = new URLSearchParams(locationSearch).get('user')?.trim();
  if (query) return query;
  return 'demo-brain';
}

export function graphPath(userId, { query = '', limit, focusId } = {}) {
  const params = new URLSearchParams();
  if (query.trim()) params.set('q', query.trim());
  if (limit != null) params.set('limit', String(limit));
  if (focusId != null) params.set('focus_id', String(focusId));
  const suffix = params.size ? `?${params}` : '';
  return `/api/graph/${encodeURIComponent(userId)}${suffix}`;
}

export async function loadArchiveSnapshot(userId, { since, signal, query = '', limit, focusId } = {}) {
  const encoded = encodeURIComponent(userId);
  const eventsQuery = since == null ? '' : `?since=${encodeURIComponent(since)}`;
  const entries = [
    ['graph', graphPath(userId, { query, limit, focusId })],
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
