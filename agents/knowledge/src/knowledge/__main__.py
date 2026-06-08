"""Uvicorn entrypoint for the knowledge A2A agent."""

import logging
import os

import uvicorn
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from starlette.applications import Starlette

from knowledge.agent import KnowledgeRequestHandler
from knowledge.card import build_card, _RPC_PATH

logging.basicConfig(level=logging.INFO)


def main() -> None:
    card = build_card()
    handler = KnowledgeRequestHandler(card)
    routes = [
        *create_agent_card_routes(card),
        *create_jsonrpc_routes(handler.request_handler, rpc_url=_RPC_PATH),
    ]
    app = Starlette(routes=routes)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9999")))


if __name__ == "__main__":
    main()
