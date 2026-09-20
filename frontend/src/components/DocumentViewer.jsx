import { useEffect, useRef, useState } from 'react'
import { getDocumentUrl } from '../api/client.js'

export default function DocumentViewer({ documentId, redFlags = [] }) {
  const [docInfo, setDocInfo] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [pdfDoc, setPdfDoc] = useState(null)
  const [pageNum, setPageNum] = useState(1)
  const [numPages, setNumPages] = useState(1)
  const [showHighlights, setShowHighlights] = useState(true)
  const canvasRef = useRef(null)

  const highlights = buildHighlights(redFlags)

  // Fetch the presigned URL for the original upload.
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    getDocumentUrl(documentId)
      .then((info) => {
        if (!cancelled) setDocInfo(info)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Could not load the document preview.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [documentId])

  // Load the PDF document (if it is one) once we have its URL. pdfjs-dist
  // is a sizeable library, so it's imported dynamically here rather than
  // eagerly at module load — most results are viewed without ever
  // needing it (images skip this path, and not every visit renders a
  // PDF), so there's no reason to make every page load pay for it.
  useEffect(() => {
    if (!docInfo || docInfo.contentType !== 'application/pdf') return
    let cancelled = false

    import('pdfjs-dist').then(async (pdfjsLib) => {
      if (cancelled) return
      const workerUrl = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url')).default
      pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl

      pdfjsLib
        .getDocument(docInfo.url)
        .promise.then((doc) => {
          if (cancelled) return
          setPdfDoc(doc)
          setNumPages(doc.numPages)
          setPageNum(1)
        })
        .catch(() => {
          if (!cancelled) setError('Could not render the PDF preview.')
        })
    })

    return () => {
      cancelled = true
    }
  }, [docInfo])

  // Render the current PDF page onto the canvas.
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return
    let cancelled = false
    pdfDoc.getPage(pageNum).then((page) => {
      if (cancelled) return
      const viewport = page.getViewport({ scale: 1.6 })
      const canvas = canvasRef.current
      canvas.width = viewport.width
      canvas.height = viewport.height
      const ctx = canvas.getContext('2d')
      page.render({ canvasContext: ctx, viewport })
    })
    return () => {
      cancelled = true
    }
  }, [pdfDoc, pageNum])

  if (loading) {
    return (
      <div className="glass-card doc-viewer">
        <p className="muted">Loading document preview…</p>
      </div>
    )
  }

  // A preview isn't essential to using the app — if it can't load for
  // any reason, omit it quietly rather than breaking the results page.
  if (error || !docInfo) return null

  const isImage = docInfo.contentType.startsWith('image/')
  const isPdf = docInfo.contentType === 'application/pdf'
  const pageHighlights = highlights.filter((h) => !isPdf || h.page === pageNum)

  return (
    <div className="glass-card doc-viewer">
      <div className="doc-viewer-header">
        <h3>Document preview</h3>
        {highlights.length > 0 && (
          <button className="ghost-button doc-viewer-toggle" onClick={() => setShowHighlights((s) => !s)}>
            {showHighlights ? 'Hide highlights' : 'Show highlights'}
          </button>
        )}
      </div>

      <div className="doc-viewer-canvas-wrap">
        {isImage && <img src={docInfo.url} alt="Uploaded document" className="doc-viewer-image" />}
        {isPdf && <canvas ref={canvasRef} className="doc-viewer-canvas" />}

        {showHighlights &&
          pageHighlights.map((h, i) => (
            <span
              key={i}
              className={`doc-highlight severity-${h.severity}`}
              title={h.issue}
              style={{
                left: `${h.boundingBox.left * 100}%`,
                top: `${h.boundingBox.top * 100}%`,
                width: `${h.boundingBox.width * 100}%`,
                height: `${h.boundingBox.height * 100}%`,
              }}
            />
          ))}
      </div>

      {isPdf && numPages > 1 && (
        <div className="doc-viewer-pager">
          <button className="ghost-button" onClick={() => setPageNum((p) => Math.max(1, p - 1))} disabled={pageNum <= 1}>
            Prev
          </button>
          <span className="fine-print">
            Page {pageNum} of {numPages}
          </span>
          <button
            className="ghost-button"
            onClick={() => setPageNum((p) => Math.min(numPages, p + 1))}
            disabled={pageNum >= numPages}
          >
            Next
          </button>
        </div>
      )}

      {highlights.length === 0 && (
        <p className="fine-print doc-viewer-note">No flagged clauses could be matched to a spot on the page.</p>
      )}
    </div>
  )
}

function buildHighlights(redFlags) {
  const highlights = []
  redFlags.forEach((flag) => {
    ;(flag.location || []).forEach((loc) => {
      highlights.push({
        page: loc.page || 1,
        boundingBox: loc.boundingBox || {},
        severity: flag.severity || 'low',
        issue: flag.issue,
      })
    })
  })
  return highlights
}
