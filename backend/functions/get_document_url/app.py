"""get_document_url
GET /document/{documentId}
Returns a short-lived presigned S3 URL for the original uploaded file,
plus its content type, so the frontend can render the document itself
(image or PDF) and draw highlight overlays over it. The stored S3
location works the same way regardless of file type — no branching by
extension here; the frontend decides how to render based on the
content type this returns.
"""

import json
import mimetypes
import os

from clients import dynamodb_table, s3

RESULTS_TABLE = os.environ["RESULTS_TABLE"]
URL_EXPIRY_SECONDS = 300

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        document_id = path_params.get("documentId")

        if not document_id:
            return _error(400, "documentId is required.")

        table = dynamodb_table(RESULTS_TABLE)
        item = table.get_item(Key={"documentId": document_id}).get("Item")

        if not item or not item.get("s3Bucket") or not item.get("s3Key"):
            return _error(404, "No stored document found for this id.")

        bucket = item["s3Bucket"]
        key = item["s3Key"]
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"

        url = s3().generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=URL_EXPIRY_SECONDS,
        )

        return {
            "statusCode": 200,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({"url": url, "contentType": content_type, "expiresIn": URL_EXPIRY_SECONDS}),
        }

    except Exception as exc:  # noqa: BLE001
        return _error(500, str(exc))


def _error(status_code: int, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }
