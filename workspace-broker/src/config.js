import path from 'node:path';

export function loadConfig(env = process.env) {
  const config = {
    repository: String(env.JUDGE_DEMO_REPOSITORY || ''),
    githubToken: String(env.JUDGE_GITHUB_TOKEN || ''),
    hmacSecret: String(env.WORKSPACE_HMAC_SECRET || ''),
    approvalSecret: String(env.WORKSPACE_APPROVAL_SECRET || env.WORKSPACE_HMAC_SECRET || ''),
    root: path.resolve(env.WORKSPACE_ROOT || './.judge-workspaces'),
    runnerImage: String(env.JUDGE_RUNNER_IMAGE || 'mnemagent-judge-runner:local'),
    port: Number(env.WORKSPACE_BROKER_PORT || 8010),
  };
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(config.repository)) throw new Error('JUDGE_DEMO_REPOSITORY must use owner/repository format.');
  if (config.githubToken.length < 20) throw new Error('JUDGE_GITHUB_TOKEN is required.');
  if (config.hmacSecret.length < 32 || config.approvalSecret.length < 32) throw new Error('Strong workspace secrets are required.');
  if (!Number.isInteger(config.port) || config.port < 1024 || config.port > 65535) throw new Error('Workspace broker port is invalid.');
  return config;
}
