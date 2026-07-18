import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateCommand } from './command-policy.js';

export async function runAllowedCommand(request, { cwd, timeoutMs = 120_000 } = {}) {
  const { argv } = validateCommand(request);
  return await new Promise((resolve) => {
    const child = spawn(argv[0], argv.slice(1), { cwd, shell: false, env: { PATH: process.env.PATH, HOME: '/tmp' } });
    let output = '';
    const append = chunk => { if (output.length < 262_144) output += chunk.toString(); };
    child.stdout.on('data', append); child.stderr.on('data', append);
    const timer = setTimeout(() => child.kill('SIGKILL'), timeoutMs);
    child.once('close', code => { clearTimeout(timer); resolve({ exitCode: code ?? 1, output }); });
  });
}

async function runCli() {
  let input = '';
  process.stdin.setEncoding('utf8');
  for await (const chunk of process.stdin) input += chunk;
  try {
    const request = JSON.parse(input.trim());
    const result = await runAllowedCommand(request, { cwd: process.env.WORKSPACE_ROOT || process.cwd() });
    process.stdout.write(`${JSON.stringify({ ok: result.exitCode === 0, ...result })}\n`);
    process.exitCode = result.exitCode === 0 ? 0 : 1;
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ ok: false, error: error.message })}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  await runCli();
}
