"""A2A client helper for typed structured payload contracts."""

from __future__ import annotations

from typing import TypeVar
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Role, SendMessageRequest
from a2a.utils import TransportProtocol
from pydantic import BaseModel

from .a2a_payloads import PayloadContractError, message_from_model, model_from_message

T = TypeVar("T", bound=BaseModel)


async def call_agent(
    base_url: str, payload: BaseModel, response_model: type[T], timeout: float = 300.0
) -> T:
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        client_config = ClientConfig(
            streaming=False,
            supported_protocol_bindings=[TransportProtocol.JSONRPC],
            httpx_client=http_client,
        )
        client = await create_client(base_url, client_config)
        request = SendMessageRequest(
            message=message_from_model(payload, role=Role.ROLE_USER)
        )
        request.message.message_id = uuid4().hex
        message: Message | None = None
        async for response in client.send_message(request):
            if response.WhichOneof("payload") == "message":
                message = response.message

        if message is None:
            raise RuntimeError("A2A peer returned no message response")
        try:
            return model_from_message(message, response_model)
        except PayloadContractError as exc:
            raise RuntimeError(f"A2A peer returned invalid payload: {exc}") from exc
