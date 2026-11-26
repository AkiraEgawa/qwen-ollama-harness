from pathlib import Path
import json
import warnings
from datetime import datetime, timezone
from typing import Any

MEMORY_FILE = Path("data/MEMORY.md")
SESSIONS_DIR = Path("sessions")

def load_memory(max_lines: int = 50) -> str:
    if not MEMORY_FILE.exists():
        return ""
    lines = MEMORY_FILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:max_lines]).strip()

def build_system_prompt(tool_schemas: list[dict], memory_text: str = "") -> str:
    template = Path("AGENT.md").read_text(encoding="utf-8")
    memory_block = memory_text.strip() if memory_text.strip() else "No persistent notes recorded yet."
    return (
        template
        .replace("{{TOOL_SCHEMAS}}", json.dumps(tool_schemas, indent=2))
        .replace("{{MEMORY}}", memory_block)
    )

def append_action(step: dict[str, Any] | str, result: Any, session_id: int | str) -> bool:
    """
    Appends a single step/result pair to sessions/{session_id}.jsonl.
    Creates the sessions/ directory and .jsonl file automatically if missing.
    """
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_file = SESSIONS_DIR / f"{session_id}.jsonl"

        # Parse step if a raw JSON string was passed in instead of a dict
        parsed_step = json.loads(step) if isinstance(step, str) else step

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": parsed_step,
            "result": result,
        }

        with session_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return True

    except Exception as e:
        warnings.warn(
            f"[memory.py] Failed to append action to sessions/{session_id}.jsonl: {e}",
            RuntimeWarning,
            stacklevel=2,
        )
        return False