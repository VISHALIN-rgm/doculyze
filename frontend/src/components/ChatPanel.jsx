import { useState, useRef, useEffect, useCallback } from 'react'
import { askQuestion } from '../api/client.js'
import {
  isSpeechSynthesisSupported,
  isSpeechRecognitionSupported,
  speak,
  stopSpeaking,
  createSpeechRecognizer,
} from '../utils/speech.js'

const SUGGESTED_QUESTIONS = [
  'What are the most important deadlines?',
  "What happens if I don't comply with this?",
  'Explain the riskiest part in more detail.',
  'What should I do next?',
]

export default function ChatPanel({ documentId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [listening, setListening] = useState(false)
  const [speakingIndex, setSpeakingIndex] = useState(null)
  const scrollRef = useRef(null)
  const recognizerRef = useRef(null)

  const canListen = isSpeechRecognitionSupported()
  const canSpeak = isSpeechSynthesisSupported()

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  // Stop any in-progress speech when the panel unmounts.
  useEffect(() => () => stopSpeaking(), [])

  const send = async (question) => {
    const text = question.trim()
    if (!text || loading) return

    setError('')
    const history = messages.map(({ role, text }) => ({ role, text }))
    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const answer = await askQuestion(documentId, text, history)
      setMessages((prev) => [...prev, { role: 'assistant', text: answer }])
    } catch (err) {
      setError(err.message || 'Something went wrong answering that.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    send(input)
  }

  const toggleListening = useCallback(() => {
    if (!canListen) return

    if (listening) {
      recognizerRef.current?.stop()
      return
    }

    const recognizer = createSpeechRecognizer({
      onResult: (transcript) => {
        if (transcript) send(transcript)
      },
      onEnd: () => setListening(false),
      onError: () => setListening(false),
    })
    if (!recognizer) return

    recognizerRef.current = recognizer
    setListening(true)
    recognizer.start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canListen, listening, messages])

  const toggleSpeak = (index, text) => {
    if (!canSpeak) return
    if (speakingIndex === index) {
      stopSpeaking()
      setSpeakingIndex(null)
      return
    }
    setSpeakingIndex(index)
    speak(text, { onEnd: () => setSpeakingIndex(null) })
  }

  return (
    <div className="glass-card chat-panel">
      <h3>Ask about this document</h3>

      {messages.length === 0 && (
        <div className="chat-suggestions">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button key={q} className="chat-suggestion-chip" onClick={() => send(q)} disabled={loading}>
              {q}
            </button>
          ))}
        </div>
      )}

      {messages.length > 0 && (
        <div className="chat-messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble-row chat-bubble-row-${m.role}`}>
              <div className={`chat-bubble chat-bubble-${m.role}`}>{m.text}</div>
              {m.role === 'assistant' && canSpeak && (
                <button
                  type="button"
                  className={`chat-speak-button ${speakingIndex === i ? 'active' : ''}`}
                  onClick={() => toggleSpeak(i, m.text)}
                  title={speakingIndex === i ? 'Stop reading aloud' : 'Read aloud'}
                  aria-label={speakingIndex === i ? 'Stop reading aloud' : 'Read aloud'}
                >
                  {speakingIndex === i ? <StopIcon /> : <SpeakerIcon />}
                </button>
              )}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble chat-bubble-assistant chat-bubble-loading">
              <span className="chat-dot" />
              <span className="chat-dot" />
              <span className="chat-dot" />
            </div>
          )}
        </div>
      )}

      {error && <p className="chat-error">{error}</p>}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        {canListen && (
          <button
            type="button"
            className={`chat-mic-button ${listening ? 'active' : ''}`}
            onClick={toggleListening}
            disabled={loading}
            title={listening ? 'Stop listening' : 'Ask by voice'}
            aria-label={listening ? 'Stop listening' : 'Ask by voice'}
          >
            <MicIcon />
          </button>
        )}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={listening ? 'Listening…' : 'Ask a question about this document…'}
          disabled={loading || listening}
        />
        <button type="submit" className="chat-send-button" disabled={loading || !input.trim()}>
          <SendIcon />
        </button>
      </form>
    </div>
  )
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 12h16M13 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function MicIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5.5 11a6.5 6.5 0 0 0 13 0" strokeLinecap="round" />
      <path d="M12 17.5V21M9 21h6" strokeLinecap="round" />
    </svg>
  )
}

function SpeakerIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9">
      <path d="M4 9.5v5h3.5L13 19V5L7.5 9.5H4Z" strokeLinejoin="round" />
      <path d="M16.5 9a4.5 4.5 0 0 1 0 6" strokeLinecap="round" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  )
}
