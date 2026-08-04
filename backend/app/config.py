import os
import re

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)


def resolve_path(path: str) -> str:
    """Resolve path relative to project root unless absolute."""
    if not path:
        return PROJECT_ROOT
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(PROJECT_ROOT, path))


def is_within_project(path: str) -> bool:
    resolved = os.path.normpath(resolve_path(path))
    root = os.path.normpath(PROJECT_ROOT)
    try:
        return os.path.commonpath([resolved, root]) == root
    except ValueError:
        return False


BASH_BLOCKED_PATTERNS = [
    # Git destructive operations
    r"\bgit\s+push\b",
    r"\bgit\s+commit\b",
    r"\bgit\s+clone\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[fd]",
    # File deletion (Linux/Mac)
    r"\brm\s+(-[a-z]+\s+)*-?[rf]\b",
    r"\brm\s+.*-r",
    r"\brm\s+.*-f",
    r"\brmdir\b",
    # File deletion (Windows)
    r"\bdel\s+/[fq]",
    r"\brmdir\s+/s\b",
    r"\berase\b",
    # System operations
    r"\bformat\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    # Dangerous redirects and pipes
    r">\s*/dev/",
    r"\|\s*sh\b",
    r"\|\s*bash\b",
    # Chained destructive commands
    r";\s*rm\s+",
    r"&&\s*rm\s+",
    r";\s*del\s+",
    r"&&\s*del\s+",
    # PowerShell-specific dangers
    r"\bRemove-Item\b",
    r"\bStop-Computer\b",
    r"\bRestart-Computer\b",
    # Registry and system modifications
    r"\breg\s+delete\b",
    r"\bregedit\b",
    # Process killing
    r"\btaskkill\s+/f\b",
    r"\bkill\s+-9\b",
]


def is_bash_command_allowed(command: str) -> tuple[bool, str]:
    normalized = command.strip().lower()
    if not normalized:
        return False, "Empty command"
    for pattern in BASH_BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, f"Blocked command pattern: {pattern}"
    return True, ""
