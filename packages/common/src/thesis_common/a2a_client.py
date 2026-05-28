"""A2A client helper: send a JSON payload to a peer agent, get a JSON dict back."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)
from a2a.utils import get_message_text


def _text_from_message(message: Message) -> str:
    text = get_message_text(message)
    if text:
        return text
    return "".join(
        p.root.text for p in message.parts if isinstance(p.root, TextPart)
    )


def _extract(response: Any) -> dict:
    root = response.root
    if hasattr(root, "error") and root.error is not None:
        raise RuntimeError(f"A2A peer returned an error: {root.error}")

    result = root.result
    text = ""
    if isinstance(result, Message):
        text = _text_from_message(result)
    else:  # Task
        if getattr(result, "status", None) and result.status.message:
            text = _text_from_message(result.status.message)
        elif getattr(result, "history", None):
            text = _text_from_message(result.history[-1])
        elif getattr(result, "artifacts", None):
            for artifact in result.artifacts:
                text += "".join(
                    p.root.text for p in artifact.parts if isinstance(p.root, TextPart)
                )

    if not text:
        raise RuntimeError("A2A peer returned an empty response")
    return json.loads(text)


async def call_agent(base_url: str, payload: dict, timeout: float = 300.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=base_url)
        card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=http_client, agent_card=card)
        message = Message(
            role=Role.user,
            message_id=uuid4().hex,
            parts=[Part(root=TextPart(text=json.dumps(payload)))],
        )
        request = SendMessageRequest(
            id=uuid4().hex, params=MessageSendParams(message=message)
        )
        response = await client.send_message(request)
        return _extract(response)
