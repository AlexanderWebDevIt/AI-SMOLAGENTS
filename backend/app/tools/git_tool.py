import subprocess
from app.tools.base import BaseTool
from app.config import PROJECT_ROOT


class GitTool(BaseTool):
    name = "git"
    description = "Read-only Git operations: status and diff"
    parameters = {
        "operation": {"type": "string", "description": "Git operation: status or diff"},
    }

    def execute(self, operation: str, message: str = None, branch: str = None) -> str:
        op = operation.strip().lower()
        if op not in ("status", "diff"):
            return f"Error: only 'status' and 'diff' are allowed, got '{operation}'"
        try:
            result = subprocess.run(
                ["git", op],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output[:5000] if output else f"Git {op} completed"
        except Exception as e:
            return f"Error: {e}"
