import os
import re
import glob as glob_module
from app.tools.base import BaseTool
from app.config import resolve_path, is_within_project, PROJECT_ROOT


class GrepTool(BaseTool):
    name = "grep"
    description = "Search file contents by regex in the project"
    parameters = {
        "pattern": {"type": "string", "description": "Regex pattern"},
        "path": {"type": "string", "description": "Directory to search (relative to project root)", "default": "."},
        "include": {"type": "string", "description": "File pattern (e.g. *.py)", "default": "*"},
    }

    def execute(self, pattern: str, path: str = ".", include: str = "*") -> str:
        try:
            search_root = resolve_path(path)
            if not is_within_project(search_root):
                return f"Error: path outside project root: {path}"
            matches = []
            for root, dirs, files in os.walk(search_root):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "dist"}]
                for fname in files:
                    if not glob_module.fnmatch.fnmatch(fname, include):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if re.search(pattern, line):
                                    rel = os.path.relpath(fpath, PROJECT_ROOT)
                                    matches.append(f"{rel}:{i}: {line.rstrip()[:200]}")
                    except Exception:
                        pass
                    if len(matches) >= 50:
                        break
                if len(matches) >= 50:
                    break
            return "\n".join(matches) if matches else "No matches found"
        except Exception as e:
            return f"Error: {e}"


class GlobTool(BaseTool):
    name = "glob"
    description = "Find files by pattern in the project"
    parameters = {
        "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
        "path": {"type": "string", "description": "Base directory (relative to project root)", "default": "."},
    }

    def execute(self, pattern: str, path: str = ".") -> str:
        try:
            base = resolve_path(path)
            if not is_within_project(base):
                return f"Error: path outside project root: {path}"
            matches = glob_module.glob(os.path.join(base, pattern), recursive=True)
            rel_matches = [os.path.relpath(m, PROJECT_ROOT) for m in matches[:100]]
            return "\n".join(rel_matches) if rel_matches else "No files found"
        except Exception as e:
            return f"Error: {e}"
