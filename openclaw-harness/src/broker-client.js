const { createHmac, randomBytes } = require('node:crypto');

function createBrokerClient({ baseUrl = process.env.WORKSPACE_BROKER_URL || 'http://workspace-broker:8010', secret = process.env.WORKSPACE_HMAC_SECRET || '', fetchImpl = fetch } = {}) {
  if (secret.length < 32) throw new Error('Strong workspace HMAC secret is required.');
  async function request(path, payload) {
    const body = JSON.stringify(payload);
    const timestamp = Math.floor(Date.now() / 1000);
    const nonce = randomBytes(16).toString('base64url');
    const signature = createHmac('sha256', secret).update(`POST\n${path}\n${timestamp}\n${nonce}\n${body}`).digest('hex');
    const response = await fetchImpl(`${baseUrl}${path}`, { method: 'POST', body, headers: { 'Content-Type': 'application/json', 'x-mnemcode-timestamp': String(timestamp), 'x-mnemcode-nonce': nonce, 'x-mnemcode-signature': signature } });
    if (!response.ok) throw new Error('The constrained workspace rejected the approval request.');
    return response.json();
  }
  return {
    prepare(workspaceId, payload) { return request(`/v1/workspaces/${encodeURIComponent(workspaceId)}/prepare-pr`, payload); },
    open(workspaceId, payload) { return request(`/v1/workspaces/${encodeURIComponent(workspaceId)}/open-pr`, payload); },
  };
}

module.exports = { createBrokerClient };
