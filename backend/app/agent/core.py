import json
import os
from openai import OpenAI
from app.rag.engine import RAGEngine
from app.memory.store import MemoryStore
from app.models import get_active_model


class AgentLoop:
    def __init__(self, assistant_id: str, max_steps: int = 10, model_override: str = None):
        self.assistant_id = assistant_id
        self.max_steps = max_steps
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "lm-studio"),
        )
        self.model = model_override or get_active_model()
        self.rag = RAGEngine(collection_name=f"assistant_{assistant_id}")
        self.memory = MemoryStore()

    def run(self, user_message: str, session_id: str = "default") -> dict:
        """
        Выполняет прямой RAG-запрос: поиск контекста -> построение промпта -> ответ LLM.
        """
        # 1. Поиск контекста в RAG
        context_chunks = self.rag.search(user_message, k=3)
        
        # 2. Получение истории диалога
        chat_history = self.memory.get_recent(session_id, k=20)

        # 3. Сборка промпта
        system_prompt = self._build_prompt(context_chunks, chat_history)

        # 4. Прямой запрос к модели
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
            )
            final_output = response.choices[0].message.content
        except Exception as e:
            final_output = f"Ошибка при запросе к модели: {str(e)}"

        # 5. Сохранение истории
        self.memory.save_message(session_id, "user", user_message)
        self.memory.save_message(session_id, "assistant", final_output)

        # Возвращаем структуру, совместимую с текущим API (main.py)
        return {
            "plan": {"steps": []}, 
            "result": {"output": final_output, "steps": []}
        }

    def _build_prompt(self, context: list, history: list) -> str:
        prompt = "Ты — полезный ИИ-ассистент. Отвечай на вопросы пользователя, используя предоставленный контекст и историю диалога.\n"
        
        if context:
            prompt += "\n### КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:\n"
            for c in context:
                prompt += f"- {c.page_content[:500]}\n"
        
        if history:
            prompt += "\n### ИСТОРИЯ ДИАЛОГА:\n"
            for h in history[-10:]:
                prompt += f"{h['role']}: {h['content'][:200]}\n"
        
        prompt += "\nОтвечай на языке пользователя. Если в контексте нет ответа, скажи об этом, но не выдумывай."
        return prompt
