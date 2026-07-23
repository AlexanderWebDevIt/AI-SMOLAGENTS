# AI Agent

ИИ-агент с RAG, памятью и песочницей выполнения кода.

## Быстрый старт

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env под свои нужды
```

### 3. Запуск

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## API

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/agent/run` | Запрос к агенту |
| POST | `/rag/upload` | Загрузка документа |
| GET | `/api/sessions/{id}` | Получение истории сессии |

## Пример запроса

```bash
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Посчитай сумму чисел от 1 до 100", "session_id": "test"}'
```

## Структура проекта

```
AI-smolagents/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry
│   │   ├── agent/           # Agent loop logic
│   │   ├── rag/             # RAG engine
│   │   ├── memory/          # Memory storage
│   │   └── sandbox/         # Code execution
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Next.js (будущее)
└── data/                    # Хранилище данных
```

## Технологии

- **Backend**: FastAPI, Python 3.11+
- **LLM**: OpenAI-compatible API (LM Studio, OpenAI, Ollama)
- **RAG**: ChromaDB + LangChain
- **Хранение**: SQLite
- **Выполнение кода**: subprocess (sandbox)
