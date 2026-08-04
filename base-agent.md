# BASE AGENT - Specification

## Overview

Minimal viable AI agent with pluggable tool system. Designed as foundation for specialized agents (programmer, analyst, DevOps).

## Architecture

```
┌─────────────────────────────────────────┐
│              BASE AGENT                  │
├─────────────────────────────────────────┤
│  CORE (always active):                  │
│  1. Read        - read files            │
│  2. Edit        - edit files            │
│  3. Write       - create files          │
│  4. Bash        - execute commands      │
│  5. Grep        - search in file content│
│  6. Glob        - search files by name  │
├─────────────────────────────────────────┤
│  MEMORY:                                │
│  7. Short-term  - session history       │
│  8. Long-term   - RAG + summarization   │
│  9. Sessions    - switch/compare        │
├─────────────────────────────────────────┤
│  PLANNING:                              │
│  10. Tasks      - track progress        │
│  11. Planner    - decompose into steps  │
└─────────────────────────────────────────┘
```

## Directory Structure

```
AI-smolagents/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── core.py           # Agent loop
│   │   │   └── planner.py        # Step decomposition
│   │   ├── tools/
│   │   │   ├── __init__.py       # Tool registry
│   │   │   ├── base.py           # Base Tool class
│   │   │   ├── file_tool.py      # Read, Write, Edit
│   │   │   ├── shell_tool.py     # Bash execution
│   │   │   ├── search_tool.py    # Grep, Glob
│   │   │   ├── web_tool.py       # WebSearch, HTTP
│   │   │   ├── memory_tool.py    # RAG, Summarize
│   │   │   ├── code_tool.py      # CodeExec, Lint
│   │   │   ├── git_tool.py       # Git operations
│   │   │   ├── lsp_tool.py       # Code intelligence & refactoring
│   │   │   └── hooks_tool.py     # Build/test/lint hooks
│   │   ├── rag/
│   │   ├── memory/
│   │   └── main.py
│   └── data/
├── frontend/                      # Optional UI
└── base-agent.md                  # This file
```

## Tool Interface

Every tool extends BaseTool:

```python
class BaseTool:
    name: str           # Unique identifier
    description: str    # For LLM prompt (keep short)
    parameters: dict    # JSON Schema for arguments
    
    def execute(self, **kwargs) -> str:
        """Run the tool. Return result as string."""
        raise NotImplementedError
```

## Tool Levels

### Level 1 - Core (implement first)
| Tool | Description | Complexity |
|------|-------------|------------|
| read | Read file contents | Easy |
| edit | Edit file by string replacement | Easy |
| write | Create/overwrite file | Easy |
| bash | Execute shell command | Easy |
| grep | Search content by regex | Medium |
| glob | Find files by pattern | Easy |

### Level 2 - Memory
| Tool | Description | Complexity |
|------|-------------|------------|
| session_history | Get conversation history | Easy |
| session_search | Search past sessions via RAG | Medium |
| summarize | Create summary of session | Medium |

### Level 3 - Planning
| Tool | Description | Complexity |
|------|-------------|------------|
| task_create | Create tracked task | Easy |
| task_update | Update task status | Easy |
| planner | Decompose goal into steps | Hard |

### Level 4 - Extensions (optional)
| Tool | Description | Complexity |
|------|-------------|------------|
| web_search | Search internet | Medium |
| http_request | Call external API | Easy |
| code_exec | Execute Python code | Medium |
| git_operations | Commit, push, diff | Medium |
| lint | Check code quality | Easy |
| test_run | Run test suite | Easy |
| agent_lsp | Code intelligence: hover, goto, references, rename, complete, diagnose, outline | Medium |
| hooks_mcp | Run build/test/lint hooks: detect, build, test, lint, run | Medium |

## Implementation Plan

### Phase 1: Core Tools
1. Create `tools/base.py` - BaseTool class
2. Create `tools/file_tool.py` - Read, Write, Edit
3. Create `tools/shell_tool.py` - Bash
4. Create `tools/search_tool.py` - Grep, Glob
5. Create `tools/__init__.py` - Tool registry
6. Update `agent/core.py` - Use tools instead of direct calls

### Phase 2: Memory Integration
1. Connect tools to MemoryStore
2. Auto-index tool results in RAG
3. Add summarization trigger

### Phase 3: Planning
1. Add task tracking to tools
2. Implement planner (LLM-based decomposition)
3. Add step-by-step execution

### Phase 4: Extensions
1. Add web_search tool
2. Add code_exec tool
3. Add git tools
4. Add agent_lsp tool (code intelligence + safe refactoring)
5. Create specialized agent profiles

## Prompt Template

System prompt structure for tool-using agent:

```
You are an AI assistant with access to tools.

AVAILABLE TOOLS:
{tool_descriptions}

RULES:
1. Use tools when needed, don't guess
2. Verify results before reporting
3. Ask user if unsure
4. Track progress with tasks

CURRENT CONTEXT:
- Session: {session_id}
- Summary: {summary}
- Recent history: {history}
```

## Success Criteria

- [ ] All 6 core tools working
- [ ] Tools integrated with agent loop
- [ ] Memory persists across sessions
- [ ] RAG indexes tool results
- [ ] Planner decomposes complex tasks
- [ ] Easy to add new tools (plugin system)
