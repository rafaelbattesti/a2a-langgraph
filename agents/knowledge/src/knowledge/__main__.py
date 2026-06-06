"""Uvicorn entrypoint: minimal HTTP server running the knowledge agent's graph."""

import logging
import os

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from knowledge.graph import AGENT_NAME, build_graph

logging.basicConfig(level=logging.INFO)

_graph = build_graph()


async def root(_request: Request) -> JSONResponse:
    result = _graph.invoke({"name": AGENT_NAME})
    return JSONResponse({"agent": result["name"]})


app = Starlette(routes=[Route("/", root, methods=["GET"])])


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9999")))


if __name__ == "__main__":
    main()
