"""Minimal A2A server scaffolding shared by every agent.

An agent supplies an async ``handler(payload: dict) -> dict``; this module wraps
it in an A2A ``AgentExecutor`` that carries JSON as the message text.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message

from . import config

Handler = Callable[[dict], Awaitable[dict]]


def build_card(
    *, name: str, description: str, skill_id: str, public_url: str, version: str = "0.1.0"
) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        url=public_url,
        version=version,
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[
            AgentSkill(
                id=skill_id,
                name=name,
                description=description,
                tags=["thesis", "research"],
            )
        ],
    )


class _JsonExecutor(AgentExecutor):
    def __init__(self, handler: Handler) -> None:
        self._handler = handler

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raw = context.get_user_input() or "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"topic": raw}
        result = await self._handler(payload)
        await event_queue.enqueue_event(new_agent_text_message(json.dumps(result)))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancellation is not supported in the MVP")


def build_app(card: AgentCard, handler: Handler):
    request_handler = DefaultRequestHandler(
        agent_executor=_JsonExecutor(handler),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(agent_card=card, http_handler=request_handler).build()


def serve(card: AgentCard, handler: Handler) -> None:
    uvicorn.run(build_app(card, handler), host="0.0.0.0", port=config.PORT)
