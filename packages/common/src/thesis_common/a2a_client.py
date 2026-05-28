"""A2A client helper: send a JSON payload to a peer agent, get a JSON dict back."""

from __future__ import annotations

import json
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest
from a2a.utils import TransportProtocol


def _text_from_message(message: Message) -> str:
    return "".join(part.text for part in message.parts if part.text)


async def call_agent(base_url: str, payload: dict, timeout: float = 300.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        client_config = ClientConfig(
            streaming=False,
            supported_protocol_bindings=[TransportProtocol.JSONRPC],
            httpx_client=http_client,
        )
        client = await create_client(base_url, client_config)
        request = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex,
                role=Role.ROLE_USER,
                parts=[Part(text=json.dumps(payload))],
            )
        )
        text = ""
        async for response in client.send_message(request):
            if response.WhichOneof("payload") == "message":
                text = _text_from_message(response.message)

        if not text:
            raise RuntimeError("A2A peer returned an empty response")
        return json.loads(text)
