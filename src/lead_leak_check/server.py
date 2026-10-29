"""MCP server exposing lead-leak-check over stdio.

Run:  lead-leak-check-mcp            (after pip install)
or:   python -m lead_leak_check.server
"""
from __future__ import annotations

import json
from typing import Any

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

from .rules import RULES, analyze_history, check_config, check_description

mcp = FastMCP(
    "lead-leak-check",
    instructions=(
        "Finds where inbound leads are silently dropped between the first touch and the first human reply. "
        "Use check_pipeline for a structured config, check_pipeline_description for plain English, and "
        "analyze_run_history for a Zapier/Make/n8n run-history CSV export."
    ),
)


@mcp.tool()
def check_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    """Check a structured lead-pipeline config and return a ranked leak-risk list.

    Keys (all optional; omitted ones are reported as 'verify'):
      name; sources: [{type: web_form|whatsapp|email|ads_lead_form|instagram_dm|..., required_contact_field: bool, logged_to_storage: bool}];
      storage: {type: google_sheets|crm|airtable|none, dedupe: bool};
      routing: {owner_assignment: round_robin|fixed|none, after_hours_coverage: bool};
      response: {sla_minutes: int, auto_ack: bool, ai_drafts: bool, human_send_step: bool};
      monitoring: {error_alerts: bool, unanswered_lead_alert: bool, run_history_review: weekly|never};
      automation: {platform: zapier|make|n8n, plan: free|paid}; timezone: {business_tz, automation_tz};
      follow_up: {sequence: bool}
    """
    if isinstance(config, str):  # tolerate clients that send JSON as a string
        config = json.loads(config)
    return check_config(config).as_dict()


@mcp.tool()
def check_pipeline_description(description: str) -> dict[str, Any]:
    """Check a plain-English description of how leads arrive, where they are stored, who replies and what alerts exist."""
    return check_description(description).as_dict()


@mcp.tool()
def analyze_run_history(csv_text: str, expected_interval_minutes: float | None = None) -> dict[str, Any]:
    """Analyze a run-history CSV (needs a status column; a timestamp column enables gap and stale checks).

    Flags failed/halted runs, filtered runs that end without errors, long gaps with no runs, and a stale last run.
    """
    return analyze_history(csv_text, expected_interval_minutes).as_dict()


@mcp.resource("leakcheck://rules")
def list_rules() -> str:
    """All leak rules with severity, explanation and fix."""
    return json.dumps([{"id": r.id, "severity": r.severity, "title": r.title, "why": r.why, "fix": r.fix} for r in RULES], indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
