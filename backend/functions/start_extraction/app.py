"""start_extraction
Step Functions task — first step of extraction. Starts an asynchronous
Amazon Textract job against whatever document was uploaded.

The async API is used deliberately instead of the synchronous one:
Textract's synchronous AnalyzeDocument/DetectDocumentText calls only
support single-page documents. The async StartDocumentAnalysis API
supports documents of any page count, so a one-page bill and a
twenty-page lease go through the exact same code path here — nothing
about page count or document type is special-cased.
"""

from clients import textract


def handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

    response = textract().start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["TABLES", "FORMS"],
    )

    return {"jobId": response["JobId"]}
