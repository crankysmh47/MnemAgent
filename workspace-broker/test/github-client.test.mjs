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

test('GitHub client can create a bounded audit issue', async () => {
  const calls = [];
  const client = createGitHubClient({ repository: 'owner/repo', token: 'token', fetchImpl: async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => ({ number: 9, html_url: 'https://github.test/issues/9' }) }; } });
  const issue = await client.createIssue({ title: 'Normalize terminal paths', body: 'Reproduction and acceptance criteria.' });
  assert.equal(JSON.parse(calls[0].options.body).title, 'Normalize terminal paths');
  assert.equal(issue.number, 9);
});
