"""MCP server exposing FinBrain's skills as tools for any MCP-compatible client."""

import os
import sys
sys.stdout.reconfigure(encoding="utf-8")

# wbdata builds its default client (and cache directory) at import time, and
# serverless runtimes like Vercel only allow writes under /tmp.
os.environ.setdefault("WBDATA_CACHE_PATH", "/tmp/wbdata_cache/cache")

from dotenv import load_dotenv
load_dotenv()

import functools
from contextlib import asynccontextmanager

import html

import yfinance as yf
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from langfuse import get_client, observe
from mcp.server.mcpserver import MCPServer

# yfinance's default timezone cache also lives under the user cache dir,
# which is read-only on serverless runtimes like Vercel.
yf.set_tz_cache_location("/tmp/yfinance_cache")

from skills.stock_analysis.tools import collect_yfinance_data
from skills.fundamental_analysis.tools import collect_fundamental_indicators
from skills.technical_analysis.tools import collect_technical_indicators
from skills.asset_comparison.tools import compare_assets
from skills.macro_brasil.tools import get_bcb_series, get_ptax_dolar_periodo, get_market_expectations
from skills.macro_global.tools import get_world_bank_indicator, search_world_bank_indicator, compare_countries_latest

mcp = MCPServer("finbrain")

LANGCHAIN_TOOLS = [
    collect_yfinance_data,
    collect_fundamental_indicators,
    collect_technical_indicators,
    compare_assets,
    get_bcb_series,
    get_ptax_dolar_periodo,
    get_market_expectations,
    get_world_bank_indicator,
    search_world_bank_indicator,
    compare_countries_latest,
]


def _with_tracing(func, name: str):
    """Wrap a tool function so each call is traced as a Langfuse tool observation."""
    traced_func = observe(name=name, as_type="tool")(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return traced_func(*args, **kwargs)
        finally:
            get_client().flush()

    return wrapper


for langchain_tool in LANGCHAIN_TOOLS:
    mcp.tool(name=langchain_tool.name)(_with_tracing(langchain_tool.func, langchain_tool.name))

# host="0.0.0.0" (instead of the default "127.0.0.1") stops the DNS-rebinding
# allowlist from rejecting every request whose Host header isn't
# 127.0.0.1/localhost — a problem once this runs behind a real domain
# (Vercel, etc).
mcp_asgi_app = mcp.streamable_http_app(host="0.0.0.0", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


def _render_param_row(param_name: str, schema: dict) -> str:
    param_type = schema.get("type") or " | ".join(
        option.get("type", "any") for option in schema.get("anyOf", [])
    ) or "any"
    required = "default" not in schema
    default = "" if required else html.escape(repr(schema["default"]))
    return (
        "<tr>"
        f"<td><code>{html.escape(param_name)}</code></td>"
        f"<td><code>{html.escape(param_type)}</code></td>"
        f"<td>{'required' if required else default}</td>"
        "</tr>"
    )


def _render_tool_section(tool) -> str:
    param_rows = "\n".join(_render_param_row(name, schema) for name, schema in tool.args.items())
    params_table = (
        f"<table><thead><tr><th>Parameter</th><th>Type</th><th>Default</th></tr></thead>"
        f"<tbody>{param_rows}</tbody></table>"
        if param_rows
        else "<p><em>No parameters.</em></p>"
    )
    return (
        "<section>"
        f"<h3><code>{html.escape(tool.name)}</code></h3>"
        f"<p>{html.escape(tool.description)}</p>"
        f"{params_table}"
        "</section>"
    )


def _render_status_page() -> str:
    tool_sections = "\n".join(_render_tool_section(tool) for tool in LANGCHAIN_TOOLS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>FinBrain MCP</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
code {{ background: #f2f2f2; padding: 0.1rem 0.35rem; border-radius: 4px; }}
section {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem 1.25rem; margin: 1rem 0; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
th, td {{ text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>FinBrain MCP</h1>
<p>MCP server is running. Endpoint: <code>POST /mcp</code> (Streamable HTTP, JSON-RPC).</p>
<p>{len(LANGCHAIN_TOOLS)} tools registered:</p>
{tool_sections}
</body>
</html>"""


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def status_page() -> str:
    """Simple browsable page listing every registered MCP tool, its description and parameters."""
    return _render_status_page()


app.mount("/", mcp_asgi_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
