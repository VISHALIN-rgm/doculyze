"""Thin boto3 client wrappers, so each Lambda doesn't repeat setup.

Note: there is no LLM client here. Document explanation and chat call
Groq directly over HTTPS with Python's built-in urllib rather than an
AWS-hosted model — see explain_document/app.py and chat/app.py, which
each have their own small _call_groq() helper.
"""

import boto3

_s3 = None
_textract = None
_dynamodb = None


def s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def textract():
    global _textract
    if _textract is None:
        _textract = boto3.client("textract")
    return _textract


def dynamodb_table(table_name: str):
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb.Table(table_name)
