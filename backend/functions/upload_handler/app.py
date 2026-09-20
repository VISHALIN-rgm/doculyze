"""upload_handler
POST /upload
Accepts a base64-encoded file from the frontend, stores it in S3, and
starts the explain workflow (Textract -> Groq -> DynamoDB).

Works for ANY document type — no branching on file type or subject
matter happens here or anywhere downstream. Whatever gets uploaded
goes through the same extract-then-explain pipeline.
"""

import base64
import json
import os

from clients import s3
from models import new_document_id

import boto3

UPLOADS_BUCKET = os.environ["UPLOADS_BUCKET"]
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

_sfn = boto3.client("stepfunctions")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        file_b64 = body["file"]
        file_name = body.get("file_name", "document")

        # Strip a data: URL prefix if the frontend sent one
        if "," in file_b64 and file_b64.strip().startswith("data:"):
            file_b64 = file_b64.split(",", 1)[1]

        file_bytes = base64.b64decode(file_b64)

        document_id = new_document_id()
        key = f"uploads/{document_id}/{file_name}"

        s3().put_object(Bucket=UPLOADS_BUCKET, Key=key, Body=file_bytes)

        _sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(
                {
                    "documentId": document_id,
                    "bucket": UPLOADS_BUCKET,
                    "key": key,
                    "documentName": file_name,
                }
            ),
        )

        return {
            "statusCode": 202,
            "headers": CORS_HEADERS,
            "body": json.dumps({"documentId": document_id, "status": "processing"}),
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(exc)}),
        }
