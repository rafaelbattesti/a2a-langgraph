# Implementation steps

## Initialization

1. initialize uv repository
2. create virtual environment
3. activate virtual environment
4. add core python dependencies to uv
5. generate self signed CA and add to deploy/

Notes (as built):
- uv workspace root (`pyproject.toml`, `members = []`); members added per-package as scaffolded.
- venv via `uv sync` (steps 2–3 folded; no manual create/activate).
- root dev group: ruff, pytest, import-linter. Runtime deps live per-member, added later.
- root CA only: `deploy/certs/` (`ca.crt` committed, `*.key` gitignored, `generate-ca.sh`). Leaf certs deferred until compose hostnames exist.

## Tooling

1. Create docker compose with tools defaults
- postgres/pgvector
- langfuse
- agentgateway
- agentregistry
- OIDC https://dexidp.io/docs/configuration/
2. Run docker compose up

Notes (as built — `deploy/compose.yaml`, latest images):
- postgres: `pgvector/pgvector:pg18`, one shared instance; DBs `postgres` (langfuse), `platform` (pgvector ext), `agentregistry` via `infra/postgres/init.sql`. Volume mount at `/var/lib/postgresql` (pg18 convention).
- langfuse: `langfuse/langfuse:3.178.0` web + worker, plus clickhouse + redis + minio (canonical self-host deps).
- dex: `ghcr.io/dexidp/dex:v2.45.1`; `infra/auth/config.yaml` (memory storage, http issuer, one static client + user). Plaintext (TLS deferred).
- agentgateway: `cr.agentgateway.dev/agentgateway:v1.3.0-alpha.1`; `infra/agentgateway/config.yaml` (A2A listener on :8080 — :15000/:15020/:15021 are its admin/stats/readiness).
- agentregistry: v0.3.3 via custom `infra/agentregistry/Dockerfile` (arctl-server binary on debian-slim) — no Docker socket, no host kubeconfig; needs only Postgres.
- ports: langfuse 3000 · dex 5556 · gateway 8080 · registry 12121 (+MCP 31313) · postgres 5432.

## Agents

1. Add main stub that creates a simple uvicorn server
2. Add Dockerfiles
3. Create minimum agents services in docker compose
4. Run docker compose up
