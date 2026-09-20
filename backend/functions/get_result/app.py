"""get_result
GET /result/{documentId}  -> a single analysis (or {"status": "processing"})
GET /results              -> recent analyses, newest first
"""

import json
import os

from clients import dynamodb_table
from boto3.dynamodb.conditions import Attr

RESULTS_TABLE = os.environ["RESULTS_TABLE"]

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def handler(event, context):
    table = dynamodb_table(RESULTS_TABLE)
    path_params = event.get("pathParameters") or {}

    try:
        if "documentId" in path_params:
            response = table.get_item(Key={"documentId": path_params["documentId"]})
            item = response.get("Item")
            if not item:
                item = {"documentId": path_params["documentId"], "status": "processing"}
            return _ok(item)

        # GET /results — recent items, newest first (small demo dataset, so a scan is fine)
        response = table.scan(FilterExpression=Attr("status").exists())
        items = sorted(response.get("Items", []), key=lambda i: i.get("createdAt", 0), reverse=True)
        return _ok(items[:20])

    except Exception as exc:  # noqa: BLE001
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(exc)}),
        }


def _ok(body):
    return {
        "statusCode": 200,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }
