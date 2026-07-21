"""Connect to the FinBrain MCP server and list its available tools."""

import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8")

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "https://fin-brain-git-main-renansantosmendes-projects.vercel.app/mcp"


async def main(url: str) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            print(f"{len(tools.tools)} tools available at {url}:\n")
            for t in tools.tools:
                print(f"- {t.name}: {t.description}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else MCP_URL
    asyncio.run(main(url))
