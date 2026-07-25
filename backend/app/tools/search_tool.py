import os
import re
import glob as glob_module
from app.tools.base import BaseTool


class GrepTool(BaseTool):
    name = "grep"
    description = "Search file contents by regex"
    parameters = {
        "pattern": {"type": "string", "description": "Regex pattern"},
        "path": {"type": "string", "description": "Directory to search", "default": "."},
        "include": {"type": "string", "description": "File pattern (e.g. *.py)", "default": "*"},
    }

    def execute(self, pattern: str, path: str = ".", include: str = "*") -> str:
        try:
            matches = []
            for root, dirs, files in os.walk(path):
                for fname in files:
                    if not glob_module.fnmatch.fnmatch(fname, include):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if re.search(pattern, line):
                                    matches.append(f"{fpath}:{i}: {line.rstrip()[:200]}")
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
    description = "Find files by pattern"
    parameters = {
        "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
        "path": {"type": "string", "description": "Base directory", "default": "."},
    }

    def execute(self, pattern: str, path: str = ".") -> str:
        try:
            matches = glob_module.glob(os.path.join(path, pattern), recursive=True)
            return "\n".join(matches[:100]) if matches else "No files found"
        except Exception as e:
            return f"Error: {e}"
