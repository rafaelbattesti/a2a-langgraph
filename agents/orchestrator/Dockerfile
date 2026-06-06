# syntax=docker/dockerfile:1
# Self-contained AND reproducible: build context = agents/orchestrator only.
# requirements.txt is exported from the root uv.lock via `make lock` (the uv
# workspace itself never enters the image — it is a local-dev convenience).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Pinned, hashed deps first (cached layer).
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Then the agent itself, without re-resolving its dependencies.
COPY pyproject.toml ./
COPY src ./src
RUN uv pip install --system --no-cache --no-deps .

EXPOSE 9999
CMD ["python", "-m", "orchestrator"]
