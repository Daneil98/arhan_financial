# Deploying Arhan Financial Platform on Railway

The repo is now Railway-ready. Railway does **not** read `docker-compose.yml` or
`render.yaml`, so you create **one Railway service per folder** (all from this
same repo) plus RabbitMQ. Databases are **sqlite per service** (demo mode) —
no Postgres needed.

## 1. Architecture on Railway (12 services, zero Postgres)

| # | Railway service | Root Directory | Type | Healthcheck |
|---|---|---|---|---|
| 1 | `identity` | `arhan_financial` | web (Dockerfile + `./start.sh`) | `/health/` |
| 2 | `identity-worker` | `arhan_financial` | worker, start: `celery -A arhan_financial worker -l info` | none |
| 3 | `account` | `account_services` | web | `/health/` |
| 4 | `account-worker` | `account_services` | worker, start: `celery -A account_services worker -Q account_service.internal,celery -l info` | none |
| 5 | `payments` | `payments` | web | `/health/` |
| 6 | `payments-worker` | `payments` | worker, start: `celery -A payments worker -Q payment.internal,celery -l info` | none |
| 7 | `ledger` | `ledger_service` | web | `/health/` |
| 8 | `ledger-worker` | `ledger_service` | worker, start: `celery -A ledger_service worker -Q ledger.internal,celery -l info` | none |
| 9 | `frontend` | `frontend_service` | web, **public domain ON** | `/health/` |
| 10 | `fraud` | `fraud_service` | web (FastAPI, `$PORT`-aware) | `/` |
| 11 | `gateway` (optional) | `gateway` | web, **public domain ON** | `/health/` |
| 12 | RabbitMQ x1 | — | Railway RabbitMQ template / plugin | — |

Each folder already contains a `railway.toml` with build + healthcheck config.
For workers, create the service from the same Root Directory, then override
**Settings → Deploy → Start Command** with the worker command above and
**disable the healthcheck**.

## 2. Step-by-step setup

1. **New Railway project** → `New → GitHub Repo` → select this repo.
2. **Add RabbitMQ first:**
   - `New → Database → RabbitMQ` (or deploy the official RabbitMQ template).
     Note its connection URL variable (e.g. `RABBITMQ_URL`).
   - No Postgres — each Django service uses its own sqlite file (demo mode).
3. **Create the 11 app services:** for each, `New → GitHub Repo → same repo`,
   then set **Settings → General → Root Directory** to the folder in the table.
   Railway auto-detects the `Dockerfile` + `railway.toml`.
4. **Attach a Volume to each sqlite service** (identity, account, payments,
   ledger, frontend — webs AND their workers share one volume each, or give
   each web+worker pair the same volume):
   - Service → `Volumes → New Volume`, mount path `/data`.
   - Set env `SQLITE_DIR=/data` on that service (the `.sqlite3` filename is
     fixed per service, so they won't clash as long as each service has its
     own volume — do NOT share one volume across different services).
   - Without a volume, sqlite still works but **resets on every redeploy**.
5. **Public networking:** enable `Settings → Networking → Generate Domain`
   **only** for `frontend` (and `gateway` if you use it). Keep all other
   services private — they talk over Railway's private network.
6. **Private networking:** enable private networking on the project so services
   can reach each other as `<service>.railway.internal:<port>`.

## 3. Environment variables

### 3.1 Shared (set on ALL 5 Django webs + ALL 4 workers)

```bash
DEBUG=False
SECRET_KEY=<generate: openssl rand -hex 32>
# Use ONE value everywhere (accepts either name — both are read):
JWT_SHARED_SECRET=<generate: openssl rand -hex 32>
# Broker — reference the RabbitMQ service, e.g.:
CELERY_BROKER_URL=${{RabbitMQ.RABBITMQ_URL}}
# Demo sqlite persistence (set on identity, account, payments, ledger, frontend + workers):
SQLITE_DIR=/data
```

Do NOT set `DATABASE_URL` — leaving it unset keeps every service on its own
sqlite file. (Postgres is still supported: setting a `postgres*`
`DATABASE_URL` switches that service to Postgres automatically.)

`ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` need no manual work: the settings
auto-trust `RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_PRIVATE_DOMAIN`,
`.up.railway.app`, and `.railway.internal`. Override via env only if you use a
custom domain.

### 3.2 Service-to-service URLs (use private domains + web port)

Railway web services listen on the dynamic `$PORT` internally, but private
networking reaches them on that same port. Replace `<svc>` with your actual
Railway service names:

```bash
# account web + worker:
IDENTITY_SERVICE_URL=http://identity.railway.internal:8001
ENCRYPTION_KEY=<same Fernet key everywhere: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# payments web + worker:
ACCOUNT_SERVICE_BASE_URL=http://account.railway.internal:8002
FRAUD_SERVICE_URL=http://fraud.railway.internal:8006

# frontend web:
IDENTITY_SERVICE_URL=http://identity.railway.internal:8001
ACCOUNT_SERVICE_URL=http://account.railway.internal:8002
PAYMENT_SERVICE_URL=http://payments.railway.internal:8004
LEDGER_SERVICE_URL=http://ledger.railway.internal:8003

# gateway (only if deployed):
IDENTITY_UPSTREAM=http://identity.railway.internal:8001
ACCOUNT_UPSTREAM=http://account.railway.internal:8002
PAYMENTS_UPSTREAM=http://payments.railway.internal:8004
LEDGER_UPSTREAM=http://ledger.railway.internal:8003
FRONTEND_UPSTREAM=http://frontend.railway.internal:8005
FRAUD_UPSTREAM=http://fraud.railway.internal:8006
```

> Private-domain ports: use the service's **internal** port (the default in
> each `start.sh`: identity 8001, account 8002, ledger 8003, payments 8004,
> frontend 8005, fraud 8006). Do not use the public `https://…up.railway.app`
> URL for service-to-service calls.

## 4. Notes / gotchas

- **Migrations + static run automatically** in every `start.sh`
  (`migrate --noinput`, `collectstatic --noinput`), so no manual release step.
- **Web `start.sh` also boots a background Celery worker.** The dedicated
  worker services are still recommended for the named queues
  (`payment.internal`, `account_service.internal`, `ledger.internal`).
- **Fraud** needs no env; it serves `/` (health) and `POST /check/`.
- **Gateway is optional.** The simplest Railway setup exposes `frontend`
  directly and skips the gateway. Deploy the gateway only if you want the
  single-entry `/api/*` routing.
- **Local docker-compose still works** — all defaults fall back to the old
  `identity:8001`-style hostnames and sqlite when `DATABASE_URL` is unset.
