import subprocess
from app.tools.base import BaseTool
from app.config import PROJECT_ROOT, is_bash_command_allowed


class BashTool(BaseTool):
    name = "bash"
    description = "Execute shell command in project root (read-only git, no destructive ops)"
    parameters = {
        "command": {"type": "string", "description": "Command to execute"},
        "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60},
    }

    def execute(self, command: str, timeout: int = 60) -> str:
        allowed, reason = is_bash_command_allowed(command)
        if not allowed:
            return f"Error: {reason}"
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=PROJECT_ROOT,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output[:5000] if output else "Command executed (no output)"
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"
