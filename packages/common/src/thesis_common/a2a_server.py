"""Minimal A2A server scaffolding shared by every agent.

An agent supplies an async ``handler(payload: dict) -> dict``; this module wraps
it in an A2A ``AgentExecutor`` that carries JSON as the message text.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from uuid import uuid4

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
)
from a2a.utils import DEFAULT_RPC_URL, TransportProtocol
from starlette.applications import Starlette

from . import config

Handler = Callable[[dict], Awaitable[dict]]


def build_card(
    *, name: str, description: str, skill_id: str, public_url: str, version: str = "0.1.0"
) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
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
        supported_interfaces=[
            AgentInterface(protocol_binding=TransportProtocol.JSONRPC, url=public_url)
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
        message = Message(
            message_id=uuid4().hex,
            role=Role.ROLE_AGENT,
            parts=[Part(text=json.dumps(result))],
        )
        await event_queue.enqueue_event(message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancellation is not supported in the MVP")


def build_app(card: AgentCard, handler: Handler):
    request_handler = DefaultRequestHandler(
        agent_executor=_JsonExecutor(handler),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(
        request_handler, DEFAULT_RPC_URL
    )
    return Starlette(routes=routes)


def serve(card: AgentCard, handler: Handler) -> None:
    uvicorn.run(build_app(card, handler), host="0.0.0.0", port=config.PORT)
