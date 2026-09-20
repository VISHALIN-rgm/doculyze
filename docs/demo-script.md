# Demo Script — 3-Minute Walkthrough

A live, click-through script for demoing Doculyze — to judges directly,
or as the basis for a recorded video submission. Timestamps are pacing
guides, not strict cues.

**Before you start:** have a real document ready to upload — a lease,
a bill, a syllabus, anything with real text on it. A genuinely
confusing document makes a better demo than a clean, simple one.

---

## 0:00 – 0:20 — The problem

Everyone has a drawer full of documents they signed, skimmed, or filed
away without really understanding — a lease, a bill, a syllabus, a
terms-of-service page nobody reads. Doculyze reads any of them and
explains what they actually say, out loud, and lets you ask follow-up
questions.

## 0:20 – 0:40 — Upload, live

Drag a real document into the app. Point out: there's no dropdown
asking what kind of document it is — Doculyze figures that out itself,
the same way for a one-page bill or a twenty-page lease.

## 0:40 – 1:05 — While it processes

Narrate the pipeline while the loader runs:

> "This just hit S3, which kicked off a Step Functions workflow —
> Textract is pulling the text out right now, asynchronously, so it
> can handle documents of any length. Once that's done, it goes to
> Groq to actually get explained."

## 1:05 – 1:50 — Show the result

Walk through the explanation as it appears:

- The **summary** — and point out it's already being **read aloud
  automatically**, no click needed.
- **Key terms**, then **flagged clauses** with severity — click one
  and show it's **highlighted directly on the original document**
  above, not just described in text.
- **Action items** — what to actually do next.

## 1:50 – 2:20 — Chat, by voice

Click the microphone button in the chat panel and **ask a question out
loud** — "What happens if I miss a payment?" or whichever suggested
question fits the document. Let the spoken answer play. This is the
moment that makes the demo memorable: it's not just reading a
document, it's a conversation about it.

## 2:20 – 2:40 — Architecture

Describe it plainly: S3 → Step Functions → Textract (async) → Groq →
DynamoDB, fronted by API Gateway + Lambda, frontend on Amplify
Hosting. Mention it scales to zero — nothing runs, nothing costs
anything, when no one's uploading a document. If asked about Bedrock:
it's covered in the README's "Why Groq instead of Amazon Bedrock"
section — happy to talk through it, but no need to raise it
unprompted.

## 2:40 – 3:00 — Close

Click **Download PDF** to show the clean exported report, then close
on: "One pipeline, any document — that's the point."

---

## If you're short on time

Cut in this order, without losing the core story:

1. Architecture description (1:05–2:20 section) — compress to one
   sentence: "Serverless AWS pipeline, Textract for reading, Groq for
   explaining."
2. The voice question in chat — switch to typing it instead of
   speaking it.
3. The PDF download at the end.

Never cut: the upload itself, the automatic spoken summary, and the
highlighted clause on the original document — those three are what
make this feel like a real product rather than a form with extra
steps.
