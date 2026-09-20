import { useState, useCallback } from 'react'
import TopNav from './components/TopNav.jsx'
import BackgroundArt from './components/BackgroundArt.jsx'
import BotMascot from './components/BotMascot.jsx'
import UploadBox from './components/UploadBox.jsx'
import ResultView from './components/ResultView.jsx'
import ExampleCards from './components/ExampleCards.jsx'
import HowItWorks from './components/HowItWorks.jsx'
import WhyDoculyze from './components/WhyDoculyze.jsx'
import UseCases from './components/UseCases.jsx'
import FAQ from './components/FAQ.jsx'
import AwsBadge from './components/AwsBadge.jsx'
import { uploadDocument, pollResult } from './api/client.js'

const STAGES = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  DONE: 'done',
  ERROR: 'error',
}

export default function App() {
  const [stage, setStage] = useState(STAGES.IDLE)
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  const handleFile = useCallback(async (file) => {
    setStage(STAGES.UPLOADING)
    setErrorMessage('')
    setResult(null)
    try {
      const { documentId } = await uploadDocument(file)
      setStage(STAGES.PROCESSING)
      const finalResult = await pollResult(documentId)
      if (finalResult.status === 'failed') {
        setErrorMessage(finalResult.error || 'Something went wrong reading that document.')
        setStage(STAGES.ERROR)
        return
      }
      setResult(finalResult)
      setStage(STAGES.DONE)
    } catch (err) {
      setErrorMessage(err.message || 'Something went wrong.')
      setStage(STAGES.ERROR)
    }
  }, [])

  const reset = () => {
    setStage(STAGES.IDLE)
    setResult(null)
    setErrorMessage('')
  }

  const scrollToUpload = (e) => {
    e.preventDefault()
    document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <div className="app-shell">
      <div className="bg-glow" aria-hidden="true" />
      <BackgroundArt />

      <header className="topbar">
        <a href="#home" className="brand" onClick={reset}>
          <span className="brand-mark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M7 3.5h7l5 5V19a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 6 19V5A1.5 1.5 0 0 1 7 3.5Z" strokeLinejoin="round" />
              <path d="M14 3.5v5h5" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="brand-name">Doculyze</span>
        </a>

        <TopNav />
      </header>

      <main className="main-column" id="home">
        <section className="hero">
          <div className="hero-copy">
            <h1>
              <span className="hero-muted">Turn Confusing Documents</span>
              <br />
              into <span className="hero-accent">Clear Answers</span>
            </h1>
            <p className="hero-sub">
              Upload any document and let Doculyze understand, analyze and explain
              what really matters — in simple words.
            </p>
            <button className="primary-button hero-cta" onClick={scrollToUpload}>
              Get Started
            </button>
          </div>
          <BotMascot />
        </section>

        <div id="upload-section">
          <UploadBox stage={stage} onFile={handleFile} errorMessage={errorMessage} onRetry={reset} />
        </div>

        {stage === STAGES.IDLE && <ExampleCards />}

        {stage === STAGES.DONE && result && (
          <ResultView result={result} onAnalyzeAnother={reset} />
        )}
      </main>

      <HowItWorks />
      <WhyDoculyze />
      <UseCases />
      <FAQ />

      <footer className="page-footer">
        <AwsBadge />
        <span>Built on Amazon S3, Textract, Step Functions &amp; DynamoDB — explained via Groq</span>
      </footer>
    </div>
  )
}
