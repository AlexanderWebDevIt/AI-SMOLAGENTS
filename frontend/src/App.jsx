import { useState, useRef, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Message from './components/Message'
import ChatInput from './components/ChatInput'
import TypingIndicator from './components/TypingIndicator'
import Settings from './Settings'
import Documents from './components/Documents'
import Tools from './components/Tools'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('default')
  const [sessions, setSessions] = useState(['default'])
  const [currentPage, setCurrentPage] = useState('chat')
  const [activeModel, setActiveModel] = useState('')
  const messagesEnd = useRef(null)

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    loadSession(sessionId)
  }, [sessionId])

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    fetch(`${API_URL}/api/settings`)
      .then(res => res.json())
      .then(data => setActiveModel(data.active_model || ''))
      .catch(() => {})
  }, [currentPage])

  const loadSessions = async () => {
    try {
      const res = await fetch(`${API_URL}/api/sessions`)
      const data = await res.json()
      if (data.sessions && data.sessions.length > 0) {
        setSessions(data.sessions)
      }
    } catch (e) {}
  }

  const loadSession = async (id) => {
    try {
      const res = await fetch(`${API_URL}/api/sessions/${id}`)
      const data = await res.json()
      setMessages(data.messages ? data.messages.map(m => ({ role: m.role, content: m.content })) : [])
    } catch (e) {
      setMessages([])
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, session_id: sessionId }),
      })
      const data = await res.json()
      const assistantMsg = { role: 'assistant', content: data.reply, steps: data.steps }
      setMessages(prev => [...prev, assistantMsg])
      loadSessions()
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Ошибка соединения с сервером' }])
    }
    setLoading(false)
  }

  const handleNewSession = () => {
    const id = `session_${Date.now()}`
    setSessions(prev => [...prev, id])
    setSessionId(id)
    setMessages([])
  }

  const suggestions = [
    { text: 'Посчитай 2+2', icon: '🧮' },
    { text: 'Прочитай файл README.md', icon: '📄' },
    { text: 'Найди все Python файлы', icon: '🔍' },
  ]

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeSession={sessionId}
        onSessionSelect={setSessionId}
        onNewSession={handleNewSession}
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />

      <main className="chat">
        {currentPage === 'settings' && (
          <Settings onBack={() => setCurrentPage('chat')} />
        )}
        {currentPage === 'documents' && (
          <Documents onBack={() => setCurrentPage('chat')} />
        )}
        {currentPage === 'tools' && (
          <Tools onBack={() => setCurrentPage('chat')} />
        )}
        {currentPage === 'chat' && (
          <>
            <div className="chat-header">
              <h1>AI Ассистент</h1>
              <span className="model-badge">{activeModel || 'Не выбрана'}</span>
            </div>

            <div className="messages">
              {messages.length === 0 && (
                <div className="empty-state">
                  <div className="empty-icon">🤖</div>
                  <h2>Привет! Я ваш ИИ-ассистент</h2>
                  <p>Задайте мне вопрос или поручите задачу</p>
                  <div className="suggestions">
                    {suggestions.map((s, i) => (
                      <button key={i} onClick={() => setInput(s.text)}>
                        <span>{s.icon}</span> {s.text}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <Message
                  key={i}
                  role={msg.role}
                  content={msg.content}
                  steps={msg.steps}
                />
              ))}

              {loading && <TypingIndicator />}

              <div ref={messagesEnd} />
            </div>

            <ChatInput
              value={input}
              onChange={setInput}
              onSend={sendMessage}
              loading={loading}
            />
          </>
        )}
      </main>
    </div>
  )
}

export default App
