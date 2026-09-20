"""Thin boto3 client wrappers, so each Lambda doesn't repeat setup."""

import boto3

_s3 = None
_textract = None
_bedrock = None
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


def bedrock():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client("bedrock-runtime")
    return _bedrock


def dynamodb_table(table_name: str):
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb.Table(table_name)
