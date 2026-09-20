export default function Sidebar({ activeView, onNavigate, onOpenHistory }) {
  return (
    <aside className="sidebar">
      <ul className="side-nav">
        <li>
          <button
            className={`side-nav-item ${activeView === 'home' ? 'active' : ''}`}
            onClick={() => onNavigate('home')}
          >
            <HomeIcon />
            Home
          </button>
        </li>
        <li>
          <button
            className={`side-nav-item ${activeView === 'documents' ? 'active' : ''}`}
            onClick={() => onNavigate('documents')}
          >
            <FolderIcon />
            My Documents
          </button>
        </li>
        <li>
          <button className="side-nav-item" onClick={onOpenHistory}>
            <ClockIcon />
            History
          </button>
        </li>
      </ul>

      <div className="sidebar-footer">
        <span className="spark">✦</span>
        <p>
          Any document.
          <br />
          Clear understanding.
        </p>
        <div className="rule" />
      </div>
    </aside>
  )
}

function HomeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M3 11.5 12 4l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5.5 10v9a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function FolderIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M3.5 7a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1V7Z" strokeLinejoin="round" />
    </svg>
  )
}

function ClockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
