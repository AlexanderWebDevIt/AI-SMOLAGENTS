import { useState, useEffect } from 'react'
import Button from './components/Button'
import './Settings.css'

const API_URL = 'http://localhost:8000'

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

export default function Settings({ onBack }) {
  const [providers, setProviders] = useState({})
  const [activeProvider, setActiveProvider] = useState(null)
  const [models, setModels] = useState([])
  const [activeModel, setActiveModel] = useState('')
  const [editingProvider, setEditingProvider] = useState(null)
  const [formData, setFormData] = useState({ name: '', base_url: '', api_key: '', type: 'cloud' })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [modelSearch, setModelSearch] = useState('')

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/settings`, {}, 15000)
      const data = await res.json()
      setProviders(data.providers || {})
      setActiveProvider(data.active_provider || null)
      setModels(data.models || [])
      setActiveModel(data.active_model || '')
    } catch (e) {
      setMessage('Ошибка загрузки настроек: сервер недоступен')
    }
  }

  const handleSaveProvider = async () => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/providers/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: editingProvider, ...formData }),
      }, 15000)
      if (res.ok) {
        setMessage('Провайдер сохранён')
        setEditingProvider(null)
        await loadSettings()
      } else {
        const err = await res.text().catch(() => '')
        setMessage('Ошибка сохранения: ' + err.slice(0, 100))
      }
    } catch (e) {
      setMessage('Ошибка сохранения: сервер недоступен')
    }
    setLoading(false)
  }

  const handleSelectProvider = async (providerId) => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/providers/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId }),
      }, 15000)
      if (res.ok) {
        const data = await res.json()
        setActiveProvider(data.config)
        setMessage(`Активный провайдер: ${data.config.name}`)
        await loadSettings()
      } else {
        const err = await res.text().catch(() => '')
        setMessage('Ошибка выбора провайдера: ' + err.slice(0, 100))
      }
    } catch (e) {
      setMessage('Ошибка выбора провайдера: сервер недоступен')
    }
    setLoading(false)
  }

  const handleSelectModel = async (modelId) => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/models/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      })
      if (res.ok) {
        setActiveModel(modelId)
        setMessage(`Выбрана модель: ${modelId}`)
      } else {
        const err = await res.text().catch(() => '')
        setMessage('Ошибка выбора модели: ' + err.slice(0, 100))
      }
    } catch (e) {
      setMessage('Ошибка выбора модели: сервер недоступен')
    }
    setLoading(false)
  }

  const handleManualModel = async () => {
    const modelId = prompt('Введите ID модели:')
    if (!modelId) return
    setLoading(true)
    setMessage('')
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/models/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      })
      if (res.ok) {
        setActiveModel(modelId)
        setMessage(`Установлена модель: ${modelId}`)
      } else {
        const err = await res.text().catch(() => '')
        setMessage('Ошибка: ' + err.slice(0, 100))
      }
    } catch (e) {
      setMessage('Ошибка: сервер недоступен')
    }
    setLoading(false)
  }

  const startEdit = (providerId) => {
    const provider = providers[providerId] || {}
    setEditingProvider(providerId)
    setFormData({
      name: provider.name || providerId,
      base_url: provider.base_url || '',
      api_key: provider.api_key || '',
      type: provider.type || 'cloud'
    })
  }

  const addCustomProvider = () => {
    const id = `custom_${Date.now()}`
    setEditingProvider(id)
    setFormData({ name: '', base_url: '', api_key: '', type: 'cloud' })
  }

  const handleDeleteProvider = async (providerId) => {
    if (!confirm('Удалить провайдер?')) return
    setLoading(true)
    setMessage('')
    try {
      const res = await fetchWithTimeout(`${API_URL}/api/providers/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: '__delete__', name: providerId }),
      }, 15000)
      if (res.ok) {
        setMessage('Провайдер удалён')
        await loadSettings()
      } else {
        setMessage('Ошибка удаления')
      }
    } catch (e) {
      setMessage('Ошибка удаления: сервер недоступен')
    }
    setLoading(false)
  }

  return (
    <div className="settings">
      <div className="settings-header">
        <Button variant="secondary" onClick={onBack}>
          ← Назад
        </Button>
        <h1>Настройки</h1>
      </div>

      {message && <div className="settings-message">{message}</div>}

      <div className="settings-columns">
        <section className="providers-column">
          <div className="column-title">
            <h2>Провайдеры</h2>
            <Button variant="primary" onClick={addCustomProvider}>
              + Добавить
            </Button>
          </div>
          <div className="providers-grid">
            {Object.entries(providers)
              .sort(([a], [b]) => {
                const aActive = activeProvider?.name === providers[a]?.name
                const bActive = activeProvider?.name === providers[b]?.name
                return bActive - aActive
              })
              .map(([id, provider]) => (
                <div
                  key={id}
                  className={`provider-card ${activeProvider?.name === provider.name ? 'active' : ''}`}
                >
                  <div className="provider-info">
                    <div className="provider-name">
                      {provider.name}
                      {activeProvider?.name === provider.name && (
                        <span className="active-badge">Активен</span>
                      )}
                    </div>
                    <div className="provider-type">{provider.type === 'local' ? 'Локальный' : 'Облачный'}</div>
                    <div className="provider-url">{provider.base_url}</div>
                  </div>
                  <div className="provider-actions">
                    <Button
                      variant={activeProvider?.name === provider.name ? 'active' : 'primary'}
                      onClick={() => handleSelectProvider(id)}
                      disabled={loading || activeProvider?.name === provider.name}
                    >
                      {activeProvider?.name === provider.name ? '✓' : 'Выбрать'}
                    </Button>
                    <Button variant="secondary" onClick={() => startEdit(id)}>
                      Редактировать
                    </Button>
                    {id.startsWith('custom_') && (
                      <Button variant="danger" onClick={() => handleDeleteProvider(id)}>
                        Удалить
                      </Button>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </section>

        <section className="models-column">
          <div className="column-title">
            <h2>Модели</h2>
            <div className="models-actions">
              <input
                type="text"
                className="model-search"
                placeholder="Поиск модели..."
                value={modelSearch}
                onChange={(e) => setModelSearch(e.target.value)}
              />
              <Button variant="secondary" onClick={handleManualModel}>
                + Ввести вручную
              </Button>
            </div>
          </div>
          {models.length === 0 ? (
            <p className="no-models">Нет доступных моделей. Выберите провайдер или введите ID модели вручную.</p>
          ) : (
            <div className="models-list">
              {models
                .filter(m => m.type === 'chat')
                .filter(m => m.name.toLowerCase().includes(modelSearch.toLowerCase()) || m.id.toLowerCase().includes(modelSearch.toLowerCase()))
                .sort((a, b) => {
                  const aActive = activeModel === a.id
                  const bActive = activeModel === b.id
                  return bActive - aActive
                })
                .map((model) => (
                  <div
                    key={model.id}
                    className={`model-item ${activeModel === model.id ? 'active' : ''}`}
                  >
                    <div className="model-info">
                      <div className="model-name">{model.name}</div>
                      <div className="model-provider">{model.owned_by}</div>
                    </div>
                    <Button
                      variant={activeModel === model.id ? 'active' : 'primary'}
                      onClick={() => handleSelectModel(model.id)}
                      disabled={loading || activeModel === model.id}
                    >
                      {activeModel === model.id ? 'Активна' : 'Выбрать'}
                    </Button>
                  </div>
                ))}
            </div>
          )}
        </section>
      </div>

      {editingProvider && (
        <section className="edit-form">
          <h2>{editingProvider.startsWith('custom_') && !providers[editingProvider] ? 'Добавить провайдер' : `Редактировать: ${editingProvider}`}</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Название</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Base URL</label>
              <input
                type="text"
                value={formData.base_url}
                onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                placeholder="http://localhost:1234/v1"
              />
            </div>
            <div className="form-group">
              <label>API Key</label>
              <input
                type="password"
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                placeholder="lm-studio"
              />
            </div>
            <div className="form-group">
              <label>Тип</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              >
                <option value="local">Локальный</option>
                <option value="cloud">Облачный</option>
              </select>
            </div>
          </div>
          <div className="form-actions">
            <Button variant="primary" onClick={handleSaveProvider} disabled={loading}>
              Сохранить
            </Button>
            <Button variant="secondary" onClick={() => setEditingProvider(null)}>
              Отмена
            </Button>
          </div>
        </section>
      )}
    </div>
  )
}
