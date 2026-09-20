import importlib.util
import os

_here = os.path.dirname(__file__)
import sys
sys.path.insert(0, os.path.join(_here, "..", "functions", "extract_text"))
_spec = importlib.util.spec_from_file_location(
    "extract_text_app", os.path.join(_here, "..", "functions", "extract_text", "app.py")
)
extract_text_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(extract_text_app)

_collect_text = extract_text_app._collect_text
_find_value_block = extract_text_app._find_value_block


def test_collect_text_joins_words():
    blocks_by_id = {
        "key1": {
            "Id": "key1",
            "Relationships": [{"Type": "CHILD", "Ids": ["w1", "w2"]}],
        },
        "w1": {"Id": "w1", "BlockType": "WORD", "Text": "Monthly"},
        "w2": {"Id": "w2", "BlockType": "WORD", "Text": "Rent"},
    }
    assert _collect_text(blocks_by_id["key1"], blocks_by_id) == "Monthly Rent"


def test_collect_text_handles_empty_block():
    assert _collect_text(None, {}) == ""


def test_find_value_block_returns_matching_value():
    blocks_by_id = {
        "key1": {"Id": "key1", "Relationships": [{"Type": "VALUE", "Ids": ["val1"]}]},
        "val1": {"Id": "val1", "BlockType": "KEY_VALUE_SET"},
    }
    result = _find_value_block(blocks_by_id["key1"], blocks_by_id)
    assert result["Id"] == "val1"
