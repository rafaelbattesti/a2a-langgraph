"""A2A adapter layer.

Carries typed Pydantic contracts as A2A structured data parts, builds the agent
card and Starlette app, and provides the typed client. Capability-agnostic.
"""

from __future__ import annotations

from .client import call_agent
from .payloads import (
    JSON_MEDIA_TYPE,
    PayloadContractError,
    message_from_model,
    model_from_message,
)
from .server import CONTRACT_EXTENSION_URI, build_app, build_card, serve

__all__ = [
    "CONTRACT_EXTENSION_URI",
    "JSON_MEDIA_TYPE",
    "PayloadContractError",
    "build_app",
    "build_card",
    "call_agent",
    "message_from_model",
    "model_from_message",
    "serve",
]
