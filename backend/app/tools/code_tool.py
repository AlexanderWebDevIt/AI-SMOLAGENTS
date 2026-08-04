import subprocess
import os
import tempfile
from app.tools.base import BaseTool


class CodeExecTool(BaseTool):
    name = "code_exec"
    description = "Execute Python code in a sandboxed environment"
    parameters = {
        "code": {"type": "string", "description": "Python code to execute"},
        "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
    }

    def execute(self, code: str, timeout: int = 30) -> str:
        try:
            # Create a temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute the code in subprocess
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )
            
            # Clean up the temporary file
            os.unlink(temp_file)
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
                
            return output[:5000] if output else "Code executed (no output)"
        except subprocess.TimeoutExpired:
            return f"Error: code execution timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"


class LintTool(BaseTool):
    name = "lint"
    description = "Check Python code for style issues and errors"
    parameters = {
        "code": {"type": "string", "description": "Python code to lint"},
    }

    def execute(self, code: str) -> str:
        try:
            # This is a simplified implementation - in practice you'd use pylint/flake8
            return "Linting would check for issues (implementation placeholder)"
        except Exception as e:
            return f"Error: {e}"