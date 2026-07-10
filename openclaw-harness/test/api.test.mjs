import test from 'node:test';
import assert from 'node:assert/strict';

const load = () => import(`../src/public/scripts/api.js?${Date.now()}`);
const response = (body, ok = true, status = 200) => ({ ok, status, async json() { return body; } });

test('requestJson encodes paths and reports API error payloads', async () => {
  const calls = [];
  globalThis.fetch = async (url) => { calls.push(url); return response({ error: 'bad news' }, false, 503); };
  const { requestJson } = await load();
  await assert.rejects(requestJson('/api/graph/a/b'), /bad news/);
  assert.equal(calls[0], '/api/graph/a/b');
});

test('resolveUserId prioritizes query, storage, whoami, then setup', async () => {
  globalThis.fetch = async (url) => response(url.includes('whoami') ? { user_id: 'who' } : { user_id: 'setup' });
  const { resolveUserId } = await load();
  assert.equal(await resolveUserId('?user=query%20id', { getItem: () => 'stored' }), 'query id');
  assert.equal(await resolveUserId('', { getItem: () => 'stored' }), 'stored');
  assert.equal(await resolveUserId('', { getItem: () => '' }), 'who');
  globalThis.fetch = async () => response({}, false, 503);
  assert.equal(await resolveUserId('', { getItem: () => '' }), '');
});

test('loadArchiveSnapshot encodes user and since, recovering partial failures', async () => {
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(url);
    if (url.includes('/metrics/')) return response({ error: 'metrics unavailable' }, false, 500);
    if (url.includes('/events/')) return response({ events: [] });
    return response({ beliefs: [], edges: [] });
  };
  const { loadArchiveSnapshot } = await load();
  const snapshot = await loadArchiveSnapshot('a/b', { since: '2026-01-01T00:00:00Z' });
  assert.equal(snapshot.status, 'degraded');
  assert.deepEqual(snapshot.failures, { metrics: 'metrics unavailable' });
  assert.ok(calls.some((url) => url.includes('/api/graph/a%2Fb')));
  assert.ok(calls.some((url) => url.includes('since=2026-01-01T00%3A00%3A00Z')));
});

test('loadArchiveSnapshot reports error when graph fails', async () => {
  globalThis.fetch = async (url) => response({ error: `${url.includes('graph') ? 'graph down' : 'other down'}` }, false, 500);
  const { loadArchiveSnapshot } = await load();
  const snapshot = await loadArchiveSnapshot('u');
  assert.equal(snapshot.status, 'error');
  assert.equal(snapshot.failures.graph, 'graph down');
  assert.equal(snapshot.failures.metrics, 'other down');
  assert.equal(snapshot.failures.events, 'other down');
});
