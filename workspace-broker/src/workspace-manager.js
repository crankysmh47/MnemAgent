import { randomUUID } from 'node:crypto';
import { rm } from 'node:fs/promises';
import path from 'node:path';

export function createWorkspaceManager({ root, allowedRepository, clone }) {
  const sessions = new Map();
  let activeId = null;
  return {
    async create({ repository, issueNumber }) {
      if (repository !== allowedRepository) throw new Error('Repository is not on the allowlist.');
      if (!Number.isInteger(Number(issueNumber)) || Number(issueNumber) < 1) throw new Error('Issue number is invalid.');
      if (activeId) throw new Error('An active workspace already exists.');
      const id = `ws_${randomUUID()}`;
      const target = path.resolve(root, id);
      const branch = `mnemagent-judge/${Number(issueNumber)}/${id.slice(3, 11)}`;
      await clone(repository, target, branch);
      const session = { id, repository, issueNumber: Number(issueNumber), branch, path: target, createdAt: new Date().toISOString() };
      sessions.set(id, session);
      activeId = id;
      return { ...session, path: undefined };
    },
    get(id) { return sessions.get(id) || null; },
    async cleanup(id) {
      const session = sessions.get(id);
      if (!session) return false;
      await rm(session.path, { recursive: true, force: true });
      sessions.delete(id);
      if (activeId === id) activeId = null;
      return true;
    },
  };
}
