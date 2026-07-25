import { useState, useEffect } from 'react'
import Button from './Button'
import './Documents.css'

const API_URL = 'http://localhost:8000'

const DOCUMENTS = [
  { id: 'readme', name: 'Passport.md', path: 'Passport.md' },
  { id: 'base-agent', name: 'base-agent.md', path: 'base-agent.md' },
]

const Documents = ({ onBack }) => {
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)

  const loadDocument = async (doc) => {
    setSelectedDoc(doc)
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/documents/${doc.id}`)
      const data = await res.json()
      setContent(data.content || 'Файл не найден')
    } catch (e) {
      setContent('Ошибка загрузки файла')
    }
    setLoading(false)
  }

  return (
    <div className="documents">
      <div className="documents-header">
        <Button variant="secondary" onClick={onBack}>
          ← Назад
        </Button>
        <h1>Документы</h1>
      </div>

      <div className="documents-layout">
        <div className="documents-list">
          <h2>Файлы проекта</h2>
          {DOCUMENTS.map(doc => (
            <div
              key={doc.id}
              className={`document-item ${selectedDoc?.id === doc.id ? 'active' : ''}`}
              onClick={() => loadDocument(doc)}
            >
              <span className="doc-icon">📄</span>
              <div className="doc-info">
                <div className="doc-name">{doc.name}</div>
                <div className="doc-path">{doc.path}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="document-viewer">
          {selectedDoc ? (
            <>
              <div className="viewer-header">
                <h3>{selectedDoc.name}</h3>
                <span className="viewer-path">{selectedDoc.path}</span>
              </div>
              <div className="viewer-content">
                {loading ? (
                  <div className="loading">Загрузка...</div>
                ) : (
                  <pre>{content}</pre>
                )}
              </div>
            </>
          ) : (
            <div className="viewer-empty">
              <span className="empty-icon">📂</span>
              <p>Выберите файл для просмотра</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Documents
