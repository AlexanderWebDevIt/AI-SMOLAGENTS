import { useState, useEffect } from 'react'
import Button from './Button'
import './Tools.css'

const API_URL = 'http://localhost:8000'

const fetchWithTimeout = (url, options = {}, timeout = 5000) => {
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

const Tools = ({ onBack }) => {
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    setLoading(true)
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/tools`)
      const data = await res.json()
      setTools(data.tools || [])
    } catch (e) {
      setTools([])
    }
    setLoading(false)
  }

  return (
    <div className="tools-page">
      <div className="tools-header">
        <Button variant="secondary" onClick={onBack}>
          ← Назад
        </Button>
        <h1>Инструменты</h1>
      </div>

      <div className="tools-grid">
        {loading ? (
          <div className="loading">Загрузка...</div>
        ) : tools.length === 0 ? (
          <div className="tools-empty">
            <span className="empty-icon">🔧</span>
            <p>Инструменты не загружены</p>
          </div>
        ) : (
          tools.map((tool, i) => (
            <div key={i} className="tool-card">
              <div className="tool-icon">{getToolIcon(tool.name)}</div>
              <div className="tool-info">
                <div className="tool-name">{tool.name}</div>
                <div className="tool-desc">{tool.description}</div>
                {tool.parameters && (
                  <div className="tool-params">
                    <span className="params-label">Параметры:</span>
                    {Object.entries(tool.parameters).map(([key, param]) => (
                      <div key={key} className="param-item">
                        <code>{key}</code>
                        <span className="param-type">{param.type}</span>
                        {param.description && (
                          <span className="param-desc">— {param.description}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const getToolIcon = (name) => {
  const icons = {
    read: '📖',
    write: '✏️',
    edit: '🔧',
    bash: '💻',
    grep: '🔍',
    glob: '📁',
  }
  return icons[name] || '⚙️'
}

export default Tools
