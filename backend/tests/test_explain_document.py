import json

from conftest import load_function_module

explain_document_app = load_function_module("explain_document")

_safe_parse_json = explain_document_app._safe_parse_json


def test_parses_clean_json():
    raw = json.dumps({"document_type": "lease", "summary": "A lease.", "key_terms": [], "red_flags": [], "action_items": []})
    parsed = _safe_parse_json(raw)
    assert parsed["document_type"] == "lease"


def test_strips_markdown_fences():
    raw = "```json\n" + json.dumps({"document_type": "bill", "summary": "An electricity bill."}) + "\n```"
    parsed = _safe_parse_json(raw)
    assert parsed["document_type"] == "bill"


def test_falls_back_gracefully_on_bad_json():
    parsed = _safe_parse_json("not json at all")
    assert parsed["document_type"] == "document"
    assert "not json at all" in parsed["summary"]


def test_handler_calls_groq_directly(monkeypatch):
    # This is the same call shape regardless of which Groq model
    # GROQ_MODEL_ID points at — no branching per model.
    response_json = json.dumps(
        {
            "document_type": "rental agreement",
            "summary": "A 12-month lease.",
            "key_terms": ["12-month term"],
            "red_flags": [],
            "action_items": ["Review the deposit clause."],
        }
    )
    captured = {}

    def fake_call_groq(system_prompt, user_prompt):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return response_json

    monkeypatch.setattr(explain_document_app, "_call_groq", fake_call_groq)

    event = {"extraction": {"text": "This lease runs for 12 months...", "keyValuePairs": []}}
    result = explain_document_app.handler(event, None)

    assert result["documentType"] == "rental agreement"
    assert result["actionItems"] == ["Review the deposit clause."]

    assert captured["system_prompt"] == explain_document_app.SYSTEM_PROMPT
    assert "This lease runs for 12 months" in captured["user_prompt"]


def test_handler_short_circuits_on_empty_text(monkeypatch):
    calls = []
    monkeypatch.setattr(explain_document_app, "_call_groq", lambda *a: calls.append(a) or "should not be called")

    result = explain_document_app.handler({"extraction": {"text": "   ", "keyValuePairs": []}}, None)

    assert result["documentType"] == "unknown"
    assert calls == []


def _make_line(text, page=1, left=0.1, top=0.1, width=0.5, height=0.02):
    return {"text": text, "page": page, "boundingBox": {"left": left, "top": top, "width": width, "height": height}}


def test_locate_quote_matches_single_line():
    lines = [
        (explain_document_app._normalize("Tenant may not sublet without written consent"), _make_line("Tenant may not sublet without written consent", top=0.3)),
    ]
    result = explain_document_app._locate_quote("sublet without written consent", lines)
    assert result == [{"page": 1, "boundingBox": lines[0][1]["boundingBox"]}]


def test_locate_quote_matches_across_two_lines():
    line_a = _make_line("a late fee of $75 will be", page=2, top=0.5)
    line_b = _make_line("charged for any payment after the 5th", page=2, top=0.53)
    normalized = [(explain_document_app._normalize(line_a["text"]), line_a), (explain_document_app._normalize(line_b["text"]), line_b)]
    result = explain_document_app._locate_quote("a late fee of $75 will be charged for any payment", normalized)
    assert result == [
        {"page": 2, "boundingBox": line_a["boundingBox"]},
        {"page": 2, "boundingBox": line_b["boundingBox"]},
    ]


def test_locate_quote_returns_none_when_not_found():
    lines = [(explain_document_app._normalize("Completely unrelated text"), _make_line("Completely unrelated text"))]
    assert explain_document_app._locate_quote("this phrase is nowhere in the document", lines) is None


def test_attach_locations_omits_location_when_quote_unmatched():
    lines = [_make_line("Rent is due on the 1st of each month", top=0.2)]
    red_flags = [
        {"issue": "Late fee", "why_it_matters": "Costs money", "severity": "medium", "quote": "Rent is due on the 1st"},
        {"issue": "Auto-renewal", "why_it_matters": "Easy to miss", "severity": "high", "quote": "a phrase that does not appear anywhere"},
        {"issue": "No quote given", "why_it_matters": "Still shown", "severity": "low"},
    ]
    result = explain_document_app._attach_locations(red_flags, lines)

    assert result[0]["issue"] == "Late fee"
    assert "location" in result[0]
    assert result[1]["issue"] == "Auto-renewal"
    assert "location" not in result[1]
    assert result[2]["issue"] == "No quote given"
    assert "location" not in result[2]
    # why_it_matters is normalized to camelCase for the frontend
    assert result[0]["whyItMatters"] == "Costs money"
