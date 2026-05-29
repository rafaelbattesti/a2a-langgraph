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
