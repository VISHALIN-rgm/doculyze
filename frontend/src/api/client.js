// Strip any trailing slash so `${BASE_URL}/upload` never produces a
// double slash (API Gateway HTTP APIs treat "//upload" as a 404, not
// the same route as "/upload") — protects against a trailing slash
// accidentally left in VITE_API_BASE_URL.
const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export async function uploadDocument(file) {
  const base64 = await fileToBase64(file)
  const response = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file: base64, file_name: file.name }),
  })
  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`)
  }
  return response.json() // { documentId, status }
}

export async function getResult(documentId) {
  const response = await fetch(`${BASE_URL}/result/${documentId}`)
  if (!response.ok) {
    throw new Error(`Fetch failed: ${response.status}`)
  }
  return response.json()
}

export async function listResults() {
  const response = await fetch(`${BASE_URL}/results`)
  if (!response.ok) {
    throw new Error(`Fetch failed: ${response.status}`)
  }
  return response.json()
}

/**
 * Polls GET /result/{documentId} until status is "complete" or "failed".
 * The default timeout is set comfortably above the backend's own
 * extraction poll ceiling (40 attempts x 5s ≈ 200s) plus room for the
 * explain step, so a legitimately slow multi-page document doesn't get
 * reported as "timed out" here while it's still working server-side.
 */
export async function pollResult(documentId, { intervalMs = 2500, timeoutMs = 240000 } = {}) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const result = await getResult(documentId)
    if (result.status === 'complete' || result.status === 'failed') {
      return result
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error('Timed out waiting for analysis to finish.')
}

/**
 * Asks a follow-up question about an already-analyzed document.
 * `history` is the prior conversation as [{role: 'user'|'assistant', text}],
 * kept client-side — the backend is stateless per request.
 */
export async function askQuestion(documentId, question, history = []) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ documentId, question, history }),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.error || `Chat request failed: ${response.status}`)
  }
  return data.answer
}

/**
 * Gets a short-lived presigned URL (and content type) for the original
 * uploaded document, so it can be rendered in the browser.
 */
export async function getDocumentUrl(documentId) {
  const response = await fetch(`${BASE_URL}/document/${documentId}`)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.error || `Could not load the document: ${response.status}`)
  }
  return data // { url, contentType, expiresIn }
}
