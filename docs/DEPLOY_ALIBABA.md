# Deploy on Alibaba Cloud

The submission topology is one Alibaba Cloud ECS spot instance running Docker Compose. The live deployment uses Singapore (`ap-southeast-1`), which avoids mainland China ICP filing requirements for this public demonstration.

Devpost's live schedule is:

- Submission deadline: July 20, 2026 at 5:00 PM EDT
- Judging: July 28 through August 11, 2026
- Winners announced: August 17, 2026

Keep the instance available through August 11 and release it after final evidence is archived.

## 1. Instance

- Ubuntu 24.04+ LTS, x86-64
- Minimum 2 vCPU / 4 GiB; 4 vCPU / 8 GiB is more comfortable for native test suites
- 40 GB ESSD entry disk
- Inbound TCP 22 only from the owner's IP; TCP 80/443 from the internet
- No public 3000, 8000, 8001, 8010, 5432, or 18789 rules
- Pay-as-you-go spot strategy with a cost ceiling and interruption monitoring

The submission uses `sslip.io` for automatic DNS: `47-237-140-12.sslip.io` resolves to the current public IP. A normal A record works as well.

## 2. Runtime

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
newgrp docker
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
git switch MnemCode
```

## 3. Secrets

```bash
cp .env.cloud.example .env.cloud
openssl rand -hex 32  # repeat for session/HMAC/approval secrets
chmod 600 .env.cloud
getent group docker | cut -d: -f3  # use as DOCKER_GID
```

Replace every placeholder. Use a fine-grained GitHub token restricted to the demo repository with Contents, Issues, and Pull Requests read/write. The public sponsored path uses the official DeepSeek endpoint. For the Qwen path, copy values from `config/qwen-cloud.example.env` and supply a DashScope key through the environment.

Never commit `.env.cloud` or paste secrets into screenshots, logs, issues, or the Devpost description.

## 4. Deploy and verify

```bash
./scripts/deploy-cloud.sh
./scripts/verify-cloud.sh
```

The deployment script validates Compose, builds the pinned no-network runner, starts the stack, and waits for service health. Caddy obtains and renews TLS automatically.

The verification script checks:

- public HTTPS health;
- all Compose services;
- OpenClaw availability;
- MCP and workspace broker health;
- anonymous archive isolation;
- signed judge login and the 30/5/5 allowance;
- populated MnemCode UI.

## 5. Seven-day judge sessions

The signed cookie and server allowance expire after seven days. Remaining quotas are atomically stored in the `mnemagent-judge-session-state` Docker volume. A harness restart therefore neither logs out an active judge nor refreshes their sponsored quota. Extending time does not change the 30 chat, five coding, five publication, 12-session, or provider-token ceilings.

## 6. Spot protection and cost

Install `scripts/spot-interruption-watch.sh` as a systemd service. It watches the ECS metadata interruption signal, blocks new coding runs, and snapshots Postgres before termination. Configure OSS only when off-instance backups are required.

- One 2 vCPU / 4 GiB spot instance is sufficient for the bounded demo.
- Configure Alibaba budget alerts at $10, $20, and $30.
- Keep a separate provider-side model budget.
- Release the ECS instance after judging ends on August 11.

## 7. Submission proof

Devpost requires both:

1. A repository code link containing an accepted Qwen Cloud base URL.
2. A screenshot of the running Alibaba Cloud resource from Workbench.

Both are collected in [CLOUD_PROOF.md](CLOUD_PROOF.md). Do not replace the Workbench screenshot with a locally generated image or terminal-only output.
