from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.agent.core import AgentLoop
from app.rag.engine import RAGEngine
from app.memory.store import MemoryStore
from app.rag.parsers import parse_file
from app.models import get_models, get_active_model, set_active_model
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


@app.post("/api/agent/run", response_model=ChatResponse)
async def run_agent(req: ChatRequest):
    model = req.model or get_active_model()
    agent = AgentLoop(assistant_id="main", model_override=model)
    result = agent.run(req.message)
    return ChatResponse(
        reply=result["result"]["output"],
        session_id=req.session_id,
        model=model,
        steps=result.get("plan", {}).get("steps", []),
    )


@app.post("/rag/upload")
async def upload_document(file: UploadFile, assistant_id: str = "main"):
    content = await file.read()
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)

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


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    memory = MemoryStore()
    history = memory.get_recent(session_id, k=50)
    return {"session_id": session_id, "messages": history}


@app.get("/", response_class=HTMLResponse)
async def web_ui():
    html_path = os.path.join(os.path.dirname(__file__), "web.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
