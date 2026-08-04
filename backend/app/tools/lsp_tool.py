import os
import ast
import traceback
from app.tools.base import BaseTool
from app.config import resolve_path, is_within_project, PROJECT_ROOT


class LSPTool(BaseTool):
    name = "agent_lsp"
    description = "Intelligent code analysis and safe refactoring. Operations: hover, goto, references, rename, complete, diagnose, outline"
    parameters = {
        "operation": {
            "type": "string",
            "description": "Operation: hover (type info), goto (go to definition), references (find references), rename (safe rename symbol), complete (code completions), diagnose (find errors), outline (file structure)"
        },
        "file_path": {
            "type": "string",
            "description": "Path to file (relative to project root)"
        },
        "line": {
            "type": "integer",
            "description": "Line number (1-based)",
            "default": 1
        },
        "column": {
            "type": "integer",
            "description": "Column offset (0-based)",
            "default": 0
        },
        "new_name": {
            "type": "string",
            "description": "New name for rename operation",
            "default": ""
        },
        "code": {
            "type": "string",
            "description": "Code snippet for analysis (if not reading from file)",
            "default": ""
        }
    }

    def execute(self, operation: str, file_path: str = "", line: int = 1, column: int = 0, new_name: str = "", code: str = "") -> str:
        try:
            resolved = None
            if file_path:
                resolved = resolve_path(file_path)
                if not is_within_project(resolved):
                    return f"Error: path outside project root: {file_path}"
                if not os.path.exists(resolved):
                    return f"Error: file not found: {file_path}"
                with open(resolved, "r", encoding="utf-8") as f:
                    code = f.read()

            if not code:
                return "Error: no code provided (specify file_path or code parameter)"

            lang = self._detect_language(resolved or file_path)

            if lang == "python":
                return self._analyze_python(operation, code, resolved, line, column, new_name)
            else:
                return self._analyze_ast(operation, code, resolved, lang, line, column)

        except Exception as e:
            return f"Error: {e}\n{traceback.format_exc()}"

    def _detect_language(self, file_path: str) -> str:
        if not file_path:
            return "python"
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python",
            ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript",
            ".java": "java", ".kt": "kotlin",
            ".cpp": "cpp", ".c": "c", ".h": "c", ".hpp": "cpp",
            ".go": "go", ".rs": "rust", ".rb": "ruby",
            ".php": "php", ".swift": "swift",
            ".cs": "csharp", ".scala": "scala",
        }
        return mapping.get(ext, "unknown")

    def _analyze_python(self, operation: str, code: str, file_path: str, line: int, column: int, new_name: str) -> str:
        import jedi

        script = jedi.Script(code=code, path=file_path)

        if operation == "hover":
            names = script.infer(line, column)
            if not names:
                return "No type information available at this position"
            parts = []
            for n in names:
                desc = n.description
                if n.docstring():
                    desc += f"\n  Docstring: {n.docstring()[:500]}"
                desc += f"\n  Type: {n.type}"
                if n.full_name:
                    desc += f"\n  Full name: {n.full_name}"
                if n.line is not None:
                    desc += f"\n  Defined at: line {n.line}, column {n.column}"
                parts.append(desc)
            return "\n---\n".join(parts)

        elif operation == "goto":
            defs = script.goto_definitions(line, column)
            if not defs:
                return "No definition found"
            parts = []
            for d in defs:
                desc = f"Name: {d.name}"
                if d.module_name:
                    desc += f"\n  Module: {d.module_name}"
                if d.line is not None:
                    desc += f"\n  Line: {d.line}, Column: {d.column}"
                desc += f"\n  Description: {d.description}"
                if d.docstring():
                    desc += f"\n  Docstring: {d.docstring()[:300]}"
                parts.append(desc)
            return "\n---\n".join(parts)

        elif operation == "references":
            refs = script.get_references(line, column)
            if not refs:
                return "No references found"
            parts = []
            for r in refs:
                loc = f"{r.module_name or 'unknown'}:{r.line}:{r.column}" if r.line is not None else "unknown"
                parts.append(f"  {loc} ({r.description})")
            return f"Found {len(refs)} references:\n" + "\n".join(parts)

        elif operation == "rename":
            if not new_name:
                return "Error: new_name parameter is required for rename"
            try:
                refactoring = script.rename(line, column, new_name)
                changes = refactoring.get_changed_files()
                result_parts = []
                total_changes = 0
                for fpath, change_list in changes.items():
                    rel = os.path.relpath(fpath, PROJECT_ROOT) if fpath else fpath
                    result_parts.append(f"File: {rel}")
                    for c in change_list:
                        result_parts.append(f"  Line {c.line}: {c.old_line} \u2192 {c.new_line}")
                        total_changes += 1
                if not result_parts:
                    return f"Rename to '{new_name}' would not change anything"
                return f"Rename to '{new_name}' ({total_changes} change(s)):\n" + "\n".join(result_parts)
            except Exception as e:
                return f"Refactoring error: {e}"

        elif operation == "complete":
            completions = script.complete(line, column)
            if not completions:
                return "No completions available"
            parts = []
            for c in completions[:30]:
                parts.append(f"  {c.name} ({c.type})")
            return f"Completions ({len(completions)}):\n" + "\n".join(parts)

        elif operation == "diagnose":
            issues = []
            try:
                compile(code, file_path or "<string>", "exec")
            except SyntaxError as e:
                issues.append(f"Syntax Error: {e.msg} at line {e.lineno}, column {e.offset}\n  {e.text}")

            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("."):
                        pass
            except Exception:
                pass

            if not issues:
                return "No syntax errors found"
            return "\n".join(issues)

        elif operation == "outline":
            try:
                tree = ast.parse(code)
                items = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        items.append(f"  function {node.name} (line {node.lineno})")
                    elif isinstance(node, ast.ClassDef):
                        items.append(f"  class {node.name} (line {node.lineno})")
                        for child in ast.iter_child_nodes(node):
                            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                items.append(f"    method {child.name} (line {child.lineno})")
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                items.append(f"  variable {target.id} (line {node.lineno})")
                return "Outline:\n" + "\n".join(items) if items else "No symbols found"
            except SyntaxError as e:
                return f"Cannot parse file: {e.msg} at line {e.lineno}"

        else:
            return f"Error: unknown operation '{operation}'. Available: hover, goto, references, rename, complete, diagnose, outline"

    def _analyze_ast(self, operation: str, code: str, file_path: str, lang: str, line: int, column: int) -> str:
        if operation == "diagnose":
            try:
                compile(code, file_path or "<string>", "exec")
                return "No syntax errors found"
            except SyntaxError as e:
                return f"Syntax Error: {e.msg} at line {e.lineno}"
            except Exception:
                return "Basic syntax check passed (language-specific diagnostics require a dedicated LSP server)"

        elif operation == "outline":
            try:
                tree = ast.parse(code)
                items = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        items.append(f"  function {node.name} (line {node.lineno})")
                    elif isinstance(node, ast.ClassDef):
                        items.append(f"  class {node.name} (line {node.lineno})")
                return "Outline:\n" + "\n".join(items) if items else "No symbols found (language may not be supported)"
            except SyntaxError:
                return "Outline requires a valid Python file for AST-based analysis"
            except Exception:
                return f"Outline not available for {lang} files"

        elif operation == "hover":
            return f"Code intelligence for {lang} requires a language-specific LSP server. Try using Python files for full support."

        elif operation == "goto":
            return f"Go-to-definition for {lang} requires a language-specific LSP server."

        elif operation == "references":
            return f"Find references for {lang} requires a language-specific LSP server."

        elif operation == "rename":
            return f"Safe rename for {lang} requires a language-specific LSP server."

        elif operation == "complete":
            return f"Code completions for {lang} require a language-specific LSP server."

        else:
            return f"Error: unknown operation '{operation}'. Available: diagnose, outline (basic); hover, goto, references, rename, complete (Python only)"