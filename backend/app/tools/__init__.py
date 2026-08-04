from app.tools.file_tool import ReadTool, WriteTool, EditTool
from app.tools.shell_tool import BashTool
from app.tools.search_tool import GrepTool, GlobTool
from app.tools.git_tool import GitTool
from app.tools.lsp_tool import LSPTool
from app.tools.hooks_tool import HooksMCPTool
from app.tools.memory_tool import SessionHistoryTool, SessionSearchTool
from app.tools.code_tool import CodeExecTool
from app.tools.web_tool import HttpRequestTool


ALL_TOOLS = [
    ReadTool(),
    WriteTool(),
    EditTool(),
    BashTool(),
    GrepTool(),
    GlobTool(),
    GitTool(),
    LSPTool(),
    HooksMCPTool(),
    SessionHistoryTool(),
    SessionSearchTool(),
    CodeExecTool(),
    HttpRequestTool(),
]


def get_tools():
    return ALL_TOOLS


def get_tool(name: str):
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None


def tools_to_prompt():
    return chr(10).join([t.to_prompt() for t in ALL_TOOLS])