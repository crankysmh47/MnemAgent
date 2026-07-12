let csrf = '';

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (options.method && options.method !== 'GET') headers['X-CSRF-Token'] = csrf;
  const response = await fetch(path, { credentials: 'same-origin', ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'The judge service is unavailable.');
  return data;
}

export const judgeApi = {
  scenarios: () => request('/api/judge/scenarios'),
  login: async accessCode => { const data = await request('/judge/session', { method: 'POST', body: JSON.stringify({ accessCode }), headers: { 'X-CSRF-Token': '' } }); csrf = data.csrf; return data; },
  start: payload => request('/api/judge/runs', { method: 'POST', body: JSON.stringify(payload) }),
  run: id => request(`/api/judge/runs/${encodeURIComponent(id)}`),
};
