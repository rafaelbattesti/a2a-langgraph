import json
import pathlib
import sys
import tomllib
import unittest

from starlette.testclient import TestClient


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class ProjectMetadataTests(unittest.TestCase):
    def test_project_is_uv_managed_with_pinned_dependencies(self) -> None:
        pyproject = PROJECT_ROOT / "pyproject.toml"
        lockfile = PROJECT_ROOT / "uv.lock"

        self.assertTrue(pyproject.exists())
        self.assertTrue(lockfile.exists())

        data = tomllib.loads(pyproject.read_text())
        dependencies = data["project"]["dependencies"]

        self.assertIn("langgraph==1.2.5", dependencies)
        self.assertIn("a2a-sdk[http-server]==1.1.0", dependencies)


class GraphTests(unittest.TestCase):
    def test_graph_encapsulates_received_payload_in_response_text(self) -> None:
        from bastion.graph import run_stub_graph

        payload = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "ping"}],
                },
            },
        }

        result = run_stub_graph(payload)

        self.assertEqual(
            json.loads(result["response_text"]),
            {"received_payload": payload},
        )


class A2AServerTests(unittest.TestCase):
    def test_server_exposes_agent_card_discovery_and_jsonrpc_routes(self) -> None:
        from bastion.server import agent_card, app

        route_paths = {route.path for route in app.routes}

        self.assertEqual(agent_card.name, "Bastion Stub Agent")
        self.assertIn("/.well-known/agent-card.json", route_paths)
        self.assertIn("/", route_paths)

    def test_server_exposes_a2a_rest_routes(self) -> None:
        from bastion.server import agent_card, app

        route_paths = {route.path for route in app.routes}
        protocol_bindings = {
            interface.protocol_binding for interface in agent_card.supported_interfaces
        }

        self.assertIn("/message:send", route_paths)
        self.assertIn("/message:stream", route_paths)
        self.assertIn("JSONRPC", protocol_bindings)
        self.assertIn("HTTP+JSON", protocol_bindings)

    def test_cors_preflight_allows_chat_ui_for_agent_card_and_rest_routes(self) -> None:
        from bastion.server import app

        client = TestClient(app)

        for path, method in [
            ("/.well-known/agent-card.json", "GET"),
            ("/message:send", "POST"),
            ("/message:stream", "POST"),
        ]:
            response = client.options(
                path,
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method,
                    "Access-Control-Request-Headers": "A2A-Version, Content-Type, Accept",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers["access-control-allow-origin"],
                "http://localhost:3000",
            )
            self.assertIn(method, response.headers["access-control-allow-methods"])
            self.assertIn(
                "A2A-Version",
                response.headers["access-control-allow-headers"],
            )

    def test_rest_message_send_response_contains_payload_received_by_agent(self) -> None:
        from bastion.server import app

        client = TestClient(app)
        payload = {
            "message": {
                "messageId": "message-1",
                "role": "ROLE_USER",
                "parts": [{"text": "hello", "mediaType": "text/plain"}],
            },
        }

        response = client.post(
            "/message:send",
            json=payload,
            headers={
                "A2A-Version": "1.0",
                "Origin": "http://localhost:3000",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        response_text = body["task"]["status"]["message"]["parts"][0]["text"]
        received_payload = json.loads(response_text)["received_payload"]

        self.assertEqual(received_payload["message_id"], "message-1")
        self.assertEqual(received_payload["role"], "ROLE_USER")
        self.assertEqual(
            received_payload["parts"],
            [{"text": "hello", "media_type": "text/plain"}],
        )

    def test_executor_response_text_contains_payload_received_by_agent(self) -> None:
        from bastion.executor import build_response_message_text

        payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "hello"}],
            },
        }

        self.assertEqual(
            json.loads(build_response_message_text(payload)),
            {"received_payload": payload},
        )


if __name__ == "__main__":
    unittest.main()
