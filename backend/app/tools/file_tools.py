import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path("workspace")
WORKSPACE_ROOT.mkdir(exist_ok=True)


def _safe_path(relative_path: str) -> Path:
    """Resolve path and ensure it stays inside workspace/."""
    full = (WORKSPACE_ROOT / relative_path).resolve()
    if not str(full).startswith(str(WORKSPACE_ROOT.resolve())):
        raise PermissionError(f"Path escape detected: {relative_path}")
    return full


async def write_file(path: str, content: str) -> dict:
    start = datetime.utcnow()
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        ms = (datetime.utcnow() - start).microseconds // 1000
        return {
            "success": True,
            "tool": "write_file",
            "result": f"Written {len(content)} chars to {path}",
            "execution_time_ms": ms,
        }
    except Exception as e:
        return {"success": False, "tool": "write_file", "error": str(e)}


async def read_file(path: str) -> dict:
    try:
        content = _safe_path(path).read_text(encoding="utf-8")
        return {"success": True, "tool": "read_file", "result": content}
    except Exception as e:
        return {"success": False, "tool": "read_file", "error": str(e)}


async def list_directory(path: str = ".") -> dict:
    try:
        target = _safe_path(path)
        entries = [str(p.relative_to(WORKSPACE_ROOT)) for p in target.iterdir()]
        return {"success": True, "tool": "list_directory", "result": entries}
    except Exception as e:
        return {"success": False, "tool": "list_directory", "error": str(e)}


async def create_directory(path: str) -> dict:
    try:
        _safe_path(path).mkdir(parents=True, exist_ok=True)
        return {"success": True, "tool": "create_directory", "result": f"Created {path}"}
    except Exception as e:
        return {"success": False, "tool": "create_directory", "error": str(e)}


async def delete_file(path: str) -> dict:
    try:
        _safe_path(path).unlink()
        return {"success": True, "tool": "delete_file", "result": f"Deleted {path}"}
    except Exception as e:
        return {"success": False, "tool": "delete_file", "error": str(e)}
