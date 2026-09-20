// Uses the browser's built-in Web Speech API — no backend, no new AWS
// service, no extra bundle weight. Support varies by browser (voice
// input in particular is unreliable outside Chrome/Edge), so every
// function here is safe to call even when unsupported: speech
// functions no-op quietly, and recognizer creation returns null so
// callers can hide the relevant UI instead of showing a broken button.

export function isSpeechSynthesisSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

export function isSpeechRecognitionSupported() {
  return typeof window !== 'undefined' && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
}

/**
 * Speaks the given text aloud. Cancels any speech already in progress
 * first, so only one thing is ever read at a time. Calls onEnd when
 * finished (naturally or via stopSpeaking).
 */
export function speak(text, { onEnd, onStart } = {}) {
  if (!isSpeechSynthesisSupported() || !text) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = 1
  utterance.pitch = 1
  if (onStart) utterance.onstart = onStart
  if (onEnd) {
    utterance.onend = onEnd
    utterance.onerror = onEnd
  }
  window.speechSynthesis.speak(utterance)
}

export function stopSpeaking() {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.cancel()
}

/**
 * Creates a one-shot voice-input recognizer, or returns null if the
 * browser doesn't support it. Call .start() to begin listening;
 * onResult fires once with the transcript, onEnd always fires when
 * listening stops (result or not) so callers can reset their UI state.
 */
export function createSpeechRecognizer({ onResult, onEnd, onError } = {}) {
  const SpeechRecognitionCtor = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)
  if (!SpeechRecognitionCtor) return null

  const recognizer = new SpeechRecognitionCtor()
  recognizer.lang = 'en-US'
  recognizer.interimResults = false
  recognizer.maxAlternatives = 1

  recognizer.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript || ''
    onResult?.(transcript)
  }
  recognizer.onerror = (event) => onError?.(event.error)
  recognizer.onend = () => onEnd?.()

  return recognizer
}
