from conftest import load_function_module

save_result_app = load_function_module("save_result")


class _FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)


def test_saves_complete_result_from_explanation(monkeypatch):
    fake_table = _FakeTable()
    monkeypatch.setattr(save_result_app, "dynamodb_table", lambda name: fake_table)

    event = {
        "documentId": "doc1",
        "documentName": "lease.pdf",
        "bucket": "doculyze-uploads-123",
        "key": "uploads/doc1/lease.pdf",
        "extraction": {"text": "This lease runs for 12 months and renews automatically."},
        "explanation": {
            "documentType": "lease",
            "summary": "A rental agreement.",
            "keyTerms": ["12-month term"],
            "redFlags": [],
            "actionItems": ["Review the deposit clause."],
        },
    }
    result = save_result_app.handler(event, None)

    assert result["status"] == "complete"
    assert result["documentType"] == "lease"
    assert result["s3Bucket"] == "doculyze-uploads-123"
    assert result["s3Key"] == "uploads/doc1/lease.pdf"
    assert result["rawText"] == "This lease runs for 12 months and renews automatically."
    assert fake_table.items == [result]


def test_saves_failure_from_extraction_error_mapping(monkeypatch):
    # This is the shape MapExtractionFailure in the state machine produces:
    # a plain string copied from $.extraction.error to top-level $.error.
    fake_table = _FakeTable()
    monkeypatch.setattr(save_result_app, "dynamodb_table", lambda name: fake_table)

    event = {
        "documentId": "doc2",
        "documentName": "bill.png",
        "bucket": "doculyze-uploads-123",
        "key": "uploads/doc2/bill.png",
        "error": "Text extraction is taking longer than expected. Please try again.",
    }
    result = save_result_app.handler(event, None)

    assert result["status"] == "failed"
    assert "longer than expected" in result["error"]
    assert result["s3Bucket"] == "doculyze-uploads-123"


def test_saves_failure_from_lambda_exception_catch(monkeypatch):
    # This is the shape a Step Functions Catch block produces: an object
    # with Error/Cause keys, not a plain string.
    fake_table = _FakeTable()
    monkeypatch.setattr(save_result_app, "dynamodb_table", lambda name: fake_table)

    event = {
        "documentId": "doc3",
        "documentName": "form.jpg",
        "error": {"Error": "Textract.BadDocumentException", "Cause": "Unable to read document."},
    }
    result = save_result_app.handler(event, None)

    assert result["status"] == "failed"
    assert "BadDocumentException" in result["error"]
