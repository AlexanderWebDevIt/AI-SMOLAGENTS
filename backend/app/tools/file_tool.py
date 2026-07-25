import os
from app.tools.base import BaseTool


class ReadTool(BaseTool):
    name = "read"
    description = "Read file contents"
    parameters = {
        "file_path": {"type": "string", "description": "Path to file"},
        "offset": {"type": "integer", "description": "Start line (1-indexed)", "default": 1},
        "limit": {"type": "integer", "description": "Max lines to read", "default": 2000},
    }

    def execute(self, file_path: str, offset: int = 1, limit: int = 2000) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            start = max(0, offset - 1)
            end = min(len(lines), start + limit)
            result = []
            for i, line in enumerate(lines[start:end], start=start + 1):
                result.append(f"{i}: {line.rstrip()}")
            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"


class WriteTool(BaseTool):
    name = "write"
    description = "Create or overwrite file"
    parameters = {
        "file_path": {"type": "string", "description": "Path to file"},
        "content": {"type": "string", "description": "File content"},
    }

    def execute(self, file_path: str, content: str) -> str:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"OK: {file_path}"
        except Exception as e:
            return f"Error: {e}"


class EditTool(BaseTool):
    name = "edit"
    description = "Edit file by string replacement"
    parameters = {
        "file_path": {"type": "string", "description": "Path to file"},
        "old_string": {"type": "string", "description": "Text to replace"},
        "new_string": {"type": "string", "description": "Replacement text"},
    }

    def execute(self, file_path: str, old_string: str, new_string: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if old_string not in content:
                return f"Error: old_string not found in {file_path}"
            if content.count(old_string) > 1:
                return f"Error: multiple matches for old_string in {file_path}"
            new_content = content.replace(old_string, new_string, 1)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"OK: {file_path}"
        except Exception as e:
            return f"Error: {e}"
