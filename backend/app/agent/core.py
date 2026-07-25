import json
import os
from openai import OpenAI
from app.rag.engine import RAGEngine
from app.memory.store import MemoryStore
from app.models import get_active_model, get_provider_config
from app.tools import get_tools, get_tool, tools_to_prompt


class AgentLoop:
    def __init__(self, assistant_id: str, max_steps: int = 10, model_override: str = None):
        self.assistant_id = assistant_id
        self.max_steps = max_steps
        self._init_client()
        self.model = model_override or get_active_model()
        self.rag = RAGEngine(collection_name=f"assistant_{assistant_id}")
        self.memory = MemoryStore()

    def _init_client(self):
        config = get_provider_config()
        self.client = OpenAI(
            base_url=config.get("base_url", "http://localhost:1234/v1"),
            api_key=config.get("api_key", "lm-studio"),
        )

    def run(self, user_message: str, session_id: str = "default") -> dict:
        self._init_client()
        self.model = get_active_model()

        context_chunks = self.rag.search(user_message, k=5)
        chat_history = self.memory.get_recent(session_id, k=20)
        summary = self.memory.get_summary(session_id)

        system_prompt = self._build_system_prompt(context_chunks, chat_history, summary)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        steps = []
        for step in range(self.max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )
            reply = response.choices[0].message.content

            tool_call = self._parse_tool_call(reply)
            if not tool_call:
                break

            tool_name = tool_call["tool"]
            tool_args = tool_call["args"]
            tool = get_tool(tool_name)

            if tool:
                result = tool.execute(**tool_args)
                steps.append({"tool": tool_name, "args": tool_args, "result": result[:500]})
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": f"Tool result:\n{result[:3000]}"})
            else:
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": f"Tool '{tool_name}' not found. Try another tool or answer directly."})

        final_output = reply

        self.memory.save_message(session_id, "user", user_message)
        self.memory.save_message(session_id, "assistant", final_output)

        conversation_text = f"[Сессия: {session_id}] Пользователь: {user_message}\nАссистент: {final_output}"
        self.rag.add_document(conversation_text, {"source": "conversation", "session_id": session_id})

        history = self.memory.get_recent(session_id, k=100)
        if len(history) % 10 == 0 and len(history) >= 10:
            self._summarize(session_id, history)

        return {
            "plan": {"steps": steps},
            "result": {"output": final_output, "steps": steps}
        }

    def _build_system_prompt(self, context: list, history: list, summary: str = None) -> str:
        tools_desc = tools_to_prompt()

        prompt = f"""Ты — ИИ-ассистент с доступом к инструментам.

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{tools_desc}

ПРАВИЛА:
1. Если нужен инструмент, вызови его через формат: [TOOL: имя_инструмента(args)]
2. Примеры вызова:
   - [TOOL: read(file_path="src/main.py")]
   - [TOOL: bash(command="ls -la")]
   - [TOOL: grep(pattern="def.*error", path="src", include="*.py")]
3. Если инструмент не нужен — отвечай сразу
4. Не выдумывай результаты инструментов — всегда вызывай их
5. Отвечай на языке пользователя
"""

        if summary:
            prompt += f"\n### РЕЗЮМЕ ПРОШЛЫХ ДИАЛОГОВ:\n{summary}\n"

        if context:
            doc_chunks = [c for c in context if c.metadata.get("source") != "conversation"]
            conv_chunks = [c for c in context if c.metadata.get("source") == "conversation"]

            if doc_chunks:
                prompt += "\n### КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:\n"
                for c in doc_chunks:
                    prompt += f"- {c.page_content[:500]}\n"

            if conv_chunks:
                prompt += "\n### ПРОШЛЫЕ РАЗГОВОРЫ:\n"
                for c in conv_chunks:
                    prompt += f"- {c.page_content[:500]}\n"

        if history:
            prompt += "\n### ИСТОРИЯ ДИАЛОГА:\n"
            for h in history[-10:]:
                prompt += f"{h['role']}: {h['content'][:200]}\n"

        return prompt

    def _parse_tool_call(self, text: str):
        import re
        match = re.search(r'\[TOOL:\s*(\w+)\((.*?)\)\]', text, re.DOTALL)
        if not match:
            return None

        tool_name = match.group(1)
        args_str = match.group(2)

        args = {}
        for pair in args_str.split(","):
            pair = pair.strip()
            if "=" in pair:
                key, val = pair.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                args[key] = val

        return {"tool": tool_name, "args": args}

    def _summarize(self, session_id: str, history: list):
        try:
            history_text = "\n".join([f"{h['role']}: {h['content'][:300]}" for h in history[-50:]])
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты создаёшь краткое резюме диалога. Пиши на русском, 2-4 предложения, ключевые факты и решения."},
                    {"role": "user", "content": f"Сделай резюме этого диалога:\n\n{history_text}"},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            summary = response.choices[0].message.content
            self.memory.save_summary(session_id, summary)
            print(f"[Memory] Сессия {session_id} суммаризирована")
        except Exception as e:
            print(f"[Memory] Ошибка суммаризации: {e}")
