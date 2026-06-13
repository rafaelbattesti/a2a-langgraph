from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
  create_agent_card_routes,
  create_jsonrpc_routes,
  create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from bastion.executor import BastionAgentExecutor

CHAT_UI_ORIGIN = "http://localhost:3000"


def create_agent_card(base_url: str) -> AgentCard:
  skill = AgentSkill(
    id="payload_echo",
    name="Payload Echo",
    description="Returns the A2A payload received by the stub agent.",
    input_modes=["text/plain"],
    output_modes=["application/json"],
    tags=["a2a", "stub"],
    examples=["Show me the payload you received."],
  )

  return AgentCard(
    name="Bastion Stub Agent",
    description="Stub A2A agent that returns the payload it receives.",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    supported_interfaces=[
      AgentInterface(protocol_binding="JSONRPC", url=base_url),
      AgentInterface(protocol_binding="HTTP+JSON", url=base_url),
    ],
    skills=[skill],
  )


def create_app(base_url: str) -> Starlette:
  public_agent_card = create_agent_card(base_url)
  request_handler = DefaultRequestHandler(
    agent_executor=BastionAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=public_agent_card,
  )

  routes = []
  routes.extend(create_agent_card_routes(public_agent_card))
  routes.extend(create_jsonrpc_routes(request_handler, "/"))
  routes.extend(create_rest_routes(request_handler))

  app = Starlette(routes=routes)
  app.add_middleware(
    CORSMiddleware,
    allow_origins=[CHAT_UI_ORIGIN],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["A2A-Version", "A2A-Extensions", "Content-Type", "Accept"],
  )
  return app


agent_card = create_agent_card("http://localhost:9999")
app = create_app("http://localhost:9999")
