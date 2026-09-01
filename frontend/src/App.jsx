import { useState, useRef, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Message from './components/Message'
import ChatInput from './components/ChatInput'
import TypingIndicator from './components/TypingIndicator'
import Settings from './Settings'
import Documents from './components/Documents'
import Tools from './components/Tools'
import './App.css'
import './holo.css'
import Sparks from './components/Sparks'
import { useHoloSettings } from './useHoloSettings'

const API_URL = 'http://localhost:8000'

const stageIcon = (stage) => {
  const icons = {
    rag_search: '📚',
    memory: '💾',
    build_prompt: '📝',
    thinking: '🧠',
    tool: '🔧',
    task: '📋',
    generating: '✍️',
    connecting: '🔗',
    done: '✅',
    error: '❌',
    file: '📎',
  }
  return icons[stage] || '⏳'
}

const stageLabel = (stage) => {
  const labels = {
    rag_search: 'Поиск в базе знаний',
    memory: 'Загрузка памяти',
    build_prompt: 'Формирование промпта',
    thinking: 'Запрос к модели',
    tool: 'Инструмент',
    task: 'Создание задачи',
    generating: 'Формирование ответа',
    connecting: 'Подключение',
    done: 'Готово',
    error: 'Ошибка',
    file: 'Обработка файлов',
  }
  return labels[stage] || 'Обработка...'
}

const fetchWithTimeout = (url, options = {}, timeout = 10000) => {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  return fetch(url, { ...options, signal: controller.signal }).then(res => {
    clearTimeout(id)
    return res
  }).catch(err => {
    clearTimeout(id)
    throw err
  })
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [stepsLog, setStepsLog] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [sessions, setSessions] = useState([])
  const [currentPage, setCurrentPage] = useState('chat')
  const [activeModel, setActiveModel] = useState('')
  const [attachments, setAttachments] = useState([])
  const sessionLoadRef = useRef(0)
  const messagesEnd = useRef(null)
  const inputCache = useRef({})
  const abortRef = useRef(null)
  const contextInfoRef = useRef(null)
  const holo = useHoloSettings()

  useEffect(() => {
    document.getElementById('root')?.classList.toggle('holo-mode', holo.settings.enabled)
  }, [holo.settings.enabled])

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (activeSession) {
      loadSession(activeSession.id)
      setLoading(false)
      setProgress(null)
      setInput(inputCache.current[activeSession.id] || '')
      setAttachments([])
    }
  }, [activeSession?.id])

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    fetchWithTimeout(`${API_URL}/api/settings`, {}, 5000)
      .then(res => res.json())
      .then(data => setActiveModel(data.active_model || ''))
      .catch(() => {})
  }, [currentPage])

  const loadSessions = async () => {
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/sessions`, {}, 5000)
      const data = await res.json()
      if (data.sessions && data.sessions.length > 0) {
        setSessions(data.sessions)
        // Обновляем активную сессию из свежего списка (бэкенд мог переименовать)
        setActiveSession(prev => {
          if (!prev) return data.sessions[0]
          const updated = data.sessions.find(s => s.id === prev.id)
          return updated || prev
        })
      } else {
        // Нет сессий — создаём новую автоматически
        await createNewSession()
        await loadSessions()
      }
    } catch (e) {}
  }

  const createNewSession = async () => {
    try {
      const res = await fetch(`${API_URL}/api/sessions`, { method: 'POST' })
      const data = await res.json()
      inputCache.current[data.session.id] = ''
      setActiveSession(data.session)
      setMessages([])
      return data.session
    } catch (e) {
      return null
    }
  }

  const loadSession = async (id) => {
    sessionLoadRef.current += 1
    const loadId = sessionLoadRef.current
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/sessions/${id}`, {}, 5000)
      if (!res.ok) {
        if (loadId === sessionLoadRef.current) setMessages([])
        return
      }
      const data = await res.json()
      if (loadId === sessionLoadRef.current) {
        const msgs = (data.messages || []).map(m => ({
          role: m.role,
          content: m.content,
          contextInfo: m.metadata?.context_info || null,
          attachments: m.metadata?.attachments || null,
        }))
        setMessages(msgs)
      }
    } catch (e) {
      if (loadId === sessionLoadRef.current) {
        setMessages([])
      }
    }
  }

  const handleSessionSelect = (s) => {
    if (activeSession?.id) {
      inputCache.current[activeSession.id] = input
    }
    setActiveSession(s)
  }

  const handleNewSession = async () => {
    await createNewSession()
    await loadSessions()
  }

  const handleRenameSession = async (id, name) => {
    try {
      await fetch(`${API_URL}/api/sessions/${id}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      })
      setSessions(prev => prev.map(s => s.id === id ? { ...s, name } : s))
      if (activeSession?.id === id) setActiveSession(prev => ({ ...prev, name }))
    } catch (e) {}
  }

  const handleDeleteSession = async (id) => {
    try {
      await fetch(`${API_URL}/api/sessions/${id}`, { method: 'DELETE' })
      delete inputCache.current[id]
      await loadSessions()
      if (activeSession?.id === id) {
        setActiveSession(null)
        setMessages([])
      }
    } catch (e) {}
  }

  const sendMessage = async () => {
    if (loading) return
    if (!activeSession) return
    if (!input.trim() && (!attachments || attachments.length === 0)) return

    const userMsg = { role: 'user', content: input, attachments: attachments.length ? attachments : null }
    setMessages(prev => [...prev, userMsg])
    delete inputCache.current[activeSession.id]
    setInput('')
    setAttachments([])
    setLoading(true)
    setStepsLog([{ stage: 'connecting', message: 'Подключение к серверу...', timestamp: Date.now() }])
    setProgress({ stage: 'connecting', message: 'Подключение к серверу...' })

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch(`${API_URL}/api/agent/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: activeSession.id,
          attachments: attachments.map(a => ({ id: a.id })),
        }),
        signal: controller.signal,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              if (event.stage === 'done') {
                setMessages(prev => [...prev, { role: 'assistant', content: event.reply, contextInfo: contextInfoRef.current }])
                contextInfoRef.current = null
                setProgress(null)
                // Обновляем список сессий — бэкенд мог переименовать сессию
                loadSessions()
              } else if (event.stage === 'error') {
                setMessages(prev => [...prev, { role: 'assistant', content: event.message || 'Ошибка сервера' }])
                setProgress(null)
              } else if (event.stage === 'context_info') {
                contextInfoRef.current = event.data
                setProgress(event)
                setStepsLog(prev => [...prev.slice(-7), { ...event, timestamp: Date.now() }])
              } else {
                setProgress(event)
                setStepsLog(prev => [...prev.slice(-7), { ...event, timestamp: Date.now() }])
              }
            } catch (e) {}
          }
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') return
      setMessages(prev => [...prev, { role: 'assistant', content: 'Ошибка соединения с сервером. Проверьте, запущен ли бэкенд (http://localhost:8000)' }])
    }
    abortRef.current = null
    setLoading(false)
    setProgress(null)
  }

  const stopMessage = () => {
    abortRef.current?.abort()
    abortRef.current = null
    setLoading(false)
    setProgress(null)
  }

  const suggestions = [
    { text: 'Посчитай 2+2', icon: '🧮' },
    { text: 'Прочитай файл README.md', icon: '📄' },
    { text: 'Найди все Python файлы', icon: '🔍' },
  ]

  const appClass = [
    'app',
    holo.settings.enabled && 'holo-mode',
    holo.settings.enabled && !holo.settings.float && 'no-float',
    holo.settings.enabled && !holo.settings.scan && 'no-scan',
    holo.settings.enabled && !holo.settings.sheen && 'no-sheen',
  ].filter(Boolean).join(' ')

  return (
    <>
      {holo.settings.enabled && <div className="holo-scene" aria-hidden="true" />}
      {holo.settings.enabled && <Sparks on={holo.settings.sparks} />}
      <div className={appClass}>
        <Sidebar
          sessions={sessions}
          activeSession={activeSession}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
          onRenameSession={handleRenameSession}
          onDeleteSession={handleDeleteSession}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />

      <main className="chat">
        {currentPage === 'settings' && (
          <Settings onBack={() => setCurrentPage('chat')} holo={holo} />
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
                  <p>Задайте мне вопрос, прикрепите файл или поручите задачу</p>
                  <div className="suggestions">
                    {suggestions.map((s, i) => (
<button key={i} onClick={() => { setInput(s.text); if (activeSession?.id) inputCache.current[activeSession.id] = s.text }}>
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
                  contextInfo={msg.contextInfo}
                  attachments={msg.attachments}
                />
              ))}

              {loading && (
            <div className="agent-progress">
              <div className="progress-current">
                <span className={`progress-icon ${progress?.stage || ''}`}>
                  {stageIcon(progress?.stage)}
                </span>
                <div className="progress-info">
                  <span className="progress-label">{stageLabel(progress?.stage)}</span>
                  <span className="progress-detail">
                    {progress?.stage === 'tool' && progress?.tool
                      ? `${progress.tool}${progress.args ? '(' + JSON.stringify(progress.args).replace(/["']/g, '').slice(0, 60) + ')' : ''}`
                      : progress?.message || ''
                    }
                  </span>
                </div>
                <button className="stop-btn" onClick={stopMessage} title="Остановить">✕</button>
              </div>

              {stepsLog.length > 1 && (
                <div className="progress-recent">
                  {stepsLog.slice(0, -1).map((step, i) => (
                    <span key={i} className={`recent-step ${step.stage}`} title={step.message}>
                      {stageIcon(step.stage)}
                    </span>
                  ))}
                </div>
              )}

              <div className="progress-bar">
                <div className="progress-fill" />
              </div>
            </div>
          )}

              <div ref={messagesEnd} />
            </div>

            <ChatInput
              value={input}
              onChange={setInput}
              onSend={sendMessage}
              loading={loading}
              attachments={attachments}
              onAttachmentsChange={setAttachments}
            />
          </>
        )}
      </main>
      </div>

      {/* Плавающая кнопка-тумблер голограммы — всегда видна,
          чтобы режим было легко найти и выключить */}
      <button
        className={`holo-fab ${holo.settings.enabled ? 'on' : ''}`}
        onClick={() => holo.toggle('enabled')}
        title={holo.settings.enabled ? 'Голограмма: ВКЛ (нажмите, чтобы выключить)' : 'Голограмма: ВЫКЛ (нажмите, чтобы включить)'}
      >
        <span className="holo-fab-icon">◐</span>
        <span className="holo-fab-label">Голограмма</span>
      </button>
    </>
  )
}

export default App