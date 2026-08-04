import { useState } from 'react'
import './Message.css'

const API_URL = 'http://localhost:8000'

const ContextPanel = ({ info }) => {
  const [open, setOpen] = useState(false)
  if (!info) return null

  const sections = [
    { label: 'Фрагменты из базы знаний (RAG)', value: info.rag_chunks },
    { label: 'Сообщений в истории', value: info.history_count },
    { label: 'Фактов из других сессий', value: info.cross_memory_count },
  ]

  return (
    <div className="context-panel">
      <button className="context-toggle" onClick={() => setOpen(!open)}>
        <span>🧠</span> Контекст {open ? '▲' : '▼'}
      </button>
      {open && (
        <div className="context-body">
          {sections.map((s, i) => (
            <div key={i} className="context-row">
              <span className="context-label">{s.label}</span>
              <span className="context-value">{s.value}</span>
            </div>
          ))}
          {info.summary && (
            <div className="context-row">
              <span className="context-label">Резюме диалога</span>
              <span className="context-value">{info.summary}</span>
            </div>
          )}
          {info.system_prompt && (
            <div className="context-row">
              <span className="context-label">Фрагмент системного промпта</span>
              <span className="context-value context-mono">{info.system_prompt}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const Attachments = ({ attachments }) => {
  if (!attachments || attachments.length === 0) return null

  return (
    <div className="message-attachments">
      {attachments.map(att => {
        if (att.type === 'image') {
          return (
            <a
              key={att.id}
              href={API_URL + att.url}
              target="_blank"
              rel="noopener noreferrer"
              className="attachment-image-link"
              title={att.filename}
            >
              <img src={API_URL + att.url} alt={att.filename} className="attachment-image" />
            </a>
          )
        }
        return (
          <a
            key={att.id}
            href={API_URL + att.url}
            download={att.filename}
            className="attachment-doc"
            title={att.filename}
          >
            <span className="attachment-doc-icon">📄</span>
            <span className="attachment-doc-name">{att.filename}</span>
          </a>
        )
      })}
    </div>
  )
}

const Message = ({ role, content, steps, contextInfo, attachments }) => {
  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        <Attachments attachments={attachments} />
        <div className="message-text">{content}</div>
        {role === 'assistant' && <ContextPanel info={contextInfo} />}
        {steps && steps.length > 0 && (
          <div className="tool-steps">
            <details>
              <summary>Инструментов: {steps.length}</summary>
              {steps.map((step, i) => (
                <div key={i} className="step">
                  <code>{step.tool}</code>
                  <span className="step-args">{JSON.stringify(step.args)}</span>
                </div>
              ))}
            </details>
          </div>
        )}
      </div>
    </div>
  )
}

export default Message