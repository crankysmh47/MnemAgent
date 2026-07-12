import { spawn } from 'node:child_process';
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
