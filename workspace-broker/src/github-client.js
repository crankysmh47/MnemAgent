export function createGitHubClient({ repository, token, fetchImpl = fetch }) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) throw new Error('GitHub repository is invalid.');
  if (!token) throw new Error('GitHub token is required.');
  const request = async (path, options = {}) => {
    const response = await fetchImpl(`https://api.github.com/repos/${repository}${path}`, {
      ...options,
      headers: { Accept: 'application/vnd.github+json', Authorization: `Bearer ${token}`, 'X-GitHub-Api-Version': '2022-11-28', ...(options.headers || {}) },
    });
    if (!response.ok) throw new Error('GitHub operation failed.');
    return response.json();
  };
  return {
    issue(number) { if (!Number.isInteger(Number(number)) || Number(number) < 1) throw new Error('Issue number is invalid.'); return request(`/issues/${Number(number)}`); },
    listIssues() { return request('/issues?state=open&per_page=20'); },
    createIssue({ title, body }) {
      if (!String(title).trim() || String(title).length > 120 || !String(body).trim() || String(body).length > 20_000) throw new Error('Issue metadata is invalid.');
      return request('/issues', { method: 'POST', body: JSON.stringify({ title, body }) });
    },
    async openDraftPr({ head, title, body, base = 'main' }) {
      if (!String(head).startsWith('mnemagent-judge/') || head === base) throw new Error('Draft PR branch is invalid.');
      if (!String(title).trim() || String(title).length > 120 || String(body).length > 20_000) throw new Error('Draft PR metadata is invalid.');
      return request('/pulls', { method: 'POST', body: JSON.stringify({ head, base, title, body, draft: true }) });
    },
  };
}
