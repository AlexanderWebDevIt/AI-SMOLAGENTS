import importlib.util
import json
import os
import subprocess
from app.tools.base import BaseTool
from app.config import PROJECT_ROOT, is_bash_command_allowed

MAX_OUTPUT = 5000
DEFAULT_TIMEOUT = 120


class HooksMCPTool(BaseTool):
    name = "hooks_mcp"
    description = "Safely run build, test, lint hooks. Operations: detect, build, test, lint, run"
    parameters = {
        "operation": {
            "type": "string",
            "description": "Operation: detect (list available hooks), build, test, lint, run (run specific npm script)"
        },
        "script": {
            "type": "string",
            "description": "npm script name to run (for operation=run)",
            "default": ""
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds",
            "default": DEFAULT_TIMEOUT
        },
    }

    def execute(self, operation: str, script: str = "", timeout: int = DEFAULT_TIMEOUT) -> str:
        op = operation.strip().lower()

        if op == "detect":
            return self._detect_hooks()

        if op == "run":
            if not script:
                return "Error: 'script' parameter is required for operation 'run'."
            return self._run_npm_script(script, timeout)

        if op in ("build", "test", "lint"):
            return self._run_hook(op, timeout)

        return f"Error: unknown operation '{operation}'. Available: detect, build, test, lint, run"

    # --- Detection ---

    def _detect_hooks(self) -> str:
        found = []
        for cwd, label in self._scan_roots():
            pj = os.path.join(cwd, "package.json")
            if os.path.exists(pj):
                scripts = self._read_json(pj).get("scripts", {})
                if scripts:
                    known = [s for s in ("build", "test", "lint", "check", "typecheck") if s in scripts]
                    other = [s for s in scripts if s not in known][:5]
                    parts = []
                    if known:
                        parts.append(", ".join(known))
                    if other:
                        parts.append("others: " + ", ".join(other))
                    found.append(f"{label} npm scripts ({'; '.join(parts)})")

            for cfg in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile"):
                if os.path.exists(os.path.join(cwd, cfg)):
                    found.append(f"{label} python ({cfg})")
                    break

            if os.path.exists(os.path.join(cwd, "Cargo.toml")):
                found.append(f"{label} cargo (build, test, clippy)")

            if os.path.exists(os.path.join(cwd, "go.mod")):
                found.append(f"{label} go (build, test, vet)")

        if not found:
            return "No build/test/lint hooks detected in the project."
        return "Detected hooks:\n" + "\n".join(f"- {f}" for f in found)

    def _scan_roots(self) -> list:
        """Return list of (cwd, label) tuples to scan for hooks."""
        roots = [(PROJECT_ROOT, ".")]
        for sub in ("frontend", "backend", "client", "server", "web", "app"):
            path = os.path.join(PROJECT_ROOT, sub)
            if os.path.isdir(path):
                roots.append((path, sub + "/"))
        return roots

    def _read_json(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _toolchains(self) -> list:
        """Return list of (toolchain, cwd) detected in priority order."""
        chains = []
        seen = set()
        for cwd, label in self._scan_roots():
            if os.path.exists(os.path.join(cwd, "package.json")):
                key = ("npm", cwd)
                if key not in seen:
                    chains.append(("npm", cwd))
                    seen.add(key)
            if any(os.path.exists(os.path.join(cwd, c)) for c in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")):
                key = ("python", cwd)
                if key not in seen:
                    chains.append(("python", cwd))
                    seen.add(key)
            if os.path.exists(os.path.join(cwd, "Cargo.toml")):
                key = ("cargo", cwd)
                if key not in seen:
                    chains.append(("cargo", cwd))
                    seen.add(key)
            if os.path.exists(os.path.join(cwd, "go.mod")):
                key = ("go", cwd)
                if key not in seen:
                    chains.append(("go", cwd))
                    seen.add(key)
        return chains

    # --- Command resolution ---

    def _run_hook(self, operation: str, timeout: int) -> str:
        chains = self._toolchains()
        if not chains:
            return "Error: no supported toolchain detected in the project."

        for toolchain, cwd in chains:
            command = self._resolve_command(toolchain, operation, cwd)
            if command is None:
                continue
            allowed, reason = is_bash_command_allowed(command)
            if not allowed:
                return f"Error: command blocked: {reason}"
            return self._exec(command, timeout, cwd)

        labels = [t for t, _ in chains]
        return f"Error: no {operation} hook found. Toolchains: {', '.join(labels)}. Run 'detect' for details."

    def _resolve_command(self, toolchain: str, operation: str, cwd: str):
        fn = {
            "npm": self._resolve_npm,
            "python": self._resolve_python,
            "cargo": self._resolve_cargo,
            "go": self._resolve_go,
        }.get(toolchain)
        if fn:
            return fn(operation, cwd)

    def _resolve_npm(self, operation: str, cwd: str):
        scripts = self._read_json(os.path.join(cwd, "package.json")).get("scripts", {})
        if operation == "build" and "build" in scripts:
            return "npm run build"
        if operation == "test" and "test" in scripts:
            return "npm test"
        if operation == "lint":
            for name in ("lint", "eslint", "check"):
                if name in scripts:
                    return f"npm run {name}"

    def _resolve_python(self, operation: str, cwd: str):
        if operation == "build":
            if importlib.util.find_spec("build") is not None:
                return "python -m build"
        if operation == "test":
            if importlib.util.find_spec("pytest") is not None:
                return "python -m pytest"
        if operation == "lint":
            for mod, args in (("ruff", "check ."), ("flake8", ""), ("mypy", ".")):
                if importlib.util.find_spec(mod) is not None:
                    return f"python -m {mod} {args}".strip()

    def _resolve_cargo(self, operation: str, cwd: str):
        if operation == "build":
            return "cargo build"
        if operation == "test":
            return "cargo test"
        if operation == "lint":
            return "cargo clippy"

    def _resolve_go(self, operation: str, cwd: str):
        if operation == "build":
            return "go build ./..."
        if operation == "test":
            return "go test ./..."
        if operation == "lint":
            return "go vet ./..."

    # --- NPM run (operation=run) ---

    def _run_npm_script(self, script_name: str, timeout: int) -> str:
        for cwd, label in self._scan_roots():
            scripts = self._read_json(os.path.join(cwd, "package.json")).get("scripts", {})
            if script_name in scripts:
                command = f"npm run {script_name}"
                allowed, reason = is_bash_command_allowed(command)
                if not allowed:
                    return f"Error: command blocked: {reason}"
                return self._exec(command, timeout, cwd)
        return f"Error: script '{script_name}' not found in any package.json in the project."

    # --- Execution ---

    def _exec(self, command: str, timeout: int, cwd: str = PROJECT_ROOT) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output[:MAX_OUTPUT] if output else f"Command '{command}' completed (no output)"
        except subprocess.TimeoutExpired:
            return f"Error: command '{command}' timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"