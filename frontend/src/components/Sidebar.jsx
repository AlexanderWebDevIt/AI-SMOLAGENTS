import { useState } from 'react'
import Button from './Button'
import './Sidebar.css'

const Sidebar = ({
  sessions,
  activeSession,
  onSessionSelect,
  onNewSession,
  onRenameSession,
  onDeleteSession,
  currentPage,
  onPageChange
}) => {
  const [isOpen, setIsOpen] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [editName, setEditName] = useState('')

  const navItems = [
    { id: 'chat', icon: '💬', label: 'Чат' },
    { id: 'documents', icon: '📄', label: 'Документы' },
    { id: 'tools', icon: '🔧', label: 'Инструменты' },
    { id: 'settings', icon: '⚙️', label: 'Настройки' },
  ]

  const handleDoubleClick = (s) => {
    setEditingId(s.id)
    setEditName(s.name)
  }

  const handleRename = (id) => {
    if (editName.trim()) {
      onRenameSession(id, editName.trim())
    }
    setEditingId(null)
  }

  const shortName = (name) => {
    if (!name || name === 'Новый чат') return 'Новый чат'
    return name.length > 28 ? name.slice(0, 28) + '…' : name
  }

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        {isOpen ? (
          <div className="logo">
            <span className="logo-icon">AI</span>
            <span className="logo-text">Agent</span>
          </div>
        ) : (
          <div className="logo-collapsed">
            <span className="logo-icon">AI</span>
          </div>
        )}
        <Button variant="ghost" onClick={() => setIsOpen(!isOpen)} className="menu-toggle">
          {isOpen ? '◀' : '▶'}
        </Button>
      </div>

      <nav className={`sidebar-nav ${isOpen ? '' : 'collapsed'}`}>
        {navItems.map(item => (
          <Button
            key={item.id}
            variant={currentPage === item.id ? 'active' : 'ghost'}
            onClick={() => onPageChange(item.id)}
            className="nav-item"
            title={item.label}
          >
            <span className="nav-icon">{item.icon}</span>
            {isOpen && <span className="nav-label">{item.label}</span>}
          </Button>
        ))}
      </nav>

      {isOpen && (
        <div className="sidebar-sessions">
          <div className="sessions-header">
            <span>Чаты</span>
            <Button variant="primary" size="sm" onClick={onNewSession}>+</Button>
          </div>
          <div className="sessions-list">
            {sessions.map(s => (
              <div
                key={s.id}
                className={`session-item ${s.id === activeSession?.id ? 'active' : ''}`}
                onClick={() => onSessionSelect(s)}
              >
                {editingId === s.id ? (
                  <input
                    className="session-rename-input"
                    value={editName}
                    onChange={e => setEditName(e.target.value)}
                    onBlur={() => handleRename(s.id)}
                    onKeyDown={e => e.key === 'Enter' && handleRename(s.id)}
                    autoFocus
                    onClick={e => e.stopPropagation()}
                  />
                ) : (
                  <>
                    <span
                      className="session-name"
                      onDoubleClick={(e) => { e.stopPropagation(); handleDoubleClick(s) }}
                      title={s.name}
                    >
                      {shortName(s.name)}
                    </span>
                    <span className="session-model">{s.model ? s.model.split('/').pop() : ''}</span>
                    <button
                      className="session-delete"
                      onClick={(e) => { e.stopPropagation(); if (confirm('Удалить чат?')) onDeleteSession(s.id) }}
                      title="Удалить чат"
                    >×</button>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  )
}

export default Sidebar