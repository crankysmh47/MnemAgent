const SAFE_JS_PATH = /^(?:src|test)\/[A-Za-z0-9_.-]{1,80}\.js$/;

export function validateCommand({ commandId, testNamePattern } = {}) {
  if (commandId === 'test' && testNamePattern === undefined) return { argv: ['npm', 'test'] };
  if (commandId === 'test-unit' && testNamePattern === undefined) return { argv: ['npm', 'run', 'test:unit'] };
  if (commandId === 'validate-fs' && testNamePattern === undefined) return { argv: ['npm', 'run', 'validate:fs'] };
  if (commandId === 'test-integration' && testNamePattern === undefined) return { argv: ['npm', 'run', 'test:integration'] };
  if (commandId === 'node-check' && SAFE_JS_PATH.test(testNamePattern || '')) {
    return { argv: ['node', '--check', testNamePattern] };
  }
  throw new Error('Command is not allowed in the judge workspace.');
}
