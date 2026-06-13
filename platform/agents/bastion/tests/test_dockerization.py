import pathlib
import re
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[2]


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_pattern(
    test_case: unittest.TestCase,
    text: str,
    pattern: str,
) -> None:
    test_case.assertRegex(text, re.compile(pattern, re.MULTILINE))


class BastionDockerizationTests(unittest.TestCase):
    def test_dockerfile_builds_and_runs_bastion_server(self) -> None:
        dockerfile_path = PROJECT_ROOT / "Dockerfile"

        self.assertTrue(dockerfile_path.exists())

        dockerfile = read_text(dockerfile_path)

        assert_contains_pattern(self, dockerfile, r"FROM\s+ghcr\.io/astral-sh/uv:python3\.14")
        self.assertIn("COPY pyproject.toml uv.lock", dockerfile)
        self.assertIn("uv sync --locked --no-dev", dockerfile)
        self.assertIn("COPY src ./src", dockerfile)
        self.assertIn('ENV PATH="/app/.venv/bin:$PATH"', dockerfile)
        self.assertIn("EXPOSE 9999", dockerfile)
        self.assertIn(
            'CMD ["uvicorn", "bastion.server:app", "--host", "0.0.0.0", "--port", "9999"]',
            dockerfile,
        )

    def test_dockerignore_excludes_local_only_inputs(self) -> None:
        dockerignore_path = PROJECT_ROOT / ".dockerignore"

        self.assertTrue(dockerignore_path.exists())

        dockerignore = read_text(dockerignore_path)

        for pattern in [
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            ".mypy_cache",
            "dist",
            "build",
            "*.egg-info",
            ".env",
            ".env*.local",
            ".git",
            ".agents",
            ".claude",
            "*.log",
        ]:
            assert_contains_pattern(
                self,
                dockerignore,
                rf"(^|\n){re.escape(pattern)}(/)?(\n|$)",
            )

    def test_root_compose_defines_bastion_service(self) -> None:
        compose = read_text(REPO_ROOT / "docker-compose.yaml")

        assert_contains_pattern(self, compose, r"services:\s*\n(?:.|\n)*^\s{2}bastion:")
        self.assertIn("context: ./platform/agents/bastion", compose)
        self.assertIn("dockerfile: Dockerfile", compose)
        self.assertIn("image: oss-multi-agent-chatbot-bastion", compose)
        self.assertIn('"9999:9999"', compose)

    def test_chat_ui_uses_localhost_for_browser_facing_a2a_url(self) -> None:
        compose = read_text(REPO_ROOT / "docker-compose.yaml")

        self.assertIn("NEXT_PUBLIC_A2A_SERVER_URL: http://localhost:9999", compose)
        self.assertNotIn("NEXT_PUBLIC_A2A_SERVER_URL: http://bastion:9999", compose)

    def test_bastion_agent_card_uses_localhost_url(self) -> None:
        from bastion.server import agent_card

        self.assertEqual(agent_card.supported_interfaces[0].url, "http://localhost:9999")


if __name__ == "__main__":
    unittest.main()
