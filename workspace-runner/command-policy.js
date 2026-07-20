export function validateCommand({ commandId, testNamePattern } = {}) {
  if (commandId === 'python-scoring-test' && testNamePattern === undefined) return { argv: ['python', '-m', 'pytest', '-q', 'tests/test_scoring.py'] };
  if (commandId === 'python-unit' && testNamePattern === undefined) return { argv: ['python', '-m', 'pytest', '-q'] };
  throw new Error('Command is not allowed in the judge workspace.');
}
