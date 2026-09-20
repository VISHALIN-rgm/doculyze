import json

from conftest import load_function_module

chat_app = load_function_module("chat")


class _FakeTable:
    def __init__(self, item=None):
        self._item = item

    def get_item(self, Key):
        if self._item and self._item.get("documentId") == Key["documentId"]:
            return {"Item": self._item}
        return {}


def _event(body):
    return {"body": json.dumps(body)}


def test_returns_400_when_question_missing(monkeypatch):
    result = chat_app.handler(_event({"documentId": "doc1"}), None)
    assert result["statusCode"] == 400


def test_returns_404_when_document_not_found(monkeypatch):
    monkeypatch.setattr(chat_app, "dynamodb_table", lambda name: _FakeTable(item=None))
    result = chat_app.handler(_event({"documentId": "missing", "question": "What is this?"}), None)
    assert result["statusCode"] == 404


def test_returns_404_when_document_not_complete(monkeypatch):
    monkeypatch.setattr(
        chat_app, "dynamodb_table", lambda name: _FakeTable(item={"documentId": "doc1", "status": "processing"})
    )
    result = chat_app.handler(_event({"documentId": "doc1", "question": "What is this?"}), None)
    assert result["statusCode"] == 404


def test_answers_question_grounded_in_stored_text(monkeypatch):
    fake_table = _FakeTable(
        item={"documentId": "doc1", "status": "complete", "rawText": "This lease runs for 12 months."}
    )
    captured = {}

    def fake_call_groq(messages):
        captured["messages"] = messages
        return "The lease runs for 12 months."

    monkeypatch.setattr(chat_app, "dynamodb_table", lambda name: fake_table)
    monkeypatch.setattr(chat_app, "_call_groq", fake_call_groq)

    result = chat_app.handler(_event({"documentId": "doc1", "question": "How long is the lease?"}), None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["answer"] == "The lease runs for 12 months."

    messages = captured["messages"]
    assert messages[0]["role"] == "system"
    assert "This lease runs for 12 months." in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "How long is the lease?"}
    assert len(messages) == 2  # system + the new question, no prior history


def test_includes_prior_history_in_the_conversation(monkeypatch):
    fake_table = _FakeTable(item={"documentId": "doc1", "status": "complete", "rawText": "Some document text."})
    captured = {}

    def fake_call_groq(messages):
        captured["messages"] = messages
        return "Follow-up answer."

    monkeypatch.setattr(chat_app, "dynamodb_table", lambda name: fake_table)
    monkeypatch.setattr(chat_app, "_call_groq", fake_call_groq)

    history = [
        {"role": "user", "text": "What is this document?"},
        {"role": "assistant", "text": "It's a lease agreement."},
    ]
    chat_app.handler(_event({"documentId": "doc1", "question": "Who is the landlord?", "history": history}), None)

    messages = captured["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "What is this document?"}
    assert messages[2] == {"role": "assistant", "content": "It's a lease agreement."}
    assert messages[3] == {"role": "user", "content": "Who is the landlord?"}


def test_ignores_malformed_history_entries(monkeypatch):
    fake_table = _FakeTable(item={"documentId": "doc1", "status": "complete", "rawText": "Text."})
    captured = {}

    def fake_call_groq(messages):
        captured["messages"] = messages
        return "Answer."

    monkeypatch.setattr(chat_app, "dynamodb_table", lambda name: fake_table)
    monkeypatch.setattr(chat_app, "_call_groq", fake_call_groq)

    bad_history = [{"role": "system", "text": "ignored"}, {"role": "user"}, {"text": "no role"}]
    chat_app.handler(_event({"documentId": "doc1", "question": "Q?", "history": bad_history}), None)

    # Only the real system prompt + the new question — every malformed
    # history entry (wrong role, missing text, missing role) is dropped.
    messages = captured["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "Q?"}


def test_returns_500_when_groq_call_fails(monkeypatch):
    fake_table = _FakeTable(item={"documentId": "doc1", "status": "complete", "rawText": "Text."})
    monkeypatch.setattr(chat_app, "dynamodb_table", lambda name: fake_table)

    def failing_call_groq(messages):
        raise RuntimeError("Groq API error 429: rate limited")

    monkeypatch.setattr(chat_app, "_call_groq", failing_call_groq)

    result = chat_app.handler(_event({"documentId": "doc1", "question": "Q?"}), None)

    assert result["statusCode"] == 500
    assert "rate limited" in json.loads(result["body"])["error"]
