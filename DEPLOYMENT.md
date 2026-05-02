# BharatDoc Production Deployment Guide

This guide details how to deploy BharatDoc to a production environment using Docker Compose. The architecture includes Caddy (auto-HTTPS + proxy), a Vite/Nginx frontend, a Gunicorn/Uvicorn FastAPI backend, Celery workers, Postgres with pgvector, and Redis.

## Prerequisites

- **VM Specs**: Minimum 4GB RAM, 2 vCPUs, 40GB Disk (Ubuntu 22.04 LTS recommended). If using the local LLM (`USE_LLM=true`), at least 16GB RAM or a dedicated GPU is required.
- **Software**: Docker and Docker Compose v2 installed.
- **DNS**: An A record pointing your domain (e.g., `bharatdoc.company.com`) to the VM's public IP address.

---

## 1. Initial Setup

1. **Clone the repository** to your production server:
   ```bash
   git clone https://github.com/Inayat-0007/BharatDoc.git
   cd BharatDoc
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.production.example .env
   ```
   Open `.env` in your editor and update:
   - `DOMAIN_NAME`: Must match your DNS record exactly for auto-HTTPS.
   - `SECRET_KEY`: Run `openssl rand -hex 32` to generate a strong key.
   - `ALLOWED_ORIGINS` / `ALLOWED_HOSTS`: Update to match your domain.
   - `POSTGRES_PASSWORD`: Generate a strong password.

---

## 2. Deployment

Start the stack in detached mode:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Verification
- Wait 1-2 minutes for Caddy to provision the SSL certificate.
- Navigate to `https://<YOUR_DOMAIN>` in your browser.
- Check logs if the site doesn't load:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f caddy
  ```

---

## 3. Backups

The database and uploaded files reside in Docker volumes. You must back them up regularly.

### Database Backup (pg_dump)
```bash
docker exec -t bharatdoc-db-1 pg_dumpall -c -U bharatdoc_user > dump_$(date +%Y-%m-%d).sql
```

### Database Restore
```bash
cat dump_recent.sql | docker exec -i bharatdoc-db-1 psql -U bharatdoc_user -d bharatdoc_prod
```

### Volumes Backup
Volumes to back up: `pg_data` and `caddy_data` (contains SSL certificates to prevent rate-limiting from Let's Encrypt).

---

## 4. Updates & Rollbacks

### Updating to a new version
```bash
# Pull latest code
git pull origin main

# Rebuild and restart containers (zero-downtime for unchanged containers)
docker compose -f docker-compose.prod.yml up -d --build
```

### Rollback
If a deployment fails, revert to the previous Git commit and rebuild:
```bash
git checkout <previous_commit_hash>
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 5. Security Notes

- **Firewall**: Ensure only ports `80` (HTTP), `443` (HTTPS), and `22` (SSH) are open to the public. All internal communication (Postgres, Redis, API) is isolated within the Docker network.
- **Audit Logs**: Sensitive actions (login, register, upload, query, delete) are logged to the `[AUDIT]` stream in the backend container logs.
- **Rate Limiting**: Configured in `backend/security.py`. Edit the `RATE_LIMITS` dictionary if the defaults are too strict for your use case.

---

## 6. CI/CD Pipeline (GitHub Actions)

The project includes two GitHub Actions workflows:
1. **Continuous Integration (`ci.yml`)**: Runs on every push/PR to `main`. It builds the frontend, tests the backend Docker image build, and runs a localized smoke test using Docker Compose to ensure the stack boots correctly.
2. **Continuous Deployment (`deploy.yml`)**: Runs manually (`workflow_dispatch`) or on version tags (e.g., `v1.0.0`). It connects to your production server via SSH, pulls the latest code, rebuilds containers, and performs an automated health check. If the health check fails, it automatically initiates a rollback to the previous commit.

### Required GitHub Secrets for Deployment

To enable automated deployments, navigate to your repository's **Settings > Secrets and variables > Actions** and add the following repository secrets:

- `SERVER_HOST`: The IP address or domain of your production VM (e.g., `192.168.1.100`).
- `SERVER_USER`: The SSH username (e.g., `ubuntu` or `root`).
- `SSH_PRIVATE_KEY`: Your private SSH key (e.g., contents of `~/.ssh/id_rsa`). Ensure the public key is added to the server's `~/.ssh/authorized_keys`.
- `SERVER_PORT`: (Optional) The SSH port, defaults to `22` if not provided.

*Note: You must run the Initial Setup (Section 1) manually on the server at least once to clone the repository and create the `.env` file before the deployment pipeline can work.*
