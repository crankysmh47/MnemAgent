# Deploy on Alibaba Cloud

Use one Hong Kong ECS spot instance for the judging window. Mainland instances can require ICP filing for public web access; Hong Kong avoids that deployment dependency. A 2 vCPU / 4 GB instance is the minimum, and 4 vCPU / 8 GB is more comfortable during C++ tests.

## 1. Create the instance

- Ubuntu 24.04 LTS, x86_64
- ESSD entry disk, 40 GB
- Security group inbound: TCP 22 from your IP, TCP 80 and 443 from anywhere
- No public 3000, 8000, 8001, 8010, 5432, or 18789 rules
- Spot maximum price capped to the amount you are willing to spend; enable automatic release only after August 13

Point an A record such as `memory.example.com` to the ECS public IP.

## 2. Install the runtime

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
newgrp docker
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
git switch MnemCode
```

## 3. Configure secrets

```bash
cp .env.cloud.example .env.cloud
openssl rand -hex 32  # repeat for each session/HMAC secret
stat -c '%a %n' .env.cloud
chmod 600 .env.cloud
getent group docker | cut -d: -f3  # use this as DOCKER_GID
```

Create a fine-grained GitHub token for the single demo repository. Grant Contents, Issues, and Pull requests read/write. Set `DEEPSEEK_API_KEY` for the official `https://api.deepseek.com` endpoint. The judge stack does not use the Qwen/DashScope key or offer an OpenRouter key option. Replace every placeholder in `.env.cloud`.

## 4. Deploy

```bash
./scripts/deploy-cloud.sh
./scripts/verify-cloud.sh
```

The deploy script builds the pinned runner first, validates Compose, starts the stack, and waits for health. Caddy obtains TLS automatically after DNS resolves.

## 5. Spot protection

Install `scripts/spot-interruption-watch.sh` as a systemd service. It checks the ECS metadata interruption signal, writes a run-block flag, backs up Postgres, and stops new judge runs before termination. Configure OSS credentials only if you want off-instance snapshots.

## 6. Cost control

- Keep one instance for the full judging window instead of crossing a monthly subscription boundary.
- Set Alibaba budget alerts at $10, $20, and $30.
- MnemCode admits at most 12 sponsored sessions per process and switches coding runs to replay after 2,000,000 measured model tokens. Set a separate $5 provider-side balance limit because token prices are controlled by the model provider.
- Stop the stack and release the ECS instance after judging on August 13.
