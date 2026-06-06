# Custom agentregistry image: just the arctl-server binary on a slim base.
#
# Why: the upstream image's canonical run mode mounts the host Docker socket and a
# real kubeconfig and rewrites it to skip TLS verification. We don't want host
# cluster credentials in a container for local dev. The binary is self-contained
# (migrations embedded) and on startup only needs Postgres, so we run it directly
# under our own control — no kubeconfig, no socket, no entrypoint rewrite.
FROM ghcr.io/agentregistry-dev/agentregistry/server:v0.3.3 AS upstream

FROM debian:12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=upstream /app/bin/arctl-server /usr/local/bin/arctl-server
ENTRYPOINT ["/usr/local/bin/arctl-server"]
