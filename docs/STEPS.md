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

1. Add uv dependencies
2. Add main stub that creates a simple uvicorn server
3. Add a one node graph that logs the agent's name on GET /
3. Add Dockerfiles
4. Create minimum agents services in docker compose

Notes (as built):
- agents orchestrator/knowledge/analysis are uv workspace members (`members = ["agents/*"]`); runtime deps `langgraph` (1.2.4), `starlette`, `uvicorn`.
- each `src/<agent>/`: `graph.py` = one-node `StateGraph` whose node logs the agent name; `__main__.py` = Starlette `GET /` → invoke graph → `{"agent": <name>}`; binds `PORT` (default 9999).
- Dockerfiles: **self-contained + reproducible** — context = each agent's own dir; install pinned `requirements.txt` then `uv pip install --no-deps .`. The `requirements.txt` are exported from the single root `uv.lock` via `make lock` (workspace/lock are local-dev only; never enter an image). `make lock-check` guards drift in CI; CI tests still run on the workspace (`uv sync --all-packages`).
- compose services orchestrator/knowledge/analysis, host ports 9001/9002/9003 → container 9999.
