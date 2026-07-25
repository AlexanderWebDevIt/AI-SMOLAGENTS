import { useState } from 'react'
import Button from './Button'
import './Sidebar.css'

const Sidebar = ({
  sessions,
  activeSession,
  onSessionSelect,
  onNewSession,
  currentPage,
  onPageChange
}) => {
  const [isOpen, setIsOpen] = useState(true)

  const navItems = [
    { id: 'chat', icon: '💬', label: 'Чат' },
    { id: 'documents', icon: '📄', label: 'Документы' },
    { id: 'tools', icon: '🔧', label: 'Инструменты' },
    { id: 'settings', icon: '⚙️', label: 'Настройки' },
  ]

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
        <Button
          variant="ghost"
          onClick={() => setIsOpen(!isOpen)}
          className="menu-toggle"
        >
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
            <span>Сессии</span>
            <Button variant="primary" size="sm" onClick={onNewSession}>
              +
            </Button>
          </div>
          {sessions.map(s => (
            <Button
              key={s}
              variant={s === activeSession ? 'active' : 'ghost'}
              onClick={() => onSessionSelect(s)}
              className="session-item"
            >
              {s}
            </Button>
          ))}
        </div>
      )}
    </aside>
  )
}

export default Sidebar
