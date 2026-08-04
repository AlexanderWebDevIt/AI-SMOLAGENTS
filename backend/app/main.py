from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
import asyncio
import json
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.agent.core import AgentLoop
from app.rag.engine import get_rag_engine
from app.memory.store import MemoryStore
from app.rag.parsers import parse_file
from app.files import save_upload, get_upload_path, delete_upload

# Singleton MemoryStore — avoids leaking SQLite connections
_memory_store = None


def get_memory() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
from app.models import get_models, get_active_model, set_active_model, get_providers, set_provider, get_provider_config, save_providers, set_active_provider
import tempfile
import os

_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")

app = FastAPI(title="AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(_FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIST, "assets")), name="frontend_assets")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: str = None
    attachments: list = []


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str
    steps: list = []
    context_info: dict = None


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


@app.get("/api/health")
async def health_check():
    """Quick health check - always responds immediately."""
    return {"status": "ok"}


@app.post("/api/agent/run", response_model=ChatResponse)
async def run_agent(req: ChatRequest):
    model = req.model or get_active_model()
    agent = AgentLoop(assistant_id="main", model_override=model)
    result = agent.run(req.message, session_id=req.session_id, attachments=req.attachments or [])
    return ChatResponse(
        reply=result["result"]["output"],
        session_id=req.session_id,
        model=model,
        steps=result.get("plan", {}).get("steps", []),
        context_info=result.get("context_info"),
    )


@app.post("/api/agent/stream")
async def stream_agent(req: ChatRequest):
    queue = asyncio.Queue()

    memory = get_memory()
    info = memory.get_session_info(req.session_id)
    if not info:
        name = (req.message[:50] + "...") if len(req.message) > 50 else req.message
        memory.create_session(req.session_id, name=name, model=req.model or get_active_model())
    elif info["name"] == "Новый чат":
        name = (req.message[:50] + "...") if len(req.message) > 50 else req.message
        memory.rename_session(req.session_id, name)

    agent_holder = {}

    def on_progress(event: dict):
        queue.put_nowait(event)

    async def run_agent():
        model = req.model or get_active_model()
        loop = asyncio.get_event_loop()
        agent = AgentLoop(assistant_id="main", model_override=model, on_progress=on_progress)
        agent_holder["agent"] = agent
        await loop.run_in_executor(None, agent.run, req.message, req.session_id, req.attachments or [])

    async def event_stream():
        task = asyncio.create_task(run_agent())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=300)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("stage") == "done":
                        break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'stage': 'error', 'message': 'Превышено время ожидания (5 мин)'})}\n\n"
                    break
        except asyncio.CancelledError:
            pass
        finally:
            agent = agent_holder.get("agent")
            if agent:
                agent.cancel()
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/upload")
async def upload_file(file: UploadFile):
    """Upload a file attachment for chat (image, text, document)."""
    content = await file.read()
    try:
        meta = save_upload(content, file.filename or "unnamed")
        return {"status": "ok", "file": meta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {e}")


@app.get("/api/files/{file_id}")
async def get_file(file_id: str):
    """Return an uploaded file (image preview or download)."""
    path = get_upload_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path)


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file."""
    delete_upload(file_id)
    return {"status": "ok"}


@app.post("/api/rag/upload")
async def upload_document(file: UploadFile, assistant_id: str = "main"):
    content = await file.read()
    # Используем временную директорию системы для безопасности
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(content)
        temp_path = tmp.name
    try:
        text = parse_file(temp_path)
        rag = get_rag_engine(collection_name=f"assistant_{assistant_id}")
        rag.add_document(text, {"source": file.filename})
        chunks_count = len(text) // 1000
        return {"status": "ok", "filename": file.filename, "chunks": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


class RenameRequest(BaseModel):
    name: str


@app.get("/api/sessions")
async def list_sessions():
    memory = get_memory()
    sessions = memory.get_all_sessions()
    return {"sessions": sessions}


@app.post("/api/sessions")
async def create_session():
    import uuid
    session_id = str(uuid.uuid4())
    model = get_active_model()
    memory = get_memory()
    info = memory.create_session(session_id, model=model)
    return {"session": info}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    memory = get_memory()
    info = memory.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Сессия не найдена")
    history = memory.get_recent(session_id, k=50)
    summary = memory.get_summary(session_id)
    return {"session": info, "messages": history, "summary": summary}


@app.post("/api/sessions/{session_id}/rename")
async def rename_session(session_id: str, req: RenameRequest):
    memory = get_memory()
    memory.rename_session(session_id, req.name)
    return {"status": "ok"}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    memory = get_memory()
    memory.delete_session(session_id)
    return {"status": "ok"}


@app.post("/api/rag/reindex")
async def reindex_conversations(assistant_id: str = "main"):
    memory = get_memory()
    rag = get_rag_engine(collection_name=f"assistant_{assistant_id}")
    
    last_id_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "last_rag_index_id.txt")
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
    index_path = os.path.join(_FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    html_path = os.path.join(os.path.dirname(__file__), "web.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>API is running. Build frontend with: cd frontend && npm run build</h1>")


def start_server():
    # Pre-warm RAG engine to avoid slow first request
    try:
        from app.rag.engine import prewarm_rag
        prewarm_rag()
    except Exception:
        pass
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)


if __name__ == "__main__":
    start_server()

