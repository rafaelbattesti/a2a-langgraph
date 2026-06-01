"""Versioned, transport-neutral contract primitives.

Capability-agnostic: the contract *mechanism* (base model and version), not any
specific service's payloads.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

CONTRACT_VERSION = "1.0.0"


class ContractModel(BaseModel):
    """Base model for versioned agent-to-agent payload contracts."""

    model_config = ConfigDict(extra="forbid")
