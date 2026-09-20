export default function HistoryList({ items, onClose }) {
  return (
    <div className="history-overlay" onClick={onClose}>
      <div className="glass-card history-panel" onClick={(e) => e.stopPropagation()}>
        <div className="history-header">
          <h3>Past documents</h3>
          <button className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>

        {items.length === 0 && <p className="muted">No documents analyzed yet.</p>}

        <ul className="history-items">
          {items.map((item) => (
            <li key={item.documentId} className="history-item">
              <div>
                <p className="history-name">{item.documentName || 'Untitled document'}</p>
                <p className="fine-print">{item.documentType || item.status}</p>
              </div>
              <span className={`status-chip status-${item.status}`}>{item.status}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
