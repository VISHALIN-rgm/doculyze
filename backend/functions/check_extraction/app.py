"""check_extraction
Step Functions task, invoked in a poll loop (see the Wait/Choice states
in the state machine). Checks the status of the async Textract job
started by start_extraction.

A single GetDocumentAnalysis call only returns one page of *results*
(a Textract pagination concept, unrelated to document page count) —
so once the job has succeeded, this pages through every result batch
via NextToken until there are no more, aggregating all of the detected
blocks before extracting text and key/value pairs. This is what makes
multi-page documents work correctly: nothing here assumes or limits
how many pages the source document has, or what kind of document it
is — the same extraction logic runs regardless.
"""

from clients import textract

# How many times this function may be polled by the state machine
# before giving up on a single extraction job. This is an operational
# timeout (guards against a stuck Textract job looping forever), not a
# limit tied to any particular document type or size.
MAX_POLL_ATTEMPTS = 40


def handler(event, context):
    job_id = event["job"]["jobId"]
    previous = event.get("extraction") or {}
    attempts = previous.get("attempts", 0) + 1

    response = textract().get_document_analysis(JobId=job_id)
    status = response["JobStatus"]

    if status == "IN_PROGRESS":
        if attempts >= MAX_POLL_ATTEMPTS:
            return {
                "status": "FAILED",
                "error": "Text extraction is taking longer than expected. Please try again.",
                "attempts": attempts,
            }
        return {"status": "IN_PROGRESS", "attempts": attempts}

    if status == "FAILED":
        return {
            "status": "FAILED",
            "error": response.get("StatusMessage") or "Text extraction failed.",
            "attempts": attempts,
        }

    if status not in ("SUCCEEDED", "PARTIAL_SUCCESS"):
        return {
            "status": "FAILED",
            "error": f"Unexpected Textract job status: {status}",
            "attempts": attempts,
        }

    blocks = list(response.get("Blocks", []))
    next_token = response.get("NextToken")
    while next_token:
        response = textract().get_document_analysis(JobId=job_id, NextToken=next_token)
        blocks.extend(response.get("Blocks", []))
        next_token = response.get("NextToken")

    lines, key_value_pairs = _extract(blocks)
    line_texts = [line["text"] for line in lines]

    return {
        "status": "SUCCEEDED",
        "text": "\n".join(line_texts)[:15000],  # keep the payload reasonable for the model
        "lines": lines[:500],  # capped to keep Step Functions state size reasonable
        "keyValuePairs": key_value_pairs[:40],
        "attempts": attempts,
    }


def _extract(blocks):
    """Pulls plain text lines (with page + position) and key/value pairs
    out of a full set of Textract blocks, regardless of how many pages
    they span. Position is Textract's own normalized bounding box (each
    value a 0-1 fraction of the page), which is what makes drawing a
    highlight over the rendered document later a matter of CSS
    percentages rather than pixel math tied to any particular render
    size."""
    blocks_by_id = {b["Id"]: b for b in blocks}
    lines = []
    key_value_pairs = []

    for block in blocks:
        if block["BlockType"] == "LINE" and "Text" in block:
            box = block.get("Geometry", {}).get("BoundingBox", {})
            lines.append(
                {
                    "text": block["Text"],
                    "page": block.get("Page", 1),
                    "boundingBox": {
                        "left": box.get("Left", 0),
                        "top": box.get("Top", 0),
                        "width": box.get("Width", 0),
                        "height": box.get("Height", 0),
                    },
                }
            )

        if block["BlockType"] == "KEY_VALUE_SET" and block.get("EntityTypes") == ["KEY"]:
            key_text = _collect_text(block, blocks_by_id)
            value_block = _find_value_block(block, blocks_by_id)
            value_text = _collect_text(value_block, blocks_by_id) if value_block else ""
            if key_text:
                key_value_pairs.append({"key": key_text, "value": value_text})

    return lines, key_value_pairs


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
