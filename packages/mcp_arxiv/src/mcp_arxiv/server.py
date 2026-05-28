"""MCP server wrapping the public arXiv API. Exposes a single `arxiv_search` tool."""

from __future__ import annotations

import os

import arxiv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "arxiv",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


@mcp.tool()
def arxiv_search(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv and return matching papers (title, abstract, url)."""
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers: list[dict] = []
    for result in client.results(search):
        papers.append(
            {
                "title": result.title.strip(),
                "summary": result.summary.strip(),
                "url": result.entry_id,
            }
        )
    return papers


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
