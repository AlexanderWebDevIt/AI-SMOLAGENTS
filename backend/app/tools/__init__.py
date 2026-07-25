from app.tools.file_tool import ReadTool, WriteTool, EditTool
from app.tools.shell_tool import BashTool
from app.tools.search_tool import GrepTool, GlobTool


ALL_TOOLS = [
    ReadTool(),
    WriteTool(),
    EditTool(),
    BashTool(),
    GrepTool(),
    GlobTool(),
]


def get_tools():
    return ALL_TOOLS


def get_tool(name: str):
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None


def tools_to_prompt():
    return "\n".join([t.to_prompt() for t in ALL_TOOLS])
