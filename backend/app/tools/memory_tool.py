from app.memory.store import MemoryStore
from app.rag.engine import RAGEngine
from app.tools.base import BaseTool


class SessionHistoryTool(BaseTool):
    name = "session_history"
    description = "Get conversation history for a session"
    parameters = {
        "session_id": {"type": "string", "description": "Session identifier"},
        "limit": {"type": "integer", "description": "Maximum number of messages to return", "default": 20},
    }

    def execute(self, session_id: str, limit: int = 20) -> str:
        try:
            memory_store = MemoryStore()
            history = memory_store.get_recent(session_id, k=limit)
            if not history:
                return f"No conversation history found for session {session_id}"
            
            result = []
            for msg in history[-limit:]:
                result.append(f"{msg['role']}: {msg['content'][:200]}")
            
            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"


class SessionSearchTool(BaseTool):
    name = "session_search"
    description = "Search past sessions via RAG for relevant information"
    parameters = {
        "query": {"type": "string", "description": "Search query"},
        "limit": {"type": "integer", "description": "Maximum number of results to return", "default": 5},
    }

    def execute(self, query: str, limit: int = 5) -> str:
        try:
            rag_engine = RAGEngine(collection_name="sessions")
            results = rag_engine.search(query, k=limit)
            
            if not results:
                return f"No relevant sessions found for query '{query}'"
            
            result = []
            for doc in results[:limit]:
                result.append(f"Session: {doc.metadata.get('session_id', 'unknown')}\n{doc.page_content[:300]}")
            
            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"


class SummarizeTool(BaseTool):
    name = "summarize"
    description = "Create summary of session or content"
    parameters = {
        "text": {"type": "string", "description": "Text to summarize"},
        "max_length": {"type": "integer", "description": "Maximum length of summary", "default": 100},
    }

    def execute(self, text: str, max_length: int = 100) -> str:
        try:
            # This is a simplified implementation - in practice you'd use an LLM
            words = text.split()
            if len(words) <= max_length:
                return text
            
            summary = " ".join(words[:max_length])
            return f"{summary}... (truncated)"
        except Exception as e:
            return f"Error: {e}"