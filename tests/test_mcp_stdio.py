"""End-to-end: launch the server over stdio with the official MCP client and call every tool."""
import json
import os
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).parent.parent


def _err(res):  # mcp 1.x: isError, mcp 2.x: is_error
    return getattr(res, "is_error", None) if hasattr(res, "is_error") else res.isError


def _structured(res):
    return getattr(res, "structured_content", None) if hasattr(res, "structured_content") else getattr(res, "structuredContent", None)


async def _run():
    params = StdioServerParameters(command=sys.executable, args=["-m", "lead_leak_check.server"],
                                   env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name for t in (await s.list_tools()).tools}
            assert tools == {"check_pipeline", "check_pipeline_description", "analyze_run_history"}
            res = await s.call_tool("check_pipeline", {"config": json.loads((ROOT / "examples/pipeline.json").read_text())})
            assert not _err(res)
            data = _structured(res) or json.loads(res.content[0].text)
            data = data.get("result", data)
            assert data["risk_score"] == 100
            res = await s.call_tool("check_pipeline_description", {"description": "WhatsApp leads go to a sheet, nobody is assigned"})
            assert not _err(res) and "no-owner" in res.content[0].text
            res = await s.call_tool("analyze_run_history", {"csv_text": (ROOT / "examples/run_history.csv").read_text()})
            assert not _err(res) and "failed-runs" in res.content[0].text
            res = await s.call_tool("check_pipeline_description", {"description": ""})
            assert _err(res)  # helpful error, not a crash
            rules = await s.read_resource("leakcheck://rules")
            assert "no-owner" in rules.contents[0].text


def test_stdio_roundtrip():
    anyio.run(_run)
