const PROTECTED = /^(\.git\/|\.github\/workflows\/|package(?:-lock)?\.json$|\.env(?:\.|$)|Dockerfile$)/;

export function validatePatch(patch = '') {
  if (typeof patch !== 'string' || patch.length > 120_000) throw new Error('Patch exceeds the judge workspace limit.');
  const files = [...patch.matchAll(/^\+\+\+ b\/(.+)$/gm)].map(match => match[1]);
  if (!files.length || files.length > 5 || new Set(files).size !== files.length) throw new Error('Patch must touch between one and five unique files.');
  for (const file of files) {
    if (file.includes('..') || file.startsWith('/') || PROTECTED.test(file) || !/^(?:src|include|test|tests|public|tools)\/[A-Za-z0-9_./-]+\.(?:js|mjs|cjs|cpp|cc|c|h|hpp|css|html|json)$/.test(file)) throw new Error(`Patch path is not allowed: ${file}`);
  }
  const changedLines = patch.split('\n').filter(line => /^[+-](?![+-])/.test(line)).length;
  if (changedLines > 500) throw new Error('Patch exceeds 500 changed lines.');
  return { files, changedLines };
}
