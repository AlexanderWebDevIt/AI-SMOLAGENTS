from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.agent.core import AgentLoop
from app.rag.engine import RAGEngine
from app.memory.store import MemoryStore
from app.rag.parsers import parse_file
from app.models import get_models, get_active_model, set_active_model, get_providers, set_provider, get_provider_config, save_providers, set_active_provider
import tempfile
import os

app = FastAPI(title="AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: str = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str
    steps: list = []


class ModelSelectRequest(BaseModel):
    model_id: str


class ProviderRequest(BaseModel):
    provider_id: str
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    type: str = "cloud"


@app.get("/api/models")
async def list_models():
    models = get_models()
    active = get_active_model()
    return {"models": models, "active_model": active}


@app.post("/api/models/select")
async def select_model(req: ModelSelectRequest):
    models = get_models()
    model_ids = [m["id"] for m in models]
    if req.model_id not in model_ids:
        raise HTTPException(status_code=400, detail=f"Модель '{req.model_id}' не найдена")
    set_active_model(req.model_id)
    return {"status": "ok", "active_model": req.model_id}


@app.get("/api/providers")
async def list_providers():
    providers = get_providers()
    active = get_provider_config()
    return {"providers": providers, "active": active}


@app.post("/api/providers/save")
async def save_provider(req: ProviderRequest):
    if req.provider_id == "__delete__":
        providers = get_providers()
        if req.name in providers:
            del providers[req.name]
            save_providers(providers)
        return {"status": "ok"}
    config = {
        "name": req.name or req.provider_id,
        "base_url": req.base_url,
        "api_key": req.api_key,
        "type": req.type
    }
    set_provider(req.provider_id, config)
    return {"status": "ok", "provider": req.provider_id}


class ProviderSelectRequest(BaseModel):
    provider_id: str


@app.post("/api/providers/select")
async def select_provider(req: ProviderSelectRequest):
    providers = get_providers()
    if req.provider_id not in providers:
        raise HTTPException(status_code=400, detail=f"Провайдер '{req.provider_id}' не найден")
    set_active_provider(req.provider_id)
    return {"status": "ok", "active_provider": req.provider_id, "config": providers[req.provider_id]}


@app.get("/api/settings")
async def get_settings():
    providers = get_providers()
    active_provider = get_provider_config()
    models = get_models()
    active_model = get_active_model()
    return {
        "providers": providers,
        "active_provider": active_provider,
        "models": models,
        "active_model": active_model
    }


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    docs_map = {
        "readme": "Passport.md",
        "base-agent": "base-agent.md",
    }
    filename = docs_map.get(doc_id)
    if not filename:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    project_root = os.path.dirname(os.getcwd())
    file_path = os.path.join(project_root, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Файл {filename} не найден")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"content": content, "filename": filename}


@app.get("/api/tools")
async def list_tools():
    from app.tools import get_tools
    tools = get_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in tools
        ]
    }


@app.post("/api/agent/run", response_model=ChatResponse)
async def run_agent(req: ChatRequest):
    model = req.model or get_active_model()
    agent = AgentLoop(assistant_id="main", model_override=model)
    result = agent.run(req.message, session_id=req.session_id)
    return ChatResponse(
        reply=result["result"]["output"],
        session_id=req.session_id,
        model=model,
        steps=result.get("plan", {}).get("steps", []),
    )


@app.post("/api/rag/upload")
async def upload_document(file: UploadFile, assistant_id: str = "main"):
    content = await file.read()
    # Используем временную директорию системы для безопасности
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(content)
        temp_path = tmp.name
    try:
        text = parse_file(temp_path)
        rag = RAGEngine(collection_name=f"assistant_{assistant_id}")
        rag.add_document(text, {"source": file.filename})
        chunks_count = len(text) // 1000
        return {"status": "ok", "filename": file.filename, "chunks": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@app.get("/api/sessions")
async def list_sessions():
    memory = MemoryStore()
    sessions = memory.get_all_sessions()
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    memory = MemoryStore()
    history = memory.get_recent(session_id, k=50)
    summary = memory.get_summary(session_id)
    return {"session_id": session_id, "messages": history, "summary": summary}


@app.post("/api/rag/reindex")
async def reindex_conversations(assistant_id: str = "main"):
    memory = MemoryStore()
    rag = RAGEngine(collection_name=f"assistant_{assistant_id}")
    
    last_id_file = os.path.join(os.getcwd(), "data", "last_rag_index_id.txt")
    last_indexed_id = 0
    if os.path.exists(last_id_file):
        with open(last_id_file, "r") as f:
            last_indexed_id = int(f.read().strip())
    
    conversations = memory.get_unindexed_conversations(last_indexed_id)
    
    if not conversations:
        return {"status": "ok", "message": "Нет новых conversations для индексации", "indexed": 0}
    
    # Группируем по сессиям и создаём документы
    session_msgs = {}
    for id_, session_id, role, content in conversations:
        if session_id not in session_msgs:
            session_msgs[session_id] = []
        session_msgs[session_id].append((role, content))
    
    indexed_count = 0
    for session_id, msgs in session_msgs.items():
        # Создаём документ из всей сессии
        conversation_text = f"[Сессия: {session_id}]\n"
        for role, content in msgs:
            conversation_text += f"{role}: {content}\n"
        
        rag.add_document(conversation_text, {"source": "conversation", "session_id": session_id})
        indexed_count += 1
    
    # Сохраняем последний индексированный ID
    new_last_id = max(c[0] for c in conversations)
    with open(last_id_file, "w") as f:
        f.write(str(new_last_id))
    
    return {"status": "ok", "indexed": indexed_count, "sessions": list(session_msgs.keys())}


@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Полезно для от다бке: возвращает старый HTML, если он есть."""
    html_path = os.path.join(os.path.dirname(__file__), "web.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>API is running. No web.html found.</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

