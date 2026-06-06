# deploy

Local-development infrastructure for the a2a-langgraph platform, via Docker Compose.
This is the **infra tier only** (datastore, observability, identity, gateway, registry).
Application images (agents, services, ui) are not wired in here yet.

> **DEV ONLY.** Every credential in `compose.yaml` is an insecure local default.
> TLS is deferred — dex serves over plain HTTP and there are no leaf certs yet
> (only a root CA in [`certs/`](./certs/)). Do not use this configuration anywhere
> but a local machine.

All commands below are run **from the project root**. A root [`.env`](../.env) sets
`COMPOSE_FILE=deploy/compose.yaml`, so `docker compose …` resolves this stack from the
root (and takes precedence over any other compose file in the repo).

## Prerequisites

- Docker Engine + Compose v2 (`docker compose version`).
- First start builds the custom agentregistry image from
  [`../infra/agentregistry/Dockerfile`](../infra/agentregistry/Dockerfile).

## Lifecycle

```bash
# Bring the whole stack up (build the agentregistry image on first run)
docker compose up --build

# Bring it up without rebuilding (after the image exists)
docker compose up -d

# Status of every service
docker compose ps

# Follow logs (all, or one service)
docker compose logs -f
docker compose logs -f langfuse-web

# Restart a single service
docker compose restart agentgateway

# Stop containers, KEEP data (volumes)
docker compose down

# Stop containers and WIPE data (drops postgres/clickhouse/minio/redis volumes)
docker compose down -v
```

### Rebuilding agentregistry

```bash
docker compose build agentregistry          # rebuild the custom image
docker compose up --build agentregistry     # rebuild and (re)start
```

### Resetting just Postgres

`init.sql` runs only on first cluster init. To re-run it (e.g. after editing
[`../infra/postgres/init.sql`](../infra/postgres/init.sql)):

```bash
docker compose rm -sf postgres
docker volume rm a2a-langgraph_postgres_data
docker compose up -d postgres
```

## Services & endpoints

| Service | Image | Host endpoint |
|---|---|---|
| postgres | `pgvector/pgvector:pg18` | `localhost:5432` (DBs: `postgres`, `platform`, `agentregistry`) |
| langfuse-web | `langfuse/langfuse:3.178.0` | http://localhost:3000 |
| langfuse-worker | `langfuse/langfuse-worker:3.178.0` | `localhost:3030` |
| clickhouse | `clickhouse/clickhouse-server` | `localhost:8123` / `9000` |
| minio | `cgr.dev/chainguard/minio` | API `localhost:9090`, console http://localhost:9091 |
| redis | `redis:7` | `localhost:6379` |
| dex (OIDC) | `ghcr.io/dexidp/dex:v2.45.1` | http://localhost:5556/dex |
| agentgateway | `cr.agentgateway.dev/agentgateway:v1.3.0-alpha.1` | `localhost:8080` (admin/stats/readiness `15000/15020/15021` internal) |
| agentregistry | custom (`infra/agentregistry/Dockerfile`, v0.3.3) | http://localhost:12121 (UI + `/docs`), MCP `localhost:31313` |

## Notes

- **agentgateway returns 503** on `:8080` until its backend (`orchestrator:9999`)
  exists — that is expected; the gateway itself is healthy.
- **One shared Postgres** backs the app (`platform`, pgvector-enabled), langfuse
  (`postgres`), and agentregistry (`agentregistry`); the extra databases are created
  by `init.sql`.
- **agentregistry** runs the bare `arctl-server` binary against Postgres only — no
  Docker socket and no host kubeconfig are mounted.
