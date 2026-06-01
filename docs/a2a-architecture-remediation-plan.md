# A2A Architecture Remediation Plan

Status: the first and second remediation slices have been implemented for the
current internal agent boundaries. The next platform slice is to use the richer
Agent Cards in a small skill registry and remove hardcoded peer selection from
the Coordinator.

## Context

This system is intended to evolve from a thesis-focused multi-agent MVP into a
multi-service orchestrated platform. The current implementation already has
useful service boundaries: each agent runs as a separate service, agents speak
A2A to one another, and the Researcher uses MCP for external tool access.

The main architectural gap is that A2A is currently used mostly as a transport
envelope for synchronous RPC. The next platform step should make A2A contracts
real before adding dynamic discovery, streaming, durable task state, or chat
session features.

## Feedback Assessment

| Feedback | Original evidence | Severity | Remediation direction |
|---|---|---:|---|
| A2A is used as ceremonial RPC | Agent calls serialized dictionaries into one text part, then parsed response text back into dictionaries. | High | Move to typed A2A structured data parts with Pydantic validation. |
| Agent cards are decorative | Skills, capabilities, and modes are advertised, but dispatch only uses configured URLs. | High | Make card skills describe real request and response contracts first; later route by advertised skill. |
| Coordinator topology is hardcoded | Peer URLs are environment-backed constants and LangGraph edges are fixed by named agent role. | Medium | Introduce a skill registry and data-driven dispatch once the contracts are explicit. |
| Agent boundaries have limited payoff today | All LLM agents use the same model factory and model; only the Researcher has a unique external tool. | Medium | Add per-agent model, tool, and capability configuration as the platform matures. |
| Chat foundations are absent | Streaming is disabled, calls block up to a flat timeout, task storage is in memory, and no cross-turn session state is modeled. | High for chatbot roadmap | Add durable task storage, streaming events, persisted conversation state, and resumable workflows. |
| Parse fallback is fragile | Non-JSON input became `{"topic": raw}`, which only fit some agents and failed later for others. | High | Remove the fallback; reject malformed payloads with explicit validation errors. |
| MCP result coercion is defensive | The arXiv adapter normalizes several possible result shapes. | Low/Medium | Pin the MCP tool contract and keep normalization at the adapter boundary with tests. |

## First Remediation: Real A2A Contracts

### Goal

Make the A2A boundary trustworthy and inspectable. Internal agents should no
longer treat A2A messages as opaque text containing ad hoc JSON. Each agent
should expose a clear request contract, response contract, and validation
behavior.

### Scope

1. Define explicit Pydantic request and response models for agent boundaries:
   `ThesisRequest`, `ResearchRequest`, `ResearchResponse`,
   `SynthesisRequest`, `SynthesisResponse`, `CritiqueRequest`,
   `CritiqueResponse`, and `ThesisResult`.
2. Replace normal internal payload transport from JSON-in-`TextPart` to the
   structured payload API supported by `a2a-sdk==1.0.3`.
3. Remove the fallback that converts arbitrary non-JSON text into
   `{"topic": raw}`.
4. Validate each agent's expected input schema before invoking its LangGraph
   graph.
5. Return structured protocol or application errors when payload validation
   fails.
6. Add contract metadata to each agent card skill, including input schema name,
   output schema name, and schema version.
7. Keep plain text input only at the public Coordinator boundary if that is an
   intentional user convenience; internal agent-to-agent calls should use
   structured contracts.

### Acceptance Criteria

- Internal A2A calls do not use opaque JSON text as the normal protocol
  contract.
- Invalid payloads fail before graph execution.
- Critic and Synthesizer reject topic-only or malformed payloads with clear
  validation failures.
- Agent cards advertise the same contract names and versions that the server
  actually validates.
- Tests cover valid structured round-trips, malformed payload rejection, and
  agent card contract metadata.
- The resulting contract layer can support later skill-based discovery without
  rewriting each agent handler.

## Suggested Implementation Sequence

1. Add boundary contract models to the shared schema package.
2. Add structured payload extraction and serialization helpers in the common
   A2A client/server layer.
3. Update one internal edge first, preferably Coordinator to Researcher, as a
   vertical slice.
4. Extend the same pattern to Synthesizer and Critic.
5. Update agent cards with contract metadata.
6. Add negative tests for malformed payloads and positive tests for structured
   round-trips.

## Follow-On Platform Work

After real contracts are in place, the next improvements should be:

1. Skill-based discovery and dispatch from agent cards.
2. Durable A2A task storage and resumable task lifecycle.
3. Streaming and partial progress events for chat and long-running research.
4. Persisted conversation/session state.
5. Per-agent model and tool configuration.
6. Observability for routing decisions, model calls, tool calls, latency,
   retries, and structured failures.

## Second Feedback Assessment

The first remediation moved payload transport from opaque JSON text to typed
structured data parts, but the card metadata still needs to become genuinely
useful to external consumers and future discovery logic.

| Feedback | Current evidence | Severity | Remediation direction |
|---|---|---:|---|
| Card homogenization was centralized | `contract_tags()` adds generic `thesis` and `research` tags to every agent. | Medium | Move semantic tags out of common helpers and into each agent card declaration. |
| Contract advertisement is not actionable | Card metadata advertises schema class names like `ResearchRequest`, but not JSON Schema. | High | Embed `model_json_schema()` for input and output contracts in the A2A card extension. |
| Internal contracts contain dead required fields | `SynthesisRequest.topic` and `CritiqueRequest.topic` are required but handlers ignore them and use `findings.topic`. | Medium | Remove unused top-level `topic` fields from Synthesizer and Critic requests. |

## Second Remediation: Actionable Agent Cards

### Goal

Make Agent Cards describe the actual agent and expose enough contract detail
for a consumer that does not import `thesis_common` to inspect the request and
response payloads.

### Scope

1. Remove generic domain tags from the shared `contract_tags()` helper.
2. Add explicit semantic tags at each agent boundary:
   - Coordinator: `orchestration`, `thesis`
   - Researcher: `research`, `evidence`, `arxiv`, `mcp`
   - Synthesizer: `synthesis`, `thesis-draft`
   - Critic: `critique`, `viability-review`
3. Keep contract tags machine-readable but narrow, for example:
   `contract:1.0.0`, `input:ResearchRequest`, `output:ResearchResponse`.
4. Replace extension params that only expose class names with actionable schema
   metadata:

   ```python
   {
       "contract_version": "1.0.0",
       "input": {
           "name": "ResearchRequest",
           "media_type": "application/json",
           "json_schema": ResearchRequest.model_json_schema(),
       },
       "output": {
           "name": "ResearchResponse",
           "media_type": "application/json",
           "json_schema": ResearchResponse.model_json_schema(),
       },
   }
   ```

5. Remove unused top-level `topic` from `SynthesisRequest` and
   `CritiqueRequest`; rely on `ResearchFindings.topic` as the single source of
   topic truth for those agents.
6. Update Coordinator calls so Synthesizer and Critic payloads no longer send
   discarded topic values.
7. Update tests to prove:
   - each agent card has distinct semantic tags,
   - extension params include JSON Schema for input and output,
   - Synthesizer and Critic requests validate without top-level `topic`,
   - extra top-level `topic` remains rejected while `extra="forbid"` is active.

### Acceptance Criteria

- Agent cards no longer receive generic semantic tags from common code.
- A consumer can inspect an Agent Card and understand the input/output JSON
  shape without importing this repository's Python models.
- Synthesizer and Critic contracts contain no required fields that handlers
  ignore.
- The contract metadata is ready to be used by a future skill registry or
  discovery-based router.

## Goal Status Summary

Goal: evolve this MVP into a multi-service orchestrated platform where A2A is
used for meaningful interoperability, discovery, and task coordination rather
than only as a request/response envelope.

Current status:

- Service boundaries exist: Coordinator, Researcher, Synthesizer, Critic, and
  MCP arXiv are separate services.
- A2A transport now uses structured data parts with typed Pydantic validation.
- The silent non-JSON fallback has been removed from the normal A2A boundary.
- Agent cards advertise contract names, versions, media types, and full input
  and output JSON Schema.
- Agent cards carry agent-specific semantic tags supplied by each agent rather
  than generic tags from common code.
- Synthesizer and Critic contracts no longer contain unused top-level `topic`
  fields; `ResearchFindings.topic` is the topic source for those agents.
- A2A client/server boundaries and Coordinator routing now emit non-secret logs
  for contract validation, call lifecycle, route decisions, and completion.

Next milestone:

1. Use the richer Agent Cards to introduce a small skill registry.
2. Replace hardcoded coordinator peer selection with data-driven lookup by
   skill and contract.
3. Add tests proving the Coordinator can resolve the expected agent by skill
   metadata instead of direct role-specific URLs.

Later milestones:

1. Durable task storage and resumable A2A task lifecycle.
2. Streaming and partial progress events for chat and long-running research.
3. Persisted conversation/session state.
4. Per-agent model and tool configuration.
5. Auth, observability, retries, and structured failure telemetry.

## Third Assessment: The A2A Interaction Model

> The sections above are kept as historical record of earlier remediations and
> their framing. They are **not** the authoritative reference. The single source
> of truth for the A2A API and mental model is the installed `a2a-sdk` (proto
> types, stubs, package source). Where an earlier claim conflicts with the
> installed SDK or this section, the SDK and this section win.

The first two remediations fixed payload *encoding* (opaque JSON text to typed
data parts) and card *metadata*. They did not change the *interaction model*,
which is still request/response RPC. This is the remaining root defect.

### Root cause

The shared scaffolding models A2A as typed RPC: one Pydantic model in, one out,
carried as a single data `Message`. A2A instead models a `Task` lifecycle
(`submitted -> working -> completed | failed | input_required | ...`) that
produces `Artifact`s and emits events. The current executor enqueues a bare
agent `Message` and never creates a task.

This is **not protocol-violating** — `DefaultRequestHandlerV2.on_message_send`
supports a valid "Message-only" mode, and the current code rides that narrow
path. But it is the degenerate mode, and it forecloses durable tasks, streaming,
progress, cancellation, and sessions — i.e. the chatbot north star.

Verified against the installed `a2a-sdk` (proto types in `a2a.types.a2a_pb2`,
`TaskUpdater`, `AgentExecutor`, `DefaultRequestHandlerV2`, `ActiveTask`).

### Problem backlog (descends from the root)

| ID | Problem | Evidence | Severity |
|---|---|---|---:|
| A1 | Executor emits a bare `Message`; no `Task` lifecycle. Task store is inert; no resumability/progress. | `a2a_server.py` `enqueue_event(message)` vs `TaskUpdater.submit/start_work/add_artifact/complete` | High (root) |
| A2 | `Handler = Callable[[BaseModel], BaseModel \| dict]` bakes in RPC; no task awareness, fixed result shape, two-shape return smell. | `a2a_server.py` `Handler` type | High (root) |
| B1 | Client keeps only the `message` payload, discards `task`/`status_update`/`artifact_update`. Breaks once the server returns a Task. | `a2a_client.py` `WhichOneof("payload") == "message"` | High |
| B2 | Client masks real failures as "no message": framework turns a raised error into a failed `Task`, which the client ignores. | `active_task.py` producer marks task failed; client only reads `message` | High |
| C1 | `cancel()` raises `NotImplementedError` — violates the `AgentExecutor` contract; cancel requests crash. | `a2a_server.py` `cancel` | Medium |
| D1 | Streaming disabled; required for chat token/progress streaming. | `capabilities.streaming=False`, `ClientConfig(streaming=False)` | Medium (roadmap) |
| E1 | Client never sets `context_id`; every call is a new context. `context_id` is the A2A session/conversation handle. | `a2a_client.py` sets only `message_id` | Medium (roadmap) |

Checked and acceptable: proto `Struct` build via `ParseDict`; hand-assembling
`create_agent_card_routes + create_jsonrpc_routes` (no higher-level app builder
exists in this version); `WhichOneof("payload")` (correct oneof name — the logic
around it is the defect, not the call).

### Why each remediation is canonical library use

Re-verified against `agent-stubs/a2a` and the installed package.

- **A1 (drive the task via `TaskUpdater`).** The `EventQueue` ABC
  (`events/event_queue.pyi`) exposes only `enqueue_event`; `TaskUpdater`
  (`tasks/task_updater.pyi`) is the SDK's own façade that turns that single
  primitive into `submit/start_work/add_artifact/complete`.
  Using it is using the lifecycle the SDK defines, not hand-rolling task state.
- **A2 (`AgentLogic` strategy receiving a `TaskUpdater`).** `AgentExecutor.execute`
  returns `None` (`agent_execution/agent_executor.pyi`) — the unit of work is
  "drive the task," not "return a value", so the strategy signature matches the
  contract. A new behavior becomes a new `AgentLogic` while `StrategyExecutor`
  stays the single `AgentExecutor` implementation (open/closed via the SDK seam).
- **B1 (consume the stream to terminal, read `task.artifacts`).**
  `Client.send_message` returns `AsyncIterator[StreamResponse]` whose `payload`
  oneof is `task|message|status_update|artifact_update` (`client/client.pyi`).
  The SDK's own `ResultAggregator.consume_all -> Task | Message | None`
  (`tasks/result_aggregator.pyi`) confirms the final value is a `Task`, so the
  client must read all variants, not cherry-pick `message`.
- **B2 (read the failed `Task`).** `on_message_send` is typed `Message | Task`
  (`request_handlers/default_request_handler_v2.pyi`) and the SDK converts an
  executor exception into a failed task; reading the `task` variant surfaces it.
  Checking `task.status.state == TaskState.TASK_STATE_FAILED` (proto enum) is the
  canonical terminal check, replacing the "no message" heuristic.
- **C1 (cooperative `cancel` via `TaskUpdater.cancel()`).** `AgentExecutor.cancel`
  is an `@abstractmethod` (`agent_executor.pyi`) the handler invokes; honoring it
  preserves Liskov instead of throwing. `TaskUpdater.cancel()` (`task_updater.pyi`)
  is the SDK path to `TASK_STATE_CANCELED`, so cancellation uses the primitive.
- **D1 (streaming via the SDK channel).** `on_message_send_stream` is gated by
  `capabilities.streaming` and yields `Event`s (`default_request_handler_v2.pyi`);
  progress is emitted with `TaskUpdater.update_status`/`add_artifact`
  (`task_updater.pyi`). The matching client primitive is `ClientConfig.streaming`
  + consuming the `StreamResponse` iterator (`client/client.pyi`) — no bespoke
  channel.
- **E1 (thread `context_id`).** `Message.context_id` (proto) and
  `RequestContext.context_id` (`agent_execution/context.pyi`) are the SDK's
  conversation/session handle, already propagated server-side. Setting it on the
  outgoing `SendMessageRequest.message` uses the protocol's own field instead of
  an external session map.

### Target architecture: decompose `common`, adopt a Strategy executor

`common` is dissolved into purpose-named workspace packages. Layering rule:
**inheritance only where the SDK provides an ABC; composition/injection
everywhere else.** A2A provides exactly one server-side inheritance point
(`AgentExecutor`); that single fact decides the shape.

```
contracts        pure Pydantic; depends on nothing (no transport, no A2A)
config  llm  observability    cross-cutting platform concerns
reasoning (per-agent LangGraph graphs)   uses contracts/llm/MCP; imports NO a2a types
a2a_runtime (adapter layer)              uses a2a-sdk + contracts
  - StrategyExecutor  implements  a2a.AgentExecutor
  - AgentLogic (Protocol)  <- injected per-agent strategy
  - data-part helpers, app builder, client wrapper
```

Package map (import names prefixed to avoid shadowing stdlib; final names TBD):

| Package | Depends on | Holds | Pattern |
|---|---|---|---|
| `contracts` | — | `ContractModel` base, versioning, JSON-schema card helpers | none (data) |
| `thesis_contracts` | `contracts` | thesis request/response models | none (data) |
| `config` | pydantic-settings | typed `BaseSettings`, per-agent subclasses, injected | settings + injection |
| `observability` | stdlib | `configure_logging()`; telemetry later | none (function) |
| `llm` | `config` | `model_for(role)` factory | Factory now; Strategy when models diverge |
| `a2a_runtime` | `a2a-sdk`, `contracts` | `AgentLogic`, `StrategyExecutor`, data-part (de)serialization, app builder, client wrapper | Adapter + Strategy |

Note: `message_from_model`/`model_from_message` move into `a2a_runtime` (they
touch A2A `Message`); `contracts` stays transport-free.

### The Strategy executor (replaces `Handler`)

```python
# a2a_runtime
class AgentLogic(Protocol):
    async def run(self, request: BaseModel, task: TaskUpdater) -> None: ...

class StrategyExecutor(AgentExecutor):            # implements (is-a) — SDK ABC
    def __init__(self, logic: AgentLogic, ...): ...   # uses (injected)
    async def execute(self, context, event_queue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)  # uses
        await updater.start_work()
        try:
            await self._logic.run(parsed_request, updater)
        except Exception:
            await updater.failed(...)              # executor GUARANTEES a terminal state
            raise
        # if logic did not reach terminal, executor completes
```

- Executor owns the **invariant** lifecycle (start_work, guaranteed terminal on
  failure). Decision: the executor guarantees the terminal state.
- Strategy owns the **variable** part — a one-shot agent emits one artifact +
  `complete()`; a streaming agent emits many updates; an agent needing more info
  calls `requires_input()`. This is how "result shape depends on the agent" is
  expressed, with no `mode=` boolean fork.
- Each agent's `AgentLogic` lives in its own package and calls its pure graph,
  keeping LangGraph free of A2A types.

### Relationships to A2A primitives (the canonical reference)

| Your code <-> A2A primitive | Relationship |
|---|---|
| `StrategyExecutor` <-> `AgentExecutor` | implements (is-a) — the one true inheritance |
| executor <-> `TaskUpdater` | uses (per-request) |
| executor <-> `AgentLogic` | uses (injected) |
| app <-> `TaskStore`/`InMemoryTaskStore` | uses (injected) |
| app <-> `DefaultRequestHandler` | uses |
| client wrapper <-> `Client` | uses (via `create_client`; never subclassed) |
| everything <-> `Message`/`Task`/`Artifact`/`Part` | uses (data) |

Headline: exactly one `is-a` against A2A exists in the whole system. A second
base class against the SDK is a smell.

### Migration sequence (additive; each step compiles and tests green)

1. Create the new workspace packages empty, alongside `common`.
2. Move dependency-free leaves: `contracts` (mechanism), `config`,
   `observability`, `llm`. Update imports.
3. Move thesis models into `thesis_contracts` (depends on `contracts`).
4. Build `a2a_runtime`: `AgentLogic` + `StrategyExecutor` (terminal guarantee) +
   data-part helpers + app builder. Fixes A1, A2. Port Researcher first as a
   vertical slice, then the other agents.
5. Rework the client wrapper to consume the stream to terminal and read
   `task.artifacts`; surface failed-task state. Fixes B1, B2.
6. Implement cooperative `cancel()`. Fixes C1.
7. Delete `common`.
8. Later slices on the new seam: streaming (D1), `context_id` sessions (E1),
   durable `TaskStore`, skill registry.
