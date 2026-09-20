export default function AwsBadge() {
  return (
    <div className="aws-badge">
      <CloudGlyph />
      <span>
        Built with <strong>AWS</strong>
      </span>
    </div>
  )
}

function CloudGlyph() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M7 17.5a4 4 0 0 1-.6-7.95 4.9 4.9 0 0 1 9.45-1.5A4 4 0 0 1 16.5 17.5H7Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M9.5 20.5h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}
