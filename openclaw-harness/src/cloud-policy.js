const DEMO_USER_ID = "demo-brain";

function canReadArchive(userId, judgeUserId, sessionUserId) {
  const candidate = String(userId || "").trim();
  return candidate === DEMO_USER_ID
    || Boolean(judgeUserId && candidate === judgeUserId)
    || Boolean(sessionUserId && candidate === sessionUserId);
}

function canMutateThroughHarness(method, cloudMode) {
  return !cloudMode || !["POST", "PUT", "PATCH", "DELETE"].includes(String(method).toUpperCase());
}

function archiveQueryString(query = {}, { privateJudge = false, repository = "" } = {}) {
  const params = new URLSearchParams(query);
  if (privateJudge && repository) {
    if (!params.has("scope_type")) params.set("scope_type", "repository");
    if (!params.has("scope_id")) params.set("scope_id", repository);
    if (!params.has("include_core")) params.set("include_core", "true");
  }
  return params.toString();
}

module.exports = { canReadArchive, canMutateThroughHarness, archiveQueryString };
