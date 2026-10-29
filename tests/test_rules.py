import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lead_leak_check import analyze_history, check_config, check_description

EX = Path(__file__).parent.parent / "examples"


def ids(rep, sev=None):
    return {f.id for f in rep.findings if sev is None or f.severity == sev}


def test_leaky_example_flags_core_risks():
    rep = check_config(json.loads((EX / "pipeline.json").read_text()))
    high = ids(rep, "high")
    assert {"no-owner", "no-sla-alert", "no-error-alert", "chat-not-logged"} <= high
    assert {"silent-filters", "ai-draft-unsent", "tz-mismatch", "free-plan-limits", "no-after-hours"} <= ids(rep, "medium")
    assert "no-auto-ack" not in ids(rep)  # auto_ack is true
    d = rep.as_dict()
    assert d["risk_score"] == 100 and d["findings"][0]["severity"] == "high"
    assert "paopao-studio" in d["report_markdown"]


def test_safe_pipeline_is_clean():
    cfg = {
        "name": "good",
        "sources": [{"type": "web_form", "required_contact_field": True}, {"type": "whatsapp", "logged_to_storage": True}],
        "storage": {"type": "crm", "dedupe": True},
        "routing": {"owner_assignment": "round_robin", "after_hours_coverage": True},
        "response": {"sla_minutes": 15, "auto_ack": True, "ai_drafts": True, "human_send_step": True},
        "monitoring": {"error_alerts": True, "unanswered_lead_alert": True, "run_history_review": "weekly"},
        "automation": {"platform": "n8n", "plan": "self_hosted"},
        "timezone": {"business_tz": "Europe/Berlin", "automation_tz": "Europe/Berlin"},
        "follow_up": {"sequence": True},
    }
    rep = check_config(cfg)
    assert rep.findings == [] and rep.score == 0


def test_empty_config_is_all_verify_not_clean():
    rep = check_config({})
    assert rep.findings and all(f.severity == "verify" for f in rep.findings)
    assert rep.notes


def test_bad_sla_value():
    rep = check_config({"response": {"sla_minutes": "soon"}})
    assert "no-sla" in ids(rep, "medium")


def test_description_parsing():
    text = ("Leads come from a Typeform and WhatsApp into Google Sheets via Zapier on the free plan. "
            "Nobody is assigned; Slack pings #sales. ChatGPT drafts replies. No error alerts.")
    rep = check_description(text)
    assert {"no-owner", "no-error-alert", "free-plan-limits"} <= ids(rep, "high") | ids(rep, "medium")
    assert "ai-draft-unsent" in ids(rep)  # AI drafts but no send step stated
    assert any("Interpreted as" in n for n in rep.notes)
    assert "platform=zapier" in rep.notes[-1]


def test_description_does_not_misread_words():
    rep = check_description("We use n8n on our platform and store information in HubSpot. Round robin assignment.")
    assert "no-owner" not in ids(rep)
    assert "platform=n8n" in rep.notes[-1]
    assert "web_form" not in rep.notes[-1]  # 'platform'/'information' must not count as 'form'


def test_description_empty_raises():
    with pytest.raises(ValueError):
        check_description("   ")


def test_history():
    now = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
    rep = analyze_history((EX / "run_history.csv").read_text(), now=now)
    assert "failed-runs" in ids(rep, "high")  # 3 failures
    assert "filtered-runs" in ids(rep)
    assert "run-gap" in ids(rep)  # ~45h gap
    assert "stale" in ids(rep, "high")  # last run a week before `now`


def test_history_requires_status_column():
    with pytest.raises(ValueError, match="status"):
        analyze_history("a,b\n1,2\n")
