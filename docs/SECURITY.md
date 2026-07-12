# Security

## Trust boundaries

- Public users can read only `demo-brain`.
- Interactive routes require a signed HttpOnly, SameSite=Strict judge cookie and same-origin CSRF token.
- Five failed access attempts lock the source IP for 30 minutes.
- OpenClaw denies host exec, process, read, write, edit, patch, browser, and generic web tools.
- Broker requests use HMAC timestamp, nonce, and body signatures. Replays and requests older than 60 seconds fail.
- The broker alone receives the fine-grained GitHub token. The runner has no token and no network.
- Patch paths, extensions, file count, changed lines, and body size use allowlists.
- Tests are exact argv arrays. No shell string is evaluated.
- Draft PR approval binds run ID, diff hash, and metadata hash for five minutes.

## Runner posture

The runner uses a non-root UID, read-only root filesystem, dropped Linux capabilities, `no-new-privileges`, no network, a bounded `nosuid` tmpfs, 768 MB RAM, 0.75 CPU, and 128 PIDs. The tmpfs permits execution because native test suites compile temporary binaries. Only one repository workspace is mounted.

The Docker socket is available only to the broker. Treat broker compromise as host compromise; keep it loopback/internal, patch the host, and use a dedicated ECS instance with no unrelated workloads.

## Secrets

Use environment variables or Alibaba secret storage. Never commit `.env.cloud`, provider keys, GitHub tokens, session secrets, or workspace HMAC secrets. The GitHub token should be fine-grained, limited to the single demo repository, with Issues and Pull Requests read/write plus Contents read/write.

Report vulnerabilities privately to the repository owner before opening a public issue.
