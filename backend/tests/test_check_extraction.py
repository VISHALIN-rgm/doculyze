from conftest import load_function_module

check_extraction_app = load_function_module("check_extraction")


def test_collect_text_joins_words():
    blocks_by_id = {
        "key1": {
            "Id": "key1",
            "Relationships": [{"Type": "CHILD", "Ids": ["w1", "w2"]}],
        },
        "w1": {"Id": "w1", "BlockType": "WORD", "Text": "Monthly"},
        "w2": {"Id": "w2", "BlockType": "WORD", "Text": "Rent"},
    }
    assert check_extraction_app._collect_text(blocks_by_id["key1"], blocks_by_id) == "Monthly Rent"


def test_collect_text_handles_empty_block():
    assert check_extraction_app._collect_text(None, {}) == ""


def test_find_value_block_returns_matching_value():
    blocks_by_id = {
        "key1": {"Id": "key1", "Relationships": [{"Type": "VALUE", "Ids": ["val1"]}]},
        "val1": {"Id": "val1", "BlockType": "KEY_VALUE_SET"},
    }
    result = check_extraction_app._find_value_block(blocks_by_id["key1"], blocks_by_id)
    assert result["Id"] == "val1"


def test_extract_pulls_lines_with_position_and_key_value_pairs():
    # Blocks spanning what would be two separate Textract result pages —
    # _extract makes no distinction, since the caller already merged all
    # pages via NextToken before calling it.
    blocks = [
        {
            "Id": "l1",
            "BlockType": "LINE",
            "Text": "Page one line",
            "Page": 1,
            "Geometry": {"BoundingBox": {"Left": 0.1, "Top": 0.2, "Width": 0.5, "Height": 0.03}},
        },
        {
            "Id": "l2",
            "BlockType": "LINE",
            "Text": "Page two line",
            "Page": 2,
            "Geometry": {"BoundingBox": {"Left": 0.1, "Top": 0.4, "Width": 0.6, "Height": 0.03}},
        },
        {
            "Id": "k1",
            "BlockType": "KEY_VALUE_SET",
            "EntityTypes": ["KEY"],
            "Relationships": [
                {"Type": "CHILD", "Ids": ["kw1"]},
                {"Type": "VALUE", "Ids": ["v1"]},
            ],
        },
        {"Id": "kw1", "BlockType": "WORD", "Text": "Total"},
        {
            "Id": "v1",
            "BlockType": "KEY_VALUE_SET",
            "Relationships": [{"Type": "CHILD", "Ids": ["vw1"]}],
        },
        {"Id": "vw1", "BlockType": "WORD", "Text": "$42"},
    ]
    lines, kv_pairs = check_extraction_app._extract(blocks)
    assert [line["text"] for line in lines] == ["Page one line", "Page two line"]
    assert lines[0]["page"] == 1
    assert lines[1]["page"] == 2
    assert lines[0]["boundingBox"] == {"left": 0.1, "top": 0.2, "width": 0.5, "height": 0.03}
    assert kv_pairs == [{"key": "Total", "value": "$42"}]


class _FakeTextractSucceeded:
    def get_document_analysis(self, JobId, NextToken=None):
        return {
            "JobStatus": "SUCCEEDED",
            "Blocks": [
                {
                    "Id": "l1",
                    "BlockType": "LINE",
                    "Text": "Hello",
                    "Page": 1,
                    "Geometry": {"BoundingBox": {"Left": 0.05, "Top": 0.1, "Width": 0.2, "Height": 0.02}},
                }
            ],
        }


class _FakeTextractInProgress:
    def get_document_analysis(self, JobId, **kwargs):
        return {"JobStatus": "IN_PROGRESS"}


class _FakeTextractFailed:
    def get_document_analysis(self, JobId, **kwargs):
        return {"JobStatus": "FAILED", "StatusMessage": "Unsupported document."}


def test_handler_returns_succeeded_status_with_extracted_text(monkeypatch):
    monkeypatch.setattr(check_extraction_app, "textract", lambda: _FakeTextractSucceeded())
    result = check_extraction_app.handler({"job": {"jobId": "abc"}}, None)
    assert result["status"] == "SUCCEEDED"
    assert "Hello" in result["text"]
    assert result["lines"][0]["text"] == "Hello"
    assert result["lines"][0]["boundingBox"]["left"] == 0.05


def test_handler_returns_in_progress_and_increments_attempts(monkeypatch):
    monkeypatch.setattr(check_extraction_app, "textract", lambda: _FakeTextractInProgress())
    result = check_extraction_app.handler({"job": {"jobId": "abc"}, "extraction": {"attempts": 3}}, None)
    assert result["status"] == "IN_PROGRESS"
    assert result["attempts"] == 4


def test_handler_gives_up_after_max_poll_attempts(monkeypatch):
    monkeypatch.setattr(check_extraction_app, "textract", lambda: _FakeTextractInProgress())
    previous = {"attempts": check_extraction_app.MAX_POLL_ATTEMPTS - 1}
    result = check_extraction_app.handler({"job": {"jobId": "abc"}, "extraction": previous}, None)
    assert result["status"] == "FAILED"
    assert "longer than expected" in result["error"]


def test_handler_surfaces_textract_failure_message(monkeypatch):
    monkeypatch.setattr(check_extraction_app, "textract", lambda: _FakeTextractFailed())
    result = check_extraction_app.handler({"job": {"jobId": "abc"}}, None)
    assert result["status"] == "FAILED"
    assert result["error"] == "Unsupported document."
