import { createHmac, randomBytes } from 'node:crypto';
import readline from 'node:readline';
import { projectBrokerEvent } from './broker-events.js';

const base = process.env.WORKSPACE_BROKER_URL || 'http://127.0.0.1:8010';
const secret = process.env.WORKSPACE_HMAC_SECRET || '';
const runId = process.env.MNEMCODE_RUN_ID || '';
const eventUrl = process.env.MNEMCODE_EVENT_URL || 'http://127.0.0.1:3000/api/judge/internal/events';

async function emitEvidence(event) {
  if (!runId || !event) return;
  const body = JSON.stringify({ runId, ...event, timestamp: new Date().toISOString() });
  const timestamp = Math.floor(Date.now() / 1000);
  const nonce = randomBytes(16).toString('base64url');
  const pathname = new URL(eventUrl).pathname;
  const signature = createHmac('sha256', secret).update(`POST\n${pathname}\n${timestamp}\n${nonce}\n${body}`).digest('hex');
  await fetch(eventUrl, { method: 'POST', body, headers: { 'Content-Type': 'application/json', 'x-mnemcode-timestamp': String(timestamp), 'x-mnemcode-nonce': nonce, 'x-mnemcode-signature': signature } }).catch(() => {});
}

async function broker(path, method = 'POST', payload = {}) {
  const body = method === 'GET' ? '' : JSON.stringify(payload);
  const timestamp = Math.floor(Date.now() / 1000);
  const nonce = randomBytes(16).toString('base64url');
  const signature = createHmac('sha256', secret).update(`${method}\n${path}\n${timestamp}\n${nonce}\n${body}`).digest('hex');
  const response = await fetch(`${base}${path}`, { method, body: body || undefined, headers: { 'Content-Type': 'application/json', 'x-mnemcode-timestamp': String(timestamp), 'x-mnemcode-nonce': nonce, 'x-mnemcode-signature': signature } });
  if (!response.ok) throw new Error('The constrained workspace rejected this operation.');
  return response.json();
}

const tools = [
  ['list_issues', 'List open issues in the single allowlisted repository', {}],
  ['create_issue', 'Create one bounded issue selected during the audit', { title: { type: 'string' }, body: { type: 'string' } }],
  ['create_workspace', 'Create the only isolated judge workspace', { repository: { type: 'string' }, issueNumber: { type: 'integer' } }],
  ['read_workspace_file', 'Read one regular file inside the active workspace', { workspaceId: { type: 'string' }, path: { type: 'string' } }],
  ['list_workspace_files', 'List bounded regular-file paths in the active workspace', { workspaceId: { type: 'string' } }],
  ['apply_workspace_patch', 'Validate and apply a bounded unified patch', { workspaceId: { type: 'string' }, patch: { type: 'string' } }],
  ['replace_workspace_text', 'Replace one exact, unique, bounded source fragment', { workspaceId: { type: 'string' }, path: { type: 'string' }, oldText: { type: 'string' }, newText: { type: 'string' } }],
  ['run_workspace_tests', 'Run one fixed no-network test command', { workspaceId: { type: 'string' }, commandId: { type: 'string', enum: ['python-scoring-test','python-unit'] } }],
  ['show_workspace_diff', 'Show the current bounded workspace diff', { workspaceId: { type: 'string' } }],
  ['cleanup_workspace', 'Delete the active workspace', { workspaceId: { type: 'string' } }],
].map(([name, description, properties]) => ({ name, description, inputSchema: { type: 'object', properties, additionalProperties: false } }));

async function call(name, args) {
  let result;
  if (name === 'list_issues') result = await broker('/v1/issues', 'GET');
  else if (name === 'create_issue') result = await broker('/v1/issues', 'POST', args);
  else if (name === 'create_workspace') result = await broker('/v1/workspaces', 'POST', args);
  else {
  const id = encodeURIComponent(args.workspaceId || '');
  if (name === 'read_workspace_file') result = await broker(`/v1/workspaces/${id}/files?path=${encodeURIComponent(args.path)}`, 'GET');
  else if (name === 'list_workspace_files') result = await broker(`/v1/workspaces/${id}/files`, 'GET');
  else if (name === 'apply_workspace_patch') result = await broker(`/v1/workspaces/${id}/patch`, 'POST', { patch: args.patch });
  else if (name === 'replace_workspace_text') result = await broker(`/v1/workspaces/${id}/replace`, 'POST', { path: args.path, oldText: args.oldText, newText: args.newText });
  else if (name === 'run_workspace_tests') result = await broker(`/v1/workspaces/${id}/test`, 'POST', { commandId: args.commandId });
  else if (name === 'show_workspace_diff') result = await broker(`/v1/workspaces/${id}/diff`, 'POST');
  else if (name === 'cleanup_workspace') result = await broker(`/v1/workspaces/${id}/cleanup`, 'POST');
  else throw new Error('Unknown MnemCode tool.');
  }
  await emitEvidence(projectBrokerEvent(name, args, result));
  return result;
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', async line => {
  let requestId = null;
  try {
    const message = JSON.parse(line);
    requestId = message.id ?? null;
    let result;
    if (message.method === 'initialize') result = { protocolVersion: '2025-06-18', capabilities: { tools: {} }, serverInfo: { name: 'mnemcode', version: '1.0.0' } };
    else if (message.method === 'tools/list') result = { tools };
    else if (message.method === 'tools/call') result = { content: [{ type: 'text', text: JSON.stringify(await call(message.params.name, message.params.arguments || {})) }] };
    else if (message.id === undefined) return;
    else throw new Error('Unsupported MCP method.');
    process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: message.id, result })}\n`);
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: requestId, error: { code: -32000, message: error.message } })}\n`);
  }
});
