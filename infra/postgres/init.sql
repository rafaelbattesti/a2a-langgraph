-- Minimal bootstrap for the shared local-dev Postgres (pgvector/pgvector:pg18).
-- DEV ONLY. Runs once, on first cluster init, via /docker-entrypoint-initdb.d/.
--
-- The default `postgres` database is used by Langfuse (its DATABASE_URL).
-- Here we add the two extra databases the stack needs:
--   * platform      — app corpus/checkpoints/audit; pgvector enabled (D12: one Postgres)
--   * agentregistry — agentregistry server store
CREATE DATABASE platform;
CREATE DATABASE agentregistry;

\connect platform
CREATE EXTENSION IF NOT EXISTS vector;
