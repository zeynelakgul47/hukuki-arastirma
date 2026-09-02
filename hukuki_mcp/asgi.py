"""HTTP / Streamable MCP for Grok.com and ChatGPT custom connectors."""
from __future__ import annotations

import os

from hukuki_mcp.server import get_mcp_app

mcp = get_mcp_app()
app = mcp.http_app(path="/mcp")


def run_http() -> None:
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("hukuki_mcp.asgi:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run_http()
