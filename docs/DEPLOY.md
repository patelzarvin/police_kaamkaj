# Deployment Guide — police_kaamkaj

Repository: https://github.com/patelzarvin/police_kaamkaj

## How auto-deploy works

1. Team member pushes code to `main` on GitHub
2. GitHub Actions runs `.github/workflows/deploy.yml`
3. Server pulls latest code and runs `docker compose up -d --build`
4. Website updates in ~3–5 minutes

## One-time server setup (VPS)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
git clone https://github.com/patelzarvin/police_kaamkaj.git /opt/sentinel
cd /opt/sentinel
cp .env.example .env
# Edit .env for production secrets

# First deploy
docker compose up -d --build
```

Open: `http://YOUR_SERVER_IP:3000`

## GitHub Secrets (Settings → Secrets → Actions)

| Secret | Example |
|--------|---------|
| `VPS_HOST` | `123.45.67.89` |
| `VPS_USER` | `root` |
| `VPS_SSH_KEY` | Private SSH key (full PEM) |
| `VPS_PORT` | `22` (optional) |
| `DEPLOY_PATH` | `/opt/sentinel` (optional) |

## Team workflow

```bash
git pull origin main
# make changes
git add .
git commit -m "describe change"
git push origin main
# → live site updates automatically
```

## Production speed settings (.env on server)

```env
MAX_CONCURRENT_STREAMS=4
YOLO_ENABLE_TILING=false
PIPELINE_STARTUP_DELAY_SEC=5
ENABLE_LIVE_PIPELINE=true
```

For demo-only (fastest UI): `ENABLE_LIVE_PIPELINE=false`

## HTTPS (recommended)

Point domain DNS to server IP, use Cloudflare free SSL in front of port 3000.
