const PREPARED_ISSUES = new Set([1, 2, 3]);

export function validateJudgeRun({ issueNumber, message } = {}) {
  const parsedIssue = Number(issueNumber);
  const text = String(message || '').trim();
  if (!PREPARED_ISSUES.has(parsedIssue)) throw new Error('Choose a prepared issue.');
  if (!text || text.length > 2_000) throw new Error('Judge messages must contain at most 2,000 characters.');
  return { issueNumber: parsedIssue, message: text };
}

export function canOpenDraftPr({ testsPassed, approval, diffHash } = {}) {
  return Boolean(testsPassed && approval?.valid === true && typeof diffHash === 'string' && diffHash.length >= 3);
}
