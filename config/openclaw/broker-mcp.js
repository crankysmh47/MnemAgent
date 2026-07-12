import { createHmac, randomBytes } from 'node:crypto';
import readline from 'node:readline';

const base = process.env.WORKSPACE_BROKER_URL || 'http://127.0.0.1:8010';
const secret = process.env.WORKSPACE_HMAC_SECRET || '';

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
  ['create_workspace', 'Create the only isolated judge workspace', { repository: { type: 'string' }, issueNumber: { type: 'integer' } }],
  ['read_workspace_file', 'Read one regular file inside the active workspace', { workspaceId: { type: 'string' }, path: { type: 'string' } }],
  ['apply_workspace_patch', 'Validate and apply a bounded unified patch', { workspaceId: { type: 'string' }, patch: { type: 'string' } }],
  ['run_workspace_tests', 'Run one fixed no-network test command', { workspaceId: { type: 'string' }, commandId: { type: 'string', enum: ['test','test-unit','validate-fs','test-integration'] } }],
  ['show_workspace_diff', 'Show the current bounded workspace diff', { workspaceId: { type: 'string' } }],
  ['cleanup_workspace', 'Delete the active workspace', { workspaceId: { type: 'string' } }],
].map(([name, description, properties]) => ({ name, description, inputSchema: { type: 'object', properties, additionalProperties: false } }));

async function call(name, args) {
  if (name === 'list_issues') return broker('/v1/issues', 'GET');
  if (name === 'create_workspace') return broker('/v1/workspaces', 'POST', args);
  const id = encodeURIComponent(args.workspaceId || '');
  if (name === 'read_workspace_file') return broker(`/v1/workspaces/${id}/files?path=${encodeURIComponent(args.path)}`, 'GET');
  if (name === 'apply_workspace_patch') return broker(`/v1/workspaces/${id}/patch`, 'POST', { patch: args.patch });
  if (name === 'run_workspace_tests') return broker(`/v1/workspaces/${id}/test`, 'POST', { commandId: args.commandId });
  if (name === 'show_workspace_diff') return broker(`/v1/workspaces/${id}/diff`, 'POST');
  if (name === 'cleanup_workspace') return broker(`/v1/workspaces/${id}/cleanup`, 'POST');
  throw new Error('Unknown MnemCode tool.');
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', async line => {
  try {
    const message = JSON.parse(line);
    let result;
    if (message.method === 'initialize') result = { protocolVersion: '2025-06-18', capabilities: { tools: {} }, serverInfo: { name: 'mnemcode', version: '1.0.0' } };
    else if (message.method === 'tools/list') result = { tools };
    else if (message.method === 'tools/call') result = { content: [{ type: 'text', text: JSON.stringify(await call(message.params.name, message.params.arguments || {})) }] };
    else if (message.id === undefined) return;
    else throw new Error('Unsupported MCP method.');
    process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: message.id, result })}\n`);
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32000, message: error.message } })}\n`);
  }
});
