import { randomUUID } from 'node:crypto';
import { execFile, spawn } from 'node:child_process';
import { readFile, realpath, rm } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { validatePatch } from '../../workspace-runner/patch-policy.js';

const execFileAsync = promisify(execFile);

function gitWithInput(cwd, args, input) {
  return new Promise((resolve, reject) => {
    const child = spawn('git', args, { cwd, shell: false, windowsHide: true });
    let stderr = '';
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.once('error', reject);
    child.once('close', code => code === 0 ? resolve() : reject(new Error(`Patch rejected: ${stderr}`)));
    child.stdin.end(input);
  });
}

export function createWorkspaceManager({ root, allowedRepository, clone, runnerImage = 'mnemagent-judge-runner:local' }) {
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
    async readFile(id, relativePath) {
      const session = sessions.get(id);
      if (!session) throw new Error('Workspace not found.');
      if (typeof relativePath !== 'string' || relativePath.includes('..') || path.isAbsolute(relativePath)) throw new Error('Workspace path is invalid.');
      const workspace = await realpath(session.path);
      const target = await realpath(path.join(workspace, relativePath));
      if (target !== workspace && !target.startsWith(`${workspace}${path.sep}`)) throw new Error('Workspace path escapes the repository.');
      return readFile(target, 'utf8');
    },
    async applyPatch(id, patchText) {
      const session = sessions.get(id);
      if (!session) throw new Error('Workspace not found.');
      const summary = validatePatch(patchText);
      await gitWithInput(session.path, ['apply', '--check', '--whitespace=error', '-'], patchText);
      await gitWithInput(session.path, ['apply', '--whitespace=error', '-'], patchText);
      return summary;
    },
    async diff(id) {
      const session = sessions.get(id);
      if (!session) throw new Error('Workspace not found.');
      const { stdout } = await execFileAsync('git', ['diff', '--no-ext-diff', '--', '.'], { cwd: session.path, maxBuffer: 600_000, windowsHide: true });
      return stdout;
    },
    async test(id, request = { commandId: 'test' }) {
      const session = sessions.get(id);
      if (!session) throw new Error('Workspace not found.');
      const args = ['run', '--rm', '-i', '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--memory', '768m', '--cpus', '0.75', '--pids-limit', '128', '--tmpfs', '/tmp:rw,noexec,nosuid,size=128m', '-e', 'WORKSPACE_ROOT=/workspace', '-v', `${session.path}:/workspace:rw`, runnerImage];
      return new Promise((resolve, reject) => {
        const child = spawn('docker', args, { shell: false, windowsHide: true });
        let stdout = ''; let stderr = '';
        child.stdout.on('data', chunk => { stdout += chunk; });
        child.stderr.on('data', chunk => { stderr += chunk; });
        child.once('error', reject);
        child.once('close', code => {
          try { resolve(JSON.parse(stdout.trim())); }
          catch { reject(new Error(`Runner failed (${code}): ${stderr.slice(0, 500)}`)); }
        });
        child.stdin.end(`${JSON.stringify(request)}\n`);
      });
    },
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
