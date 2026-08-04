import { useRef, useEffect, useState } from 'react'
import Button from './Button'
import './ChatInput.css'

const API_URL = 'http://localhost:8000'

const ChatInput = ({ value, onChange, onSend, loading, attachments, onAttachmentsChange }) => {
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [value])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return

    setUploading(true)
    try {
      const uploaded = []
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        const res = await fetch(API_URL + '/api/upload', {
          method: 'POST',
          body: formData,
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          alert(err.detail || 'Ошибка загрузки файла')
          continue
        }
        const data = await res.json()
        uploaded.push(data.file)
      }
      if (uploaded.length) {
        onAttachmentsChange([...(attachments || []), ...uploaded])
      }
    } catch (err) {
      alert('Ошибка соединения с сервером при загрузке файла')
    }
    setUploading(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removeAttachment = (id) => {
    onAttachmentsChange((attachments || []).filter(a => a.id !== id))
  }

  return (
    <div className="chat-input">
      {attachments && attachments.length > 0 && (
        <div className="attachments-preview">
          {attachments.map(att => (
            <div key={att.id} className="attachment-chip">
              {att.type === 'image' ? (
                <img src={API_URL + att.url} alt={att.filename} className="attachment-thumb" />
              ) : (
                <span className="attachment-icon">📄</span>
              )}
              <span className="attachment-name" title={att.filename}>{att.filename}</span>
              <button className="attachment-remove" onClick={() => removeAttachment(att.id)} title="Удалить">×</button>
            </div>
          ))}
        </div>
      )}

      <div className="input-wrapper">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".png,.jpg,.jpeg,.gif,.webp,.bmp,.svg,.txt,.md,.pdf,.docx,.doc,.xlsx,.xls,.csv,.py,.js,.jsx,.ts,.tsx,.json,.html,.css,.yaml,.yml,.toml,.sh,.bat,.ps1"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <Button
          variant="ghost"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading || uploading}
          className="attach-btn"
          title="Прикрепить файл"
        >
          {uploading ? '⏳' : '📎'}
        </Button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Введите сообщение..."
          rows="1"
          disabled={loading}
        />
        <Button
          variant="primary"
          onClick={onSend}
          disabled={loading || (!value.trim() && (!attachments || attachments.length === 0))}
          className="send-btn"
        >
          →
        </Button>
      </div>
    </div>
  )
}

export default ChatInput