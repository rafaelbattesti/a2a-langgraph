# Architecture

> Incremental document. The product vision lives in [GOAL.md](GOAL.md); the A2A
> remediation backlog and rationale live in
> [a2a-architecture-remediation-plan.md](a2a-architecture-remediation-plan.md).
> The authoritative reference for any A2A API is the installed `a2a-sdk`, not
> this document.

This file grows one iteration at a time. It records the **structural blocks** of
the platform and the concrete layout each iteration lands.

## High-level blocks

The platform is composed of five kinds of block. Everything above the core
libraries is an **A2A service** (an `AgentCard` + a `StrategyExecutor`); a
service's internal shape — single agent, coordinator-of-agents, or sequential
pipeline — is invisible across the A2A boundary.

| Block | Role | Composed of |
|---|---|---|
| Ingress adapters | Turn external triggers (chat, admin workflows, anomaly/eval) into A2A requests | A2A clients |
| Platform Coordinator | The custodian: routes a request to the target service; hosts the governance gate | A2A service (router logic) |
| User Services | The capabilities users ask for (Thesis generator, Knowledge search, DataAnalysis, Support/IT, HR, Training) | A2A services (leaf / coordinator / pipeline) |
| Platform Services | The self-governing control plane (Governance, Provenance, Observability, Evaluation, Security, Capability/Agent/Tool/MCP/Knowledge/Memory/User management, Self-Improvement) | A2A services + boundary seams |
| Core libraries | The shared abstractions every service is built from | Importable packages, **not** services |

Two principles hold across all iterations:

- **The A2A boundary is the composition boundary.** Callers bind to cards
  (skills + contracts), never to a callee's internal topology or URL.
  Composition is therefore recursive and uniform (Composite).
- **Governance attaches at the boundary, not inside agents.** Policy,
  provenance, observability, and security ride on A2A client interceptors and
  the server call context — never inside LangGraph reasoning.

Only the **User Services / Thesis generator** and **Core libraries** blocks are
realized in Iteration 1. The rest are named here as the target decomposition.

## Iteration 1 — Extract core libraries; wrap the thesis agents as a user service

Goal: replace the `common` package with capability-agnostic **core libraries**,
and move the existing thesis agents into a single **user service**, with all
thesis-specific knowledge owned by that service.

### Layout

```
core/
  a2a/               # A2A adapter layer — import package `a2a_core` (executor, client, app, data parts)
  contracts/         # contract mechanism: ContractModel base, versioning, card JSON-schema
  config/            # typed settings
  observability/     # logging now; telemetry later
  llm/               # model factory
services/
  agentic/
    researcher/
      thesis_contracts/   # thesis request/response models + card definitions
      coordinator/        # thesis orchestration (A2A service)
      librarian/          # A2A service (uses arXiv MCP)
      critic/             # A2A service
      synthesizer/        # A2A service
      mcp_arxiv/          # arXiv MCP tool used by librarian
```

### core — platform abstractions (no capability knowledge)

| Package | Responsibility (one sentence) | Depends on |
|---|---|---|
| `a2a_core` | Adapt agent reasoning to the A2A task lifecycle and carry typed contracts in data parts | `a2a-sdk`, `contracts` |
| `contracts` | Define the versioned, transport-neutral contract base and emit card JSON-schema | — |
| `config` | Provide typed, validated, injectable settings | pydantic-settings |
| `observability` | Configure structured logging (telemetry later) | stdlib |
| `llm` | Provide the model for a role | `config` |

`a2a_core` owns the **only** A2A inheritance in the system:
`StrategyExecutor(AgentExecutor)`. It also exposes the `AgentLogic` Protocol,
`build_card` / `serve`, the data-part (de)serialization helpers, and the client
wrapper. None of it imports any thesis name. (The import name `a2a_core`
deliberately avoids shadowing the SDK's `a2a`.)

### services/agentic/researcher — the thesis capability (all thesis knowledge)

| Package | Holds | Built from |
|---|---|---|
| `thesis_contracts` | `ResearchRequest/Response`, `Synthesis*`, `Critique*`, `ResearchFindings`, `ThesisResult`; the agent **card** definitions | `contracts`, `a2a_core` |
| `coordinator` | thesis orchestration graph + its `AgentLogic`; the thesis service's public card | core libs + `thesis_contracts` |
| `librarian` / `critic` / `synthesizer` | each agent's LangGraph graph + `AgentLogic` + card + app entrypoint | core libs + `thesis_contracts` |
| `mcp_arxiv` | arXiv MCP server (librarian's tool) | MCP |

Each agent contributes a **Strategy** (an `AgentLogic` implementation) wrapping
its graph; it does **not** subclass any A2A type. Cards and contracts live here
because they describe *this* service's skills and payloads.

`mcp_arxiv` stays with researcher as the research tool for now; it may graduate
to a platform Tool/MCP service in a later iteration.

### Relationships: core ↔ researcher

```
researcher  ──────depends on──────▶  core     (one direction; core never imports thesis)
   │
   ├─ thesis_contracts models   ── extend ─────▶  contracts.ContractModel
   ├─ <agent>.AgentLogic        ── implements ──▶  a2a_core.AgentLogic        (Protocol)
   ├─ <agent> executor          ── is the shared ▶ a2a_core.StrategyExecutor  (composed, not subclassed)
   ├─ <agent> card              ── built by ────▶  a2a_core.build_card + contracts JSON-schema
   └─ <agent> app               ── uses ───────▶  a2a_core.serve, config, observability, llm
```

Stated plainly:

- **Dependency direction is inward.** The capability depends on the platform
  abstractions; the platform never depends on the capability. Adding a second
  user service changes nothing in `core`.
- **The only A2A `is-a` lives in `core`** (`StrategyExecutor implements
  AgentExecutor`). researcher contributes `AgentLogic` *implementations*
  (Strategy) and `ContractModel` *subclasses* (data); it `uses` everything else.
- **Cards and contracts are owned by the service**, built with core helpers, so
  a consumer can read a thesis card without importing any thesis Python.

### Out of scope for Iteration 1

Governance/interceptor seam, ServiceRegistry/discovery, platform coordinator,
streaming, sessions, durable task store. These land in later iterations on top
of this layout.
