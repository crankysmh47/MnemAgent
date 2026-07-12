const SAFE_PATTERN = /^[A-Za-z0-9_.-]{1,80}$/;

export function validateCommand({ commandId, testNamePattern } = {}) {
  if (commandId === 'test' && testNamePattern === undefined) return { argv: ['npm', 'test'] };
  if (commandId === 'node-check' && SAFE_PATTERN.test(testNamePattern || '') && testNamePattern.endsWith('.js')) {
    return { argv: ['node', '--check', testNamePattern] };
  }
  throw new Error('Command is not allowed in the judge workspace.');
}
