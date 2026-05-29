# A2A Architecture Remediation Plan

Status: the first remediation slice has been implemented for the current
internal agent boundaries. The remaining items are follow-on platform work.

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
