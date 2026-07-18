import assert from 'node:assert/strict';
import { test } from 'node:test';
import clientModule from '../src/broker-client.js';

const { createBrokerClient } = clientModule;

test('broker client signs prepare and open requests without exposing its secret', async () => {
  const calls = [];
  const client = createBrokerClient({ baseUrl: 'http://broker:8010', secret: 's'.repeat(64), fetchImpl: async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({ ok: true }) };
  } });
  await client.prepare('ws_123', { runId: 'run_1', title: 'fix: bounded issue', body: 'Closes #11.' });
  await client.open('ws_123', { runId: 'run_1', title: 'fix: bounded issue', body: 'Closes #11.', token: 'approval', expiresAt: 123 });
  assert.equal(calls.length, 2);
  assert.match(calls[0].url, /prepare-pr$/);
  assert.ok(calls[0].options.headers['x-mnemcode-signature']);
  assert.doesNotMatch(JSON.stringify(calls), /s{32}/);
});
