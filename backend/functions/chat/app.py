"""chat
POST /chat
Answers a follow-up question about a document that has already been
analyzed. Grounded entirely in that document's stored extracted text.
Calls Groq's OpenAI-compatible chat completions endpoint directly with
Python's built-in urllib — same approach as explain_document, no extra
dependency. Each Lambda invocation is stateless: the client sends the
prior conversation back with every request, and it's replayed into the
messages array alongside the new question.
"""

import json
import os
import urllib.error
import urllib.request

from clients import dynamodb_table
from prompts import build_system_prompt

RESULTS_TABLE = os.environ["RESULTS_TABLE"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL_ID = os.environ["GROQ_MODEL_ID"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 30

# Cap how much prior conversation gets replayed to the model each turn —
# keeps the request bounded regardless of how long a chat runs.
MAX_HISTORY_MESSAGES = 16

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def _call_groq(messages: list[dict]) -> str:
    """Sends a full message list (system + history + new question) to
    Groq and returns the reply text. Split out as its own function so
    tests can monkeypatch it instead of hitting the real Groq API."""
    payload = {
        "model": GROQ_MODEL_ID,
        "messages": messages,
        "max_tokens": 500,
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
    try:
        body = json.loads(event.get("body") or "{}")
        document_id = body.get("documentId")
        question = (body.get("question") or "").strip()
        history = body.get("history") or []

        if not document_id or not question:
            return _error(400, "documentId and question are required.")

        table = dynamodb_table(RESULTS_TABLE)
        item = table.get_item(Key={"documentId": document_id}).get("Item")

        if not item or item.get("status") != "complete":
            return _error(404, "No completed analysis found for this document.")

        raw_text = item.get("rawText", "")
        if not raw_text.strip():
            return _error(400, "This document has no stored text to answer questions from.")

        messages = _build_messages(raw_text, history, question)
        answer = _call_groq(messages).strip()

        return {
            "statusCode": 200,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({"answer": answer}),
        }

    except Exception as exc:  # noqa: BLE001
        return _error(500, str(exc))


def _build_messages(raw_text: str, history: list[dict], question: str) -> list[dict]:
    messages = [{"role": "system", "content": build_system_prompt(raw_text)}]
    for turn in history[-MAX_HISTORY_MESSAGES:]:
        role = turn.get("role")
        text = turn.get("text", "")
        if role in ("user", "assistant") and text:
            messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": question})
    return messages


def _error(status_code: int, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }
