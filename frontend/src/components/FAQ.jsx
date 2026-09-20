const FAQS = [
  {
    q: 'What kinds of documents can I upload?',
    a: 'Any document with readable text — a PDF, a scanned image, or a photo. There\u2019s no menu of supported types; Doculyze reads whatever you give it and works out what it is.',
  },
  {
    q: 'Is my document stored anywhere?',
    a: 'It\u2019s stored in S3 inside the app\u2019s own AWS account, only for as long as it takes to process and show you the result.',
  },
  {
    q: 'Can I trust the explanation completely?',
    a: 'Treat it as a clear starting point, not professional advice. Always double-check anything flagged as a red flag before acting on it.',
  },
  {
    q: 'Does it work with handwritten documents?',
    a: 'It can read some handwriting, but results are most reliable with typed or printed text.',
  },
  {
    q: 'Is there a cost to use it?',
    a: 'Running it costs whatever AWS charges per document processed for text extraction and the explanation step — there\u2019s no separate fee on top.',
  },
]

export default function FAQ() {
  return (
    <section className="content-section" id="faq">
      <div className="section-heading-wrap">
        <h2 className="section-heading">Frequently Asked Questions</h2>
        <p className="section-sub">Everything else worth knowing before you upload something.</p>
      </div>
      <div className="faq-list">
        {FAQS.map((item) => (
          <details className="faq-item" key={item.q}>
            <summary>
              <span>{item.q}</span>
              <ChevronIcon />
            </summary>
            <p>{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

function ChevronIcon() {
  return (
    <svg className="faq-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
