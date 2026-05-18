from app.tools.file_tools import (
    write_file,
    read_file,
    list_directory,
    create_directory,
    delete_file,
)
from app.tools.terminal_tools import run_command

TOOL_REGISTRY = {
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "create_directory": create_directory,
    "delete_file": delete_file,
    "run_command": run_command,
}


async def execute_tool(tool_name: str, args: dict) -> dict:
    """Dispatch a tool call by name with args dict."""
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    return await fn(**args)
