const PILLARS = [
  {
    title: 'One pipeline, any document',
    desc: 'No dropdowns, no picking a category. Upload anything with text on it and the same pipeline reads it.',
    icon: SparkIcon,
  },
  {
    title: 'Built for people, not just lawyers',
    desc: 'We think understanding a lease or a bill shouldn\u2019t require a background in the subject.',
    icon: PeopleIcon,
  },
  {
    title: 'Fully serverless on AWS',
    desc: 'S3, Textract, Bedrock, Step Functions, Lambda and DynamoDB — nothing to run, nothing idle costs.',
    icon: StackIcon,
  },
]

export default function AboutUs() {
  return (
    <section className="content-section" id="about-us">
      <div className="section-heading-wrap">
        <h2 className="section-heading">About Us</h2>
        <p className="section-sub">
          Doculyze started as a simple idea: everyone has a document they signed, skimmed,
          or filed away without really understanding. We built an agent that reads it properly
          — whatever it is — and explains it back in plain words.
        </p>
      </div>
      <div className="example-grid">
        {PILLARS.map((p) => (
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

function SparkIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.5c.6 3.4 2.1 5 5.5 5.5-3.4.6-5 2.1-5.5 5.5-.6-3.4-2.1-5-5.5-5.5 3.4-.6 5-2.1 5.5-5.5Z" />
      <path d="M19 15c.3 1.7 1 2.4 2.7 2.7-1.7.3-2.4 1-2.7 2.7-.3-1.7-1-2.4-2.7-2.7 1.7-.3 2.4-1 2.7-2.7Z" />
    </svg>
  )
}

function PeopleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19c.5-3.3 2.7-5 5.5-5s5 1.7 5.5 5" strokeLinecap="round" />
      <circle cx="17" cy="7.5" r="2.3" />
      <path d="M15.8 14.2c2.2.3 3.7 1.8 4.2 4.3" strokeLinecap="round" />
    </svg>
  )
}

function StackIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="m12 3.5 8 4.3-8 4.3-8-4.3 8-4.3Z" strokeLinejoin="round" />
      <path d="m4 12.2 8 4.3 8-4.3M4 16 12 20.3 20 16" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
