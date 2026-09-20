from conftest import load_function_module

start_extraction_app = load_function_module("start_extraction")


class _FakeTextract:
    def __init__(self):
        self.calls = []

    def start_document_analysis(self, DocumentLocation, FeatureTypes):
        self.calls.append((DocumentLocation, FeatureTypes))
        return {"JobId": "job-123"}


def test_handler_starts_job_with_correct_s3_location(monkeypatch):
    fake = _FakeTextract()
    monkeypatch.setattr(start_extraction_app, "textract", lambda: fake)

    result = start_extraction_app.handler(
        {"documentId": "doc1", "bucket": "my-bucket", "key": "uploads/doc1/file.pdf"}, None
    )

    assert result == {"jobId": "job-123"}
    assert len(fake.calls) == 1
    location, feature_types = fake.calls[0]
    assert location == {"S3Object": {"Bucket": "my-bucket", "Name": "uploads/doc1/file.pdf"}}
    assert set(feature_types) == {"TABLES", "FORMS"}


def test_handler_works_regardless_of_file_extension(monkeypatch):
    # No branching on document type or extension — same call shape every time.
    fake = _FakeTextract()
    monkeypatch.setattr(start_extraction_app, "textract", lambda: fake)

    for key in ["uploads/a/bill.png", "uploads/b/lease.pdf", "uploads/c/syllabus.jpg"]:
        start_extraction_app.handler({"documentId": "x", "bucket": "b", "key": key}, None)

    assert len(fake.calls) == 3
    for _, feature_types in fake.calls:
        assert set(feature_types) == {"TABLES", "FORMS"}
