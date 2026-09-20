const POINTS = [
  {
    title: 'Encrypted in transit & at rest',
    desc: 'Every upload travels over HTTPS and is stored in S3 with encryption at rest, end to end.',
    icon: LockIcon,
  },
  {
    title: 'Stays inside your AWS account',
    desc: 'The whole pipeline — Textract, Bedrock, DynamoDB — runs in your own account. Nothing goes to a third party.',
    icon: CloudIcon,
  },
  {
    title: 'Used only to explain your document',
    desc: 'Extracted text is sent to the model purely to generate your explanation, never for training or sharing.',
    icon: ShieldIcon,
  },
  {
    title: 'You stay in control',
    desc: 'Every upload and result is deletable from S3 and DynamoDB at any time — nothing lingers by default.',
    icon: TrashIcon,
  },
]

export default function Security() {
  return (
    <section className="content-section" id="security">
      <div className="section-heading-wrap">
        <h2 className="section-heading">Security &amp; Privacy</h2>
        <p className="section-sub">Your documents stay inside your own AWS account, end to end.</p>
      </div>
      <div className="example-grid">
        {POINTS.map((p) => (
          <div className="example-card static" key={p.title}>
            <span className="example-icon">
              <p.icon />
            </span>
            <strong>{p.title}</strong>
            <span>{p.desc}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

function LockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="5.5" y="11" width="13" height="9.5" rx="2.2" strokeLinejoin="round" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function CloudIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path
        d="M7 18.5a4.5 4.5 0 0 1-.7-8.94 5.5 5.5 0 0 1 10.6-1.7A4.5 4.5 0 0 1 17 18.5H7Z"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ShieldIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3.5 19 6.5v5c0 5-3 8.2-7 9.9-4-1.7-7-4.9-7-9.9v-5L12 3.5Z" strokeLinejoin="round" />
      <path d="m9 12 2 2 4-4.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M5.5 7h13M9.5 7V5a1.5 1.5 0 0 1 1.5-1.5h2A1.5 1.5 0 0 1 14.5 5v2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 7v12a1.5 1.5 0 0 0 1.5 1.5h7A1.5 1.5 0 0 0 17 19V7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
