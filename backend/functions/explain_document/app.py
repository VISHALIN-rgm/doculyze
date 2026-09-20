"""explain_document
Step Functions task. Sends the extracted document text to Groq and
parses the structured JSON explanation back out. Works the same way no
matter what kind of document was uploaded.

Calls Groq's OpenAI-compatible chat completions endpoint directly with
Python's built-in urllib — no extra dependency beyond the standard
library. This keeps the deployment package tiny and fast to build on
any platform, and swapping GROQ_MODEL_ID is a config change, not a
code change.
"""

import json
import os
import re
import urllib.error
import urllib.request

from prompts import SYSTEM_PROMPT, build_user_prompt

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL_ID = os.environ["GROQ_MODEL_ID"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 60


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Sends a single system+user turn to Groq and returns the model's
    reply text. Split out as its own function so tests can monkeypatch
    it instead of hitting the real Groq API."""
    payload = {
        "model": GROQ_MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1500,
        "temperature": 0.3,
    }
    request = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Groq API: {exc.reason}") from exc

    return body["choices"][0]["message"]["content"]


def handler(event, context):
    extraction = event["extraction"]
    document_text = extraction.get("text", "")
    key_value_pairs = extraction.get("keyValuePairs", [])
    lines = extraction.get("lines", [])

    if not document_text.strip():
        return {
            "documentType": "unknown",
            "summary": "No readable text was found in this document.",
            "keyTerms": [],
            "redFlags": [],
            "actionItems": ["Try re-uploading a clearer scan or a text-based file."],
        }

    user_prompt = build_user_prompt(document_text, key_value_pairs)
    model_text = _call_groq(SYSTEM_PROMPT, user_prompt)

    parsed = _safe_parse_json(model_text)
    red_flags = _attach_locations(parsed.get("red_flags", []), lines)

    return {
        "documentType": parsed.get("document_type", "document"),
        "summary": parsed.get("summary", ""),
        "keyTerms": parsed.get("key_terms", []),
        "redFlags": red_flags,
        "actionItems": parsed.get("action_items", []),
    }


def _safe_parse_json(text: str) -> dict:
    """Models are instructed to return raw JSON, but strip code fences
    defensively in case one wraps the response anyway."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "document_type": "document",
            "summary": text[:800],
            "key_terms": [],
            "red_flags": [],
            "action_items": [],
        }


def _attach_locations(red_flags: list[dict], lines: list[dict]) -> list[dict]:
    """For each red flag with a "quote", find the line(s) it appears in
    and attach their position as "location" — a list of
    {page, boundingBox} entries (more than one when a quote spans two
    consecutive lines). Flags with no quote, or a quote that can't be
    matched to any line, are returned unchanged with no "location"."""
    normalized_lines = [(_normalize(line.get("text", "")), line) for line in lines]

    result = []
    for flag in red_flags:
        out = {
            "issue": flag.get("issue", ""),
            "whyItMatters": flag.get("why_it_matters", flag.get("whyItMatters", "")),
            "severity": flag.get("severity", "low"),
        }
        quote = flag.get("quote")
        if quote:
            location = _locate_quote(quote, normalized_lines)
            if location:
                out["location"] = location
        result.append(out)
    return result


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _locate_quote(quote: str, normalized_lines: list[tuple[str, dict]]) -> list[dict] | None:
    quote_norm = _normalize(quote)
    if not quote_norm:
        return None

    # Priority 1: the quote is fully contained within a single detected
    # line — the common case, and the most reliable match.
    for line_norm, line in normalized_lines:
        if line_norm and quote_norm in line_norm:
            return [_to_location(line)]

    # Priority 2: the quote spans two consecutive lines (Textract splits
    # lines by visual position, which doesn't always align with where a
    # sentence the model quoted actually breaks).
    for i in range(len(normalized_lines) - 1):
        line_a_norm, line_a = normalized_lines[i]
        line_b_norm, line_b = normalized_lines[i + 1]
        combined = f"{line_a_norm} {line_b_norm}"
        if quote_norm in combined:
            return [_to_location(line_a), _to_location(line_b)]

    # Priority 3: a single line covers most of the quote (near-exact
    # match with minor OCR/formatting differences) — only accepted when
    # the line makes up a large share of the quote's length, so a short
    # unrelated line snippet can't falsely "match" a long quote.
    for line_norm, line in normalized_lines:
        if line_norm and line_norm in quote_norm and len(line_norm) >= 0.8 * len(quote_norm):
            return [_to_location(line)]

    return None


def _to_location(line: dict) -> dict:
    return {"page": line.get("page", 1), "boundingBox": line.get("boundingBox", {})}
