# Security model

MnemCode is a hackathon demonstration with a deliberately narrow trust boundary. It is not a general multi-tenant cloud IDE.

## Public and judge identity

- Anonymous visitors may read only the seeded `demo-brain` archive.
- Interactive routes require a signed HttpOnly, SameSite=Strict cookie and same-origin CSRF token.
- Judge cookies and server-side allowance expire after seven days.
- Five failed access attempts lock the source IP for 30 minutes.
- The server persists random session IDs, random namespaces, expiry, quota, and in-flight counters—never the access code or cookie signature.
- Atomic volume-backed writes preserve spent quota across restarts. Interrupted reservations are refunded because their run state did not complete.

## Agent boundary

OpenClaw is denied host exec, process, read, write, edit, patch, browser, and generic web tools. It receives only filtered MnemAgent memory tools and structured MnemCode repository tools.

Broker requests include HMAC signatures over method, path, timestamp, nonce, and body. Replayed requests and timestamps older than 60 seconds fail.

## Patch and test policy

- Allowlisted file extensions and paths
- Maximum five files, 500 changed lines, and 120 KB request body
- Fixed test-command IDs mapped to exact argv arrays
- No evaluated shell strings
- One active coding run per judge session
- Draft PR only; no direct push to `main`
- Approval bound to run ID, diff hash, metadata hash, and five-minute expiry

## Runner isolation

The runner uses:

- non-root UID;
- read-only root filesystem;
- dropped Linux capabilities;
- `no-new-privileges`;
- no network;
- bounded `nosuid` temporary filesystem;
- 768 MB RAM, 0.75 CPU, and 128 PID limits;
- one mounted repository workspace.

The temporary filesystem permits execution because native tests compile temporary binaries.

## Credential custody

The browser and runner never receive provider or GitHub credentials. The private broker alone receives a fine-grained GitHub token restricted to the demo repository. The Docker socket is mounted only into the broker; broker compromise should therefore be treated as host compromise.

Use environment variables or Alibaba secret storage. Never commit `.env`, `.env.cloud`, API keys, GitHub tokens, judge codes, session secrets, HMAC secrets, or approval secrets.

## Production path

A production rollout should replace the shared judge code with user identity, per-organization authorization, per-user provider/GitHub OAuth, auditable key rotation, managed runner isolation, and a durable database-backed job queue. Those controls are intentionally not misrepresented as complete in this hackathon build.

Report vulnerabilities privately to the repository owner before opening a public issue.
