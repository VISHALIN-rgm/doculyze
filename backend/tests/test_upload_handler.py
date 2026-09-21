import json

from conftest import load_function_module

upload_handler_app = load_function_module("upload_handler")


class _FakeS3:
    def __init__(self):
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(kwargs)


class _FakeSfn:
    def __init__(self):
        self.calls = []

    def start_execution(self, **kwargs):
        self.calls.append(kwargs)


def test_handler_uploads_file_and_starts_workflow(monkeypatch):
    fake_s3 = _FakeS3()
    fake_sfn = _FakeSfn()

    monkeypatch.setattr(upload_handler_app, "s3", lambda: fake_s3)
    monkeypatch.setattr(upload_handler_app, "_stepfunctions", lambda: fake_sfn)
    monkeypatch.setattr(upload_handler_app, "new_document_id", lambda: "doc-123")

    event = {"body": json.dumps({"file": "aGVsbG8=", "file_name": "bill.pdf"})}
    result = upload_handler_app.handler(event, None)

    assert result["statusCode"] == 202
    body = json.loads(result["body"])
    assert body == {"documentId": "doc-123", "status": "processing"}
    assert fake_s3.calls[0]["Bucket"] == "test-bucket"
    assert fake_s3.calls[0]["Key"] == "uploads/doc-123/bill.pdf"
    assert fake_s3.calls[0]["Body"] == b"hello"
    assert len(fake_sfn.calls) == 1


def test_handler_returns_400_when_file_missing():
    event = {"body": json.dumps({"file_name": "bill.pdf"})}
    result = upload_handler_app.handler(event, None)
    assert result["statusCode"] == 400


def test_handler_returns_400_when_file_is_invalid_base64():
    event = {"body": json.dumps({"file": "not-valid-base64!!", "file_name": "bill.pdf"})}
    result = upload_handler_app.handler(event, None)
    assert result["statusCode"] == 400


def test_handler_returns_400_for_invalid_json():
    result = upload_handler_app.handler({"body": "{"}, None)
    assert result["statusCode"] == 400
