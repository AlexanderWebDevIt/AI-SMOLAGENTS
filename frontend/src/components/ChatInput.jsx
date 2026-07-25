import { useRef, useEffect } from 'react'
import Button from './Button'
import './ChatInput.css'

const ChatInput = ({ value, onChange, onSend, loading }) => {
  const textareaRef = useRef(null)

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

  return (
    <div className="chat-input">
      <div className="input-wrapper">
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
          disabled={loading || !value.trim()}
          className="send-btn"
        >
          →
        </Button>
      </div>
    </div>
  )
}

export default ChatInput
