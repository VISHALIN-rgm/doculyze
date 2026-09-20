import { useState, useEffect, useRef } from 'react'
import DocumentViewer from './DocumentViewer.jsx'
import ChatPanel from './ChatPanel.jsx'
import { downloadResultAsPdf } from '../utils/pdfExport.js'
import { isSpeechSynthesisSupported, speak, stopSpeaking } from '../utils/speech.js'

const SEVERITY_LABEL = { low: 'Low', medium: 'Medium', high: 'High' }

export default function ResultView({ result, onAnalyzeAnother }) {
  const [downloading, setDownloading] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const narratedDocumentId = useRef(null)
  const {
    documentId,
    documentType,
    documentName,
    summary,
    keyTerms = [],
    redFlags = [],
    actionItems = [],
  } = result

  const canSpeak = isSpeechSynthesisSupported()
  const narration = buildNarration({ documentType, summary, redFlags, actionItems })

  // Read the explanation aloud automatically as soon as it's ready —
  // once per document, so switching between two already-loaded results
  // (or a re-render) doesn't replay it.
  useEffect(() => {
    if (!canSpeak || !narration) return
    if (narratedDocumentId.current === documentId) return
    narratedDocumentId.current = documentId
    setSpeaking(true)
    speak(narration, { onEnd: () => setSpeaking(false) })
    return () => stopSpeaking()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId])

  const toggleListen = () => {
    if (speaking) {
      stopSpeaking()
      setSpeaking(false)
      return
    }
    setSpeaking(true)
    speak(narration, { onEnd: () => setSpeaking(false) })
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await downloadResultAsPdf(result)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <section className="result-grid">
      <div className="glass-card result-header">
        <div>
          <p className="fine-print">{documentName || 'Your document'}</p>
          <h2 className="doc-type">{documentType || 'Document'}</h2>
        </div>
        <div className="result-header-actions">
          {canSpeak && narration && (
            <button className="ghost-button" onClick={toggleListen}>
              {speaking ? <StopIcon /> : <ListenIcon />}
              {speaking ? 'Stop' : 'Listen'}
            </button>
          )}
          <button className="ghost-button" onClick={handleDownload} disabled={downloading}>
            <DownloadIcon />
            {downloading ? 'Preparing…' : 'Download PDF'}
          </button>
          <button className="ghost-button" onClick={onAnalyzeAnother}>
            Analyze another
          </button>
        </div>
      </div>

      {documentId && <DocumentViewer documentId={documentId} redFlags={redFlags} />}

      <div className="glass-card summary-card">
        <h3>What this says</h3>
        <p>{summary}</p>
      </div>

      {keyTerms.length > 0 && (
        <div className="glass-card">
          <h3>Key terms</h3>
          <ul className="pill-list">
            {keyTerms.map((term, i) => (
              <li key={i} className="pill">
                {term}
              </li>
            ))}
          </ul>
        </div>
      )}

      {redFlags.length > 0 && (
        <div className="glass-card">
          <h3>Worth double-checking</h3>
          <ul className="flag-list">
            {redFlags.map((flag, i) => (
              <li key={i} className={`flag-item severity-${flag.severity || 'low'}`}>
                <span className="severity-dot" aria-hidden="true" />
                <div>
                  <p className="flag-issue">{flag.issue}</p>
                  <p className="flag-reason">{flag.why_it_matters || flag.whyItMatters}</p>
                </div>
                <span className="severity-tag">{SEVERITY_LABEL[flag.severity] || 'Note'}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {actionItems.length > 0 && (
        <div className="glass-card">
          <h3>What to do next</h3>
          <ul className="action-list">
            {actionItems.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {documentId && <ChatPanel documentId={documentId} />}
    </section>
  )
}

function buildNarration({ documentType, summary, redFlags, actionItems }) {
  const parts = []
  if (summary) {
    parts.push(`Here's what this ${documentType || 'document'} says. ${summary}`)
  }
  if (redFlags?.length) {
    const issues = redFlags.map((f) => f.issue).filter(Boolean).join('. ')
    parts.push(`${redFlags.length} thing${redFlags.length > 1 ? 's' : ''} worth double-checking: ${issues}.`)
  }
  if (actionItems?.length) {
    parts.push(`Suggested next steps: ${actionItems.join('. ')}.`)
  }
  return parts.join(' ')
}

function DownloadIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9">
      <path d="M12 4v11m0 0 4-4m-4 4-4-4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 18.5h14" strokeLinecap="round" />
    </svg>
  )
}

function ListenIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9">
      <path d="M4 9.5v5h3.5L13 19V5L7.5 9.5H4Z" strokeLinejoin="round" />
      <path d="M16.5 9a4.5 4.5 0 0 1 0 6M19 6.5a8.5 8.5 0 0 1 0 11" strokeLinecap="round" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  )
}
