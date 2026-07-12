import { execFile } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { chmod, mkdir, rm, writeFile } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { promisify } from 'node:util';
import { createGitHubClient } from './github-client.js';
import { createApproval, verifyApproval } from './approval.js';
import { verifyHmacRequest } from './hmac.js';
import { loadConfig } from './config.js';
import { createWorkspaceManager } from './workspace-manager.js';

const execFileAsync = promisify(execFile);
const config = loadConfig();
const github = createGitHubClient({ repository: config.repository, token: config.githubToken });
const nonces = new Set();
const testEvidence = new Map();

const hash = value => createHash('sha256').update(value).digest('hex');

async function cloneRepository(repository, target, branch) {
  await mkdir(config.root, { recursive: true });
  const isWindows = process.platform === 'win32';
  const helper = path.join(config.root, `askpass-${randomBytes(8).toString('hex')}${isWindows ? '.cmd' : '.sh'}`);
  await writeFile(helper, isWindows ? `@echo off\necho ${config.githubToken}\n` : `#!/bin/sh\nprintf '%s' '${config.githubToken}'\n`, { mode: 0o700 });
  if (!isWindows) await chmod(helper, 0o700);
  try {
    await execFileAsync('git', ['clone', '--depth', '1', '--branch', 'main', `https://github.com/${repository}.git`, target], {
      env: { PATH: process.env.PATH, GIT_ASKPASS: helper, GIT_TERMINAL_PROMPT: '0', GIT_USERNAME: 'x-access-token' },
      windowsHide: true,
    });
    await execFileAsync('git', ['checkout', '-b', branch], { cwd: target, windowsHide: true });
    await execFileAsync('git', ['config', '--unset-all', 'credential.helper'], { cwd: target, windowsHide: true }).catch(() => {});
  } finally { await rm(helper, { force: true }); }
}

async function withAskPass(callback) {
  const isWindows = process.platform === 'win32';
  const helper = path.join(config.root, `askpass-${randomBytes(8).toString('hex')}${isWindows ? '.cmd' : '.sh'}`);
  await writeFile(helper, isWindows ? `@echo off\necho ${config.githubToken}\n` : `#!/bin/sh\nprintf '%s' '${config.githubToken}'\n`, { mode: 0o700 });
  if (!isWindows) await chmod(helper, 0o700);
  try { return await callback({ PATH: process.env.PATH, GIT_ASKPASS: helper, GIT_TERMINAL_PROMPT: '0', GIT_USERNAME: 'x-access-token' }); }
  finally { await rm(helper, { force: true }); }
}

const manager = createWorkspaceManager({ root: config.root, allowedRepository: config.repository, clone: cloneRepository, runnerImage: config.runnerImage });

function send(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body), 'Cache-Control': 'no-store' });
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') return send(res, 200, { status: 'ok' });
  let body = '';
  for await (const chunk of req) { body += chunk; if (body.length > 128_000) return send(res, 413, { error: 'Request too large.' }); }
  try {
    verifyHmacRequest({ method: req.method, path: req.url, body, headers: req.headers, secret: config.hmacSecret, nonces });
    const input = body ? JSON.parse(body) : {};
    if (req.method === 'GET' && req.url === '/v1/issues') return send(res, 200, { issues: await github.listIssues() });
    if (req.method === 'POST' && req.url === '/v1/workspaces') return send(res, 201, await manager.create(input));
    const fileMatch = /^\/v1\/workspaces\/([^/]+)\/files\?path=(.+)$/.exec(req.url);
    if (req.method === 'GET' && fileMatch) return send(res, 200, { content: await manager.readFile(fileMatch[1], decodeURIComponent(fileMatch[2])) });
    const actionMatch = /^\/v1\/workspaces\/([^/]+)\/(patch|test|diff)$/.exec(req.url);
    if (actionMatch && req.method === 'POST' && actionMatch[2] === 'patch') return send(res, 200, await manager.applyPatch(actionMatch[1], input.patch));
    if (actionMatch && req.method === 'POST' && actionMatch[2] === 'test') {
      const result = await manager.test(actionMatch[1], input);
      testEvidence.set(actionMatch[1], result.exitCode === 0);
      return send(res, 200, result);
    }
    if (actionMatch && req.method === 'POST' && actionMatch[2] === 'diff') return send(res, 200, { diff: await manager.diff(actionMatch[1]) });
    const prepareMatch = /^\/v1\/workspaces\/([^/]+)\/prepare-pr$/.exec(req.url);
    if (req.method === 'POST' && prepareMatch) {
      if (!testEvidence.get(prepareMatch[1])) throw new Error('Passing test evidence is required.');
      const diff = await manager.diff(prepareMatch[1]);
      if (!diff.trim()) throw new Error('A non-empty diff is required.');
      const diffHash = hash(diff);
      const metadataHash = hash(JSON.stringify({ title: input.title, body: input.body, base: 'main' }));
      return send(res, 200, { diff, diffHash, metadataHash, ...createApproval({ runId: input.runId, diffHash, metadataHash, secret: config.approvalSecret }) });
    }
    const openMatch = /^\/v1\/workspaces\/([^/]+)\/open-pr$/.exec(req.url);
    if (req.method === 'POST' && openMatch) {
      const session = manager.get(openMatch[1]);
      if (!session || !testEvidence.get(openMatch[1])) throw new Error('Workspace is not ready for a PR.');
      const diffHash = hash(await manager.diff(openMatch[1]));
      const metadataHash = hash(JSON.stringify({ title: input.title, body: input.body, base: 'main' }));
      verifyApproval({ token: input.token, expiresAt: input.expiresAt, runId: input.runId, diffHash, metadataHash, secret: config.approvalSecret });
      await execFileAsync('git', ['config', 'user.name', 'crankysmh47'], { cwd: session.path });
      await execFileAsync('git', ['config', 'user.email', 'annankhan741@gmail.com'], { cwd: session.path });
      await execFileAsync('git', ['add', '--', '.'], { cwd: session.path });
      await execFileAsync('git', ['commit', '-m', input.title], { cwd: session.path });
      await withAskPass(env => execFileAsync('git', ['push', '--set-upstream', 'origin', session.branch], { cwd: session.path, env, windowsHide: true }));
      const pr = await github.openDraftPr({ head: session.branch, title: input.title, body: input.body, base: 'main' });
      return send(res, 201, { number: pr.number, url: pr.html_url, draft: true });
    }
    const cleanupMatch = /^\/v1\/workspaces\/([^/]+)\/cleanup$/.exec(req.url);
    if (req.method === 'POST' && cleanupMatch) return send(res, 200, { cleaned: await manager.cleanup(cleanupMatch[1]) });
    return send(res, 404, { error: 'Broker route not found.' });
  } catch (error) {
    return send(res, /signature|replay/i.test(error.message) ? 401 : 400, { error: 'Workspace request rejected.' });
  }
});

server.listen(config.port, '127.0.0.1', () => console.log(`MnemCode workspace broker listening on 127.0.0.1:${config.port}`));
