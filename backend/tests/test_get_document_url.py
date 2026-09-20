import json

from conftest import load_function_module

get_document_url_app = load_function_module("get_document_url")


class _FakeTable:
    def __init__(self, item=None):
        self._item = item

    def get_item(self, Key):
        if self._item and self._item.get("documentId") == Key["documentId"]:
            return {"Item": self._item}
        return {}


class _FakeS3:
    def __init__(self):
        self.calls = []

    def generate_presigned_url(self, operation, Params, ExpiresIn):
        self.calls.append((operation, Params, ExpiresIn))
        return f"https://example-bucket.s3.amazonaws.com/{Params['Key']}?signed=true"


def test_returns_400_when_document_id_missing():
    result = get_document_url_app.handler({"pathParameters": {}}, None)
    assert result["statusCode"] == 400


def test_returns_404_when_document_not_found(monkeypatch):
    monkeypatch.setattr(get_document_url_app, "dynamodb_table", lambda name: _FakeTable(item=None))
    result = get_document_url_app.handler({"pathParameters": {"documentId": "missing"}}, None)
    assert result["statusCode"] == 404


def test_returns_presigned_url_and_content_type_for_pdf(monkeypatch):
    fake_table = _FakeTable(
        item={"documentId": "doc1", "s3Bucket": "doculyze-uploads", "s3Key": "uploads/doc1/lease.pdf"}
    )
    fake_s3 = _FakeS3()
    monkeypatch.setattr(get_document_url_app, "dynamodb_table", lambda name: fake_table)
    monkeypatch.setattr(get_document_url_app, "s3", lambda: fake_s3)

    result = get_document_url_app.handler({"pathParameters": {"documentId": "doc1"}}, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["contentType"] == "application/pdf"
    assert "uploads/doc1/lease.pdf" in body["url"]
    assert fake_s3.calls[0][1] == {"Bucket": "doculyze-uploads", "Key": "uploads/doc1/lease.pdf"}


def test_returns_correct_content_type_for_image(monkeypatch):
    fake_table = _FakeTable(item={"documentId": "doc2", "s3Bucket": "b", "s3Key": "uploads/doc2/bill.png"})
    monkeypatch.setattr(get_document_url_app, "dynamodb_table", lambda name: fake_table)
    monkeypatch.setattr(get_document_url_app, "s3", lambda: _FakeS3())

    result = get_document_url_app.handler({"pathParameters": {"documentId": "doc2"}}, None)

    body = json.loads(result["body"])
    assert body["contentType"] == "image/png"
