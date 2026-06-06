# Architecture

> **Mission:** the architectural *pattern* is the product. The workloads in §8 exist only to
> demonstrate the pattern. This document is the contract the implementation is held to;
> changes to it are deliberate architecture decisions, logged in §10.

Every component traces to a **force**, not to a previous attempt. Boundaries that matter have
a **fitness function** (§9) that fails the build when they erode — the antidote to the prior
collapse from unreviewed sprawl.

---

## 1. What the system is

A **governed multi-agent platform**, all-Python backend. A chat request enters through a UI,
is **classified then deterministically routed** to a specialized agent that runs over **A2A**,
reaching tools and data only through governed seams. New workloads are *registered*, not
grafted in.

Defining property: agents are **independently-deployable services that interoperate over
A2A**. The demonstrated claim is **standards-based agent interop + independent deployability**
(cross-language interop is *not* claimed — the system is single-language by choice).

## 2. The pattern (the product)

### 2.1 A federation of independent services

- **Each agent is an independently-deployable service** with its own image, exposing an
  AgentCard, discovered/resolved through the registry, invoked over A2A.
- **The shared seam is the contract, expressed as a versioned A2A extension** (JSON Schema
  over A2A `DataPart`s). A generated **Pydantic DTO package** (`contracts/`) is derived from
  those schemas — **DTOs only, no business logic**, so it is not a shared domain core.
- **Cross-cutting governance is delivered as adopted services** (gateway, registry, langfuse),
  not as code agents link.

### 2.2 Dependency Rule (per agent, lean)

```
  graph.py (LangGraph + all I/O: A2A, llm, retrieval, gateway, registry)  ──uses──▶  domain/
  domain/ is pure: imports no framework/driver.
```

The single enforced boundary: **`domain/` must not import `a2a`, `langgraph`, `mcp`, or any
driver** (`.importlinter` per agent, §9). Framework calls live in `graph.py`. Ports/adapters
folders are intentionally omitted for now (lean); reintroduce them if an agent's I/O grows
enough to warrant isolation.

### 2.3 Topology

```
        React + CopilotKit (ui/web)
                │  AG-UI
                ▼
        CopilotKit Runtime (ui/runtime)        ← AG-UI ↔ A2A bridge (no auth)
                │  A2A
                ▼
        agentgateway  ──extAuth──▶ dex (identity source)     ← INGRESS authn (listener phase)
                │  A2A                                            + EGRESS authz (backend phase)
                ▼
          ┌──────────────┐     resolves capability→agent
          │ orchestrator │◀──────────────  agentregistry
          └──────┬───────┘   classify (model) → dispatch (code)
          ┌──────┴───────┐
          ▼              ▼
      knowledge       analysis
      (RAG→publish)   (analyze + input-required)
          │              │
          ▼              ▼
   ┌────────────────────────────────────────┐        ┌────────────┐
   │ PostgreSQL + pgvector                    │◀───────│ ingestion  │ fetch→embed→upsert
   │ (corpus · checkpoints · audit)           │        │ (pipeline) │ (scheduled/triggered)
   └────────────────────────────────────────┘        └────────────┘
          │ publish (T3, human-gated via PR)
          ▼
      agentgateway ──▶ GitHub (PR)             egress action authz (CEL + extAuth)

  Observability: every service emits OpenTelemetry (GenAI semconv) → Langfuse (OTLP backend).
  Inference: agents/pipeline call Ollama (qwen3, nomic-embed-text); model declared per AgentCard.
```

**Deliberate non-goals (anti speculative generality):** no sub-supervisor tier; no runtime
dynamic-planner (fan-out = N concurrent A2A calls); no async message bus yet (defer NATS);
no ports/adapters folders yet; no churn×complexity hotspot check.

## 3. Components

| Component | Responsibility (one reason to change) | Deployable |
|---|---|---|
| **ui/web** | presentation, streaming, HITL affordances | image (Node) |
| **ui/runtime** | AG-UI ↔ A2A bridge (CopilotKit Runtime); no auth | image (Node) |
| **agentgateway** | ingress authn + egress action authz (CEL + extAuth) | adopted image |
| **dex** | identity source (OIDC) behind gateway extAuth; minimal user set | adopted image |
| **orchestrator** | classify intent → dispatch (resolves via registry) | image (Py) |
| **knowledge** | RAG over corpus → synthesize cited artifact → publish | image (Py) |
| **analysis** | analyze corpus; elicit params (`input-required`) | image (Py) |
| **ingestion** | pipeline: fetch → embed → upsert (NOT an agent) | image (Py) |
| **agentregistry** | catalog/discovery + governance metadata; capability→agent | adopted image |
| **PostgreSQL + pgvector** | corpus, checkpoints, audit | adopted image |
| **Ollama** | model execution (qwen3, nomic-embed-text) | adopted/host |
| **contracts** | A2A extension schemas → generated Pydantic DTOs | library (no image) |

## 4. Routing (model classifies, code dispatches)

1. **Rules** — explicit/structured intent dispatched deterministically, no model.
2. **Model classifies** — ambiguous free-text → a capability *label* (qwen3). Classification
   only.
3. **Code dispatches** — deterministic resolution of label → agent via **agentregistry**, then
   A2A send. The routing decision is code, never the model.

## 5. Capability → tool → port

| Capability | Tool | Version |
|---|---|---|
| Agent interop / bus | **A2A** (`a2a-sdk`) | 1.1.0 |
| Tool protocol | **MCP** (`mcp`) | 1.27.2 |
| Agent internal logic | **LangGraph** | 1.2.4 |
| Ingress authn + egress action authz | **agentgateway** (CEL conditional policies + `extAuth`; no OPA) | v1.3.0-alpha.1 |
| Ingress identity (OIDC) | **dex** (`extAuth` target behind the gateway) | v2.45.1 |
| Agent registry / discovery | **solo.io agentregistry** | v0.3.3 |
| Inference | **Ollama** + qwen3 (gen/classify), nomic-embed-text (embed) | v0.30.4 |
| Vector corpus / RAG + checkpoints + audit | **PostgreSQL + pgvector** | 18.4 / v0.8.2 |
| Observability | **OpenTelemetry** (GenAI semconv) → OTLP | — |
| Trace backend + eval record + online eval | **Langfuse** | v3.178.0 |
| Build-time eval gate | **DeepEval** | 4.0.5 |
| Adversarial / red-team + A/B | **Promptfoo** | 0.121.14 |
| Cross-agent contract | **local A2A extension** (JSON Schema) → generated Pydantic DTOs | — |
| UI | **CopilotKit** (React + Runtime) | v1.59.3 |

## 6. Eval & observability lines (no overlap)

- **OpenTelemetry** — instrumentation/OTLP transport.
- **Langfuse** — OTLP backend + runtime/online eval + dataset & score system-of-record + UI.
- **DeepEval** — build-time CI gate (hermetic, pytest, thresholds → fails PR); pushes scores to Langfuse.
- **Promptfoo** — adversarial / red-team + prompt-model A/B (A2A provider hits the agents).

Line: **build-time (DeepEval) vs runtime + record (Langfuse).**

## 7. Cross-cutting governance

- **agentgateway is the single bidirectional data plane:** ingress authn at the *listener*
  phase (via `extAuth` → `dex`), egress action authz at the *backend* phase. Policy is **CEL
  conditional policies + `extAuth`** — **not OPA/rego**.
- **Permission by reversibility (per action):** read/generate free (T0–1); internal corpus
  writes autonomous (ingestion, T2); **outward publish human-gated (T3)** via an `extAuth`
  approval step. No agent holds an action credential — only the gateway acts.
- **Publish is reversible by construction** — opens a **PR, never force-pushes**.
- **Verification (deterministic, not the generation path):** citation/grounding check on
  claims; gateway precondition + recorded rollback before any action; schema validation at
  every A2A boundary.
- **Two human-in-loop shapes, not collapsed:** *elicitation* (analysis → A2A `input-required`
  + checkpoint) vs *authorization* (knowledge publish → gateway approval).
- **Audit chain (day one):** request, prompt+version, retrieved sources+IDs, model+version,
  tool calls, approvals, action, errors/rollbacks.
- **Adversarial scope:** tool/action misuse (gateway least-privilege + preconditions +
  kill-switch). Kept regardless: retrieval returns **typed evidence, never raw text spliced
  into a prompt** — retrieved content is data, not instructions.

## 8. Demonstrator workloads

**WL1 — RAG → publish** (proves: routing, retrieval reuse, T3 gateway action)
`ui → runtime → agentgateway(authn) → orchestrator(classify→dispatch) → knowledge:
retrieve → synthesize(cited) → request approval → agentgateway publish(PR)[human-gated] → audit`

**WL2 — analysis with elicitation** (proves: routing, retrieval reuse, input-required + checkpoint)
`ui → runtime → agentgateway(authn) → orchestrator → analysis: begin → input-required(ask
params) → [user replies] → resume(checkpoint) → analyze → result`

Both read the **same corpus** — reuse-without-coupling (two consumers, zero shared domain code).

## 9. Fitness functions (anti-slop guardrails)

| # | Guards | Tool | Rule |
|---|---|---|---|
| 1 | **Contract compatibility** (linchpin) | A2A-extension **schema version-diff** + **AgentCard conformance** + boundary validation | breaking change to a declared extension version fails the build |
| 2 | Dependency direction (lean) | **import-linter** per agent | `domain/` must not import `a2a`/`langgraph`/`mcp`/drivers |
| 3 | No shared logic core | CI assertion | `contracts` is generated DTOs only; no agent imports another agent's code |
| 4 | Complexity | radon · lizard | cognitive ≤15, cyclomatic ≈10, per PR |
| 5 | Duplication | jscpd | token threshold; fail on regression |
| 6 | Behavior | **DeepEval** (gate) + Langfuse (record) | faithfulness/citation/classification accuracy; harness now, hard gate once calibrated |
| 7 | Adversarial | **Promptfoo** | injection / tool-misuse suite |

## 10. Decision log

| # | Decision | Why |
|---|---|---|
| D1 | Governed multi-agent router platform; pattern is the product | mission |
| D2 | A2A **service** federation, independently-deployable, persistent | independent deploy + standards interop |
| D3 | **All Python** — Go removed; cross-language interop claim dropped | simplicity; A2A claim narrowed to interop + independent deploy |
| D4 | Contract = local versioned A2A extension (JSON Schema) → generated Pydantic DTOs | single seam; DTOs (not logic) ⇒ not a shared core |
| D5 | Governance as adopted services (agentgateway, agentregistry, langfuse) | don't hand-roll cross-cutting concerns |
| D6 | Routing = rules → model **classifies** → code **dispatches** | model never routes |
| D7 | Flat topology; no sub-supervisor / dynamic planner / NATS / hotspots | add structure only on a real force |
| D8 | agentgateway **bidirectional**: ingress authn + egress authz via **CEL + extAuth** (not OPA) | matches the tool's actual policy model |
| D9 | Permission per-action by reversibility; publish via PR (reversible), human-gated T3 | calibrated trust; real rollback |
| D10 | **ingestion is a pipeline, not an agent** | deterministic ETL; nothing dispatches to it |
| D11 | identity source is **dex** (adopted OIDC) behind gateway extAuth; bespoke `auth` service dropped | adopt don't hand-roll auth (D5); gateway owns ingress authn natively |
| D12 | One PostgreSQL (corpus+checkpoint+audit) | right-sized for compose/solo |
| D13 | Eval split: DeepEval (build gate) vs Langfuse (runtime/record); Ragas & Pact dropped | no overlap; A2A-native contract checks |
| D14 | Front door: CopilotKit React + Runtime (Node, unavoidable) | adopted UI; minimal multi-user |
| D15 | A2A extension kept **local** for now | not externally published yet |
| D16 | **Single uv monorepo**, native tooling (uv + npm for ui) + compose; no meta-build tool, no task runner | right-sized |
| D17 | Lean now: no ports/adapters folders; dependency-direction reduces to `domain/` purity | start minimal, grow on demand |

### Open items
- dex minimal user set (staticPasswords connector).
- Eval thresholds (faithfulness, citation, classification accuracy) — calibrate before hard gate.
- agentgateway / agentregistry are early (alpha / v0.3.x) — track maturity.
- A2A extension name (`platform-v1` placeholder).

## 11. Repo shape (all-Python single uv monorepo)

```
a2a-langgraph/
├── pyproject.toml          # single uv workspace; members = agents/*, services/*, contracts
├── uv.lock
├── docs/ARCHITECTURE.md
├── agents/                 # A2A agents — each: Dockerfile, pyproject, .importlinter,
│   ├── orchestrator/        #   src/<a>/{domain/, graph.py, card.py, __main__.py}, tests/
│   ├── knowledge/
│   └── analysis/
├── services/               # Python, not A2A agents (each: Dockerfile, pyproject, src/, tests/)
│   └── ingestion/           #   src/ingestion/{domain/, pipeline.py, __main__.py}
├── contracts/              # library (no Dockerfile): extensions/<v>/{extension.json, schemas/},
│                           #   src/contracts/ (generated DTOs), codegen.py
├── ui/                     # Node (CopilotKit): web/ + runtime/ (each: Dockerfile, package.json, src/)
├── deploy/
│   └── compose.yaml        # builds the 6 local images; pulls infra images
└── infra/                  # adopted-infra config (no Dockerfiles)
    ├── agentgateway/config.yaml    # listeners=ingress authn (extAuth) · backend=egress · CEL
    ├── agentregistry/config.yaml
    ├── auth/config.yaml            # dex (OIDC) identity source; extAuth target
    ├── langfuse/                   # self-host config
    └── postgres/init.sql           # pgvector + corpus/checkpoint/audit schemas
```
Deployables (own image): 3 agents, 1 service, 2 UI. `contracts` is an imported library;
`infra` uses upstream images.
