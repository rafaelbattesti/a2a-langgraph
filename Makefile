# Per-agent locked requirements, derived from the single root uv.lock.
# The uv workspace is local-dev only; each agent ships a pinned requirements.txt
# into its own (self-contained) build context for reproducible image builds.
AGENTS := orchestrator knowledge analysis

EXPORT = uv export --no-dev --no-emit-workspace --frozen

.PHONY: lock lock-check

## lock: refresh the root lock and re-export each agent's requirements.txt
lock:
	uv lock
	@for a in $(AGENTS); do \
		echo "export -> agents/$$a/requirements.txt"; \
		$(EXPORT) --package $$a > agents/$$a/requirements.txt; \
	done

## lock-check: fail if any agent's requirements.txt is stale vs the lock (CI guard)
lock-check:
	@for a in $(AGENTS); do \
		$(EXPORT) --package $$a | diff -u agents/$$a/requirements.txt - \
			|| { echo "agents/$$a/requirements.txt is stale — run 'make lock'"; exit 1; }; \
	done
