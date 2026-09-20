"""extract_text
Step Functions task. Runs Amazon Textract against whatever document was
uploaded — a bill, a contract, a syllabus, a form, a letter, anything —
and returns the raw extracted text plus any detected tables/key-value
pairs. No assumptions are made about what kind of document it is.
"""

import os

from clients import textract

UPLOADS_BUCKET = os.environ["UPLOADS_BUCKET"]


def handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

    response = textract().analyze_document(
        Document={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["TABLES", "FORMS"],
    )

    lines = []
    key_value_pairs = []

    blocks_by_id = {b["Id"]: b for b in response["Blocks"]}

    for block in response["Blocks"]:
        if block["BlockType"] == "LINE" and "Text" in block:
            lines.append(block["Text"])

        if block["BlockType"] == "KEY_VALUE_SET" and block.get("EntityTypes") == ["KEY"]:
            key_text = _collect_text(block, blocks_by_id)
            value_block = _find_value_block(block, blocks_by_id)
            value_text = _collect_text(value_block, blocks_by_id) if value_block else ""
            if key_text:
                key_value_pairs.append({"key": key_text, "value": value_text})

    full_text = "\n".join(lines)

    return {
        "documentId": event["documentId"],
        "documentName": event.get("documentName"),
        "bucket": bucket,
        "key": key,
        "text": full_text[:15000],  # keep payload reasonable for Bedrock
        "keyValuePairs": key_value_pairs[:40],
    }


def _collect_text(block, blocks_by_id):
    if not block:
        return ""
    text_parts = []
    for rel in block.get("Relationships", []):
        if rel["Type"] == "CHILD":
            for child_id in rel["Ids"]:
                child = blocks_by_id.get(child_id, {})
                if child.get("BlockType") == "WORD":
                    text_parts.append(child.get("Text", ""))
    return " ".join(text_parts)


def _find_value_block(key_block, blocks_by_id):
    for rel in key_block.get("Relationships", []):
        if rel["Type"] == "VALUE":
            for value_id in rel["Ids"]:
                return blocks_by_id.get(value_id)
    return None
