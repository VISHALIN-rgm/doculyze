# Architecture notes

```
 Browser (React, Amplify Hosting — single page)
        │  POST /upload  (base64 file)
        ▼
 API Gateway (HTTP API)
        │
        ▼
 Lambda: upload_handler
        │  1. writes file to S3 (uploads bucket)
        │  2. starts Step Functions execution
        ▼
 Step Functions: doculyze-explain-workflow
        │
        ├─▶ Lambda: start_extraction    (Textract StartDocumentAnalysis — async job)
        │        │
        │        ▼
        │   Wait 5s ──────────────┐
        │        │                │
        │        ▼                │
        ├─▶ Lambda: check_extraction   (Textract GetDocumentAnalysis)
        │        │  IN_PROGRESS ──┘  (loops back to Wait)
        │        │  FAILED  ─────────▶ save_result (failed)
        │        │  SUCCEEDED
        │        ▼
        ├─▶ Lambda: explain_document   (direct HTTPS call → Groq's chat completions API)
        │
        └─▶ Lambda: save_result        (writes to DynamoDB)

 Browser polls:
        GET /result/{documentId}  →  Lambda: get_result         →  DynamoDB
        GET /results              →  Lambda: get_result         →  DynamoDB (list)

 Browser, on the results page:
        POST /chat                →  Lambda: chat               →  DynamoDB (read rawText) + Groq
        GET /document/{documentId} →  Lambda: get_document_url  →  DynamoDB (read s3 location) + presigned S3 URL

 Browser, client-side only (no backend call):
        Web Speech API → reads the explanation aloud automatically,
        and each chat answer, on demand. Also powers the chat's
        microphone input (speech-to-text) where the browser supports it.
```

**Why Groq instead of Bedrock:** `explain_document` and `chat` both
call Groq's chat completions API directly over HTTPS
(`https://api.groq.com/openai/v1/chat/completions`) using Python's
built-in `urllib`, rather than calling an AWS-hosted model. This was a
deliberate swap, not a default — it genuinely changes what "Built on
AWS" means for this project, since the model host itself is no longer
an AWS service even though everything around it (S3, Textract, Lambda,
Step Functions, DynamoDB, API Gateway) still is.

**Why a direct HTTP call instead of an SDK:** we initially tried
reaching Groq through the Strands Agents SDK, for its agent-framework
structure. Two things ruled it out. First, `strands-agents` has a
hard, non-optional dependency on `mcp` (Model Context Protocol
support — a tool-integration feature this app never uses), and `mcp`
itself requires `pywin32` on Windows — meaning `sam build` run
natively on Windows without a container fails trying to resolve a
Windows-only package unrelated to anything we actually needed Strands
for. Second, even past that, `strands-agents[openai]` (the leaner of
the two viable installs — the more commonly documented
`strands-agents[litellm]` path installs to **314MB**, over Lambda's
250MB unzipped limit entirely) still installs to **132MB**, versus a
few KB for a plain HTTP call using only the standard library. Neither
problem is worth paying for a framework whose actual agentic features
— tool use, multi-step reasoning, MCP — this code never exercises.
Calling Groq directly with `urllib` sidesteps both: it builds
identically on any OS, and the deployment package is back to the same
lean size it was with the original Bedrock setup.

**Why chat and the document viewer are plain API calls, not part of
the Step Functions workflow:** both are read-driven, on-demand, and
don't need retries or multi-step orchestration — `chat` is a single
Groq call grounded in text `save_result` already persisted, and
`get_document_url` is a single presigned-URL generation. Putting them
in Step Functions would add orchestration overhead with no benefit;
plain Lambda + API Gateway is the right amount of machinery for a
single synchronous read-and-respond.

**Why highlighting a flagged clause doesn't need its own OCR or
matching service:** `check_extraction` already gets each line's
position from Textract for free (`Geometry.BoundingBox`), and
`explain_document` asks the model to quote the flagged text verbatim
rather than paraphrase it. Matching that quote back to a line (or a
short span of two consecutive lines) is a simple normalized-text
containment check — no extra service, no additional cost. When a
quote can't be matched exactly (the model paraphrased despite
instructions, which happens occasionally), that one flag simply has no
highlight and still appears in the text list — never a hard failure
over one unmatched flag.

**Why an async Textract job instead of a single synchronous call:**
Textract's synchronous `AnalyzeDocument`/`DetectDocumentText` API only
supports single-page documents — a real multi-page lease or syllabus
PDF would fail outright. The async `StartDocumentAnalysis` +
`GetDocumentAnalysis` pair handles any page count. `start_extraction`
kicks the job off; `check_extraction` is polled by the state machine's
`Wait`/`Choice` loop every 5 seconds until Textract reports
`SUCCEEDED` or `FAILED` (capped at 40 polls — about 3 minutes — before
giving up gracefully rather than looping forever). Once a job
succeeds, `check_extraction` pages through *every* result batch via
Textract's own `NextToken` pagination (a separate concept from
document page count) before extracting text and key/value pairs, so
the number of pages in the source document never changes the code
path.

**Why Step Functions instead of one big Lambda:** it makes the
pipeline visible and debuggable (each stage's input/output is
inspectable in the AWS console), it isolates retries per stage instead
of retrying the whole thing on any failure, and it gives judges a
clear diagram of a genuine multi-service architecture rather than
"one Lambda calling an API."

**Why the pipeline doesn't branch on document type:** the same
sequence — start extraction, poll until done, explain, save — runs
regardless of what's uploaded. The "what kind of document is this"
judgment is left entirely to the model prompt
(`backend/functions/explain_document/prompts.py`), which asks the
model to identify the document type itself rather than the code
assuming it ahead of time. This keeps the system genuinely general
purpose instead of a set of if/else branches for a few hardcoded
categories.

**Why voice is entirely client-side:** reading the explanation aloud
and accepting spoken questions both use the browser's built-in Web
Speech API (`speechSynthesis` and `SpeechRecognition`) rather than a
service like Amazon Polly or Transcribe. That keeps it free, adds zero
backend complexity, and works instantly — the trade-off is that
voice *input* specifically only works reliably in Chromium-based
browsers; `frontend/src/utils/speech.js` feature-detects this and the
microphone button simply doesn't render where it isn't supported,
rather than showing something broken.

**Cost shape:** every AWS component is pay-per-use (S3, Lambda, Step
Functions, Textract, DynamoDB on-demand, API Gateway HTTP API) —
nothing runs, and nothing costs anything, when no one is uploading a
document. Groq is billed separately, per token, outside AWS.
