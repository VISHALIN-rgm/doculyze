"""save_result
Step Functions terminal task (success or failure path). Writes the
analysis — or the error — to DynamoDB, keyed by documentId, so the
frontend can poll GET /result/{documentId}.

Also persists the raw extracted text and the document's S3 location,
which two other features need after this point: the chat endpoint
grounds its answers in the raw text, and the document-viewer endpoint
generates a presigned URL from the stored S3 location so the original
file can be rendered (with highlights) in the browser.
"""

import os
import time

from clients import dynamodb_table

RESULTS_TABLE = os.environ["RESULTS_TABLE"]


def handler(event, context):
    table = dynamodb_table(RESULTS_TABLE)
    document_id = event["documentId"]
    extraction = event.get("extraction") or {}

    base = {
        "documentId": document_id,
        "documentName": event.get("documentName"),
        "s3Bucket": event.get("bucket"),
        "s3Key": event.get("key"),
        "createdAt": int(time.time()),
    }

    if "error" in event:
        item = {
            **base,
            "status": "failed",
            "error": str(event["error"]),
        }
    else:
        explanation = event.get("explanation", {})
        item = {
            **base,
            "status": "complete",
            "documentType": explanation.get("documentType", "document"),
            "summary": explanation.get("summary", ""),
            "keyTerms": explanation.get("keyTerms", []),
            "redFlags": explanation.get("redFlags", []),
            "actionItems": explanation.get("actionItems", []),
            "rawText": extraction.get("text", ""),
        }

    table.put_item(Item=item)
    return item
