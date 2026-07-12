import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createGitHubClient } from '../src/github-client.js';

test('GitHub client opens draft PRs only against the configured default branch', async () => {
  const calls = [];
  const client = createGitHubClient({ repository: 'owner/repo', token: 'token', fetchImpl: async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => ({ number: 7, html_url: 'https://github.test/pr/7' }) }; } });
  const pr = await client.openDraftPr({ head: 'mnemagent-judge/1/run', title: 'Fix issue', body: 'Tested', base: 'main' });
  const payload = JSON.parse(calls[0].options.body);
  assert.equal(payload.draft, true);
  assert.equal(payload.base, 'main');
  assert.equal(pr.number, 7);
  await assert.rejects(client.openDraftPr({ head: 'main', title: 'bad', body: 'bad', base: 'main' }), /branch/i);
});
