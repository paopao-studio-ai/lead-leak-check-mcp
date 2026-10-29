# lead-leak-check (MCP server)

Find where inbound leads are silently dropped between the first touch and the first human reply.

Your Zapier, Make or n8n runs say **Success**. The lead still never hears back: nobody owned the reply, a filter stopped on an empty field, the workflow was switched off for a day, or an AI draft sat unsent. `lead-leak-check` turns a description of your lead pipeline into a ranked list of those risks, each with a concrete fix.

<!-- mcp-name: io.github.paopao-studio-ai/lead-leak-check -->

## Tools

| Tool | Input | Output |
|---|---|---|
| `check_pipeline` | JSON config of your pipeline (sources, storage, routing, response, monitoring…) | Risk score 0–100 and findings ranked high / medium / low / verify |
| `check_pipeline_description` | Plain English, e.g. "Typeform and WhatsApp go to Google Sheets via Zapier, nobody is assigned" | Same report, plus how the text was interpreted |
| `analyze_run_history` | CSV export of run history (`status` column, optional `timestamp`) | Failed and filtered runs, long gaps with no runs, stale workflows |

Resource: `leakcheck://rules` lists all 15 rules with their explanation and fix.

Anything you don't describe is reported as **verify**, never as safe. No network calls, no data leaves your machine.

## Install

```bash
git clone https://github.com/paopao-studio-ai/lead-leak-check-mcp && cd lead-leak-check-mcp
pip install .            # Python 3.10+, works with mcp 1.x and 2.x
```

### Claude Desktop / Cursor / any MCP client

```json
{
  "mcpServers": {
    "lead-leak-check": { "command": "lead-leak-check-mcp" }
  }
}
```

Without installing: `{"command": "python", "args": ["-m", "lead_leak_check.server"], "env": {"PYTHONPATH": "/path/to/lead-leak-check-mcp/src"}}`

### Command line

```bash
lead-leak-check check examples/pipeline.json
lead-leak-check describe "WhatsApp leads land in Google Sheets via Make.com. Nobody is assigned."
lead-leak-check history examples/run_history.csv --interval 30
lead-leak-check --json check examples/pipeline.json
```

## Config shape (all keys optional)

```json
{
  "name": "Typeform -> Google Sheets -> Slack #sales",
  "sources": [{ "type": "web_form", "required_contact_field": false }, { "type": "whatsapp", "logged_to_storage": false }],
  "storage": { "type": "google_sheets", "dedupe": false },
  "routing": { "owner_assignment": "none", "after_hours_coverage": false },
  "response": { "sla_minutes": 30, "auto_ack": true, "ai_drafts": true, "human_send_step": false },
  "monitoring": { "error_alerts": false, "unanswered_lead_alert": false, "run_history_review": "never" },
  "automation": { "platform": "zapier", "plan": "free" },
  "timezone": { "business_tz": "America/New_York", "automation_tz": "UTC" },
  "follow_up": { "sequence": false }
}
```

Example output (top of the report for the config above):

```
# Lead leak risk: Typeform -> Google Sheets -> Slack #sales
Risk score: **100/100** (12 findings)
## 1. [HIGH] Nobody owns the first reply
- Why it leaks: Leads posted to a shared sheet or channel are seen by everyone and answered by no one.
- Fix: Assign an owner per lead (round robin or fixed) at the moment it is created, and name them in the notification.
```

## Fix the #1 finding for free

The most common high-severity finding is "no alert when a lead goes unanswered". The free **n8n missed-lead heartbeat** template checks your sheet or CRM every 5 minutes and pings Slack, Discord or any webhook when a lead waits past your SLA. <!-- TODO: link the template once it is published on n8n.io -->

## Want a human to map it?

Paopao Studio runs a fixed-price **Lead Leak Check ($197)**: a written leak map of 1–2 lead workflows, credited in full to a Starter build within 30 days. Free screenshot triage by email.
→ https://paopao-studio.pages.dev/?utm_source=github&utm_medium=oss&utm_campaign=lead_leak_1029

## Develop

```bash
pip install -e ".[test]"
pytest -q          # rule tests + an end-to-end stdio round trip with the official MCP client
```

## License

MIT, see [LICENSE](LICENSE).
