import shutil
from pathlib import Path
import subprocess

# --- 1. Tool Implementations ---

def read_file(path: str) -> str:
    """Reads content from a specified file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
def copy_file(src: str, dst: str) -> str:
    """Copies a file from src to dst"""
    try:
        shutil.copyfile(src,dst)
        return f"Successfully copied {src} to {dst}"
    except Exception as e:
        return f"Error copying file: {e}"

def extract_code_block(source_file: str, dest_file: str, start_marker: str, end_marker: str) -> str:
    """Extracts lines between two markers in a source_file and writes them to a dest file"""
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        recording = False
        extracted = []
        for line in lines:
            if start_marker in line:
                recording = True
            if recording:
                extracted.append(line)
            if end_marker and end_marker in line and recording and line.strip() != start_marker:
                break
        with open(dest_file, "w", encoding="utf-8") as f:
            f.writelines(extracted)
        return f"Wrote {len(extracted)} lines to {dest_file}"
    except Exception as e:
        return f"Extraction error: {e}"
    
def write_file(path: str, content: str) -> str:
    """Writes content to a specified file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def create_folder(path: str, exist_ok: bool = True) -> str:
    """Creates a directory at the specified path
    Args:
        path: The directory path to create.
        exist_ok: If True, do not raise an error if directory already exists, Defaults to True
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=exist_ok)
        return f"Successfully created directory: {path}"
    except FileExistsError:
        return f"Error: Directory already exists at {path}"
    except Exception as e:
        return f"Error creating directory: {e}"

def run_shell(command: str) -> str:
    """Runs a shell command and returns stdout or stderr (truncated)."""
    try:
        res = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15
        )
        output = res.stdout if res.stdout else res.stderr
        # Truncate output to prevent saturating the context window
        lines = output.splitlines()
        if len(lines) > 25:
            output = "\n".join(lines[:10] + ["... [truncated] ..."] + lines[-10:])
        return output.strip() or "[Command executed with empty output]"
    except Exception as e:
        return f"Command execution error: {e}"

def delete_file(path: str) -> str:
    """Deletes a file at the specified path."""
    try:
        Path(path).unlink()
        return f"Successfully deleted {path}"
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except IsADirectoryError:
        return f"Error: Path is a directory, not a file: {path}"
    except Exception as e:
        return f"Error deleting file: {e}"


# Tool registry mapping tool names to actual callables
TOOL_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "run_shell": run_shell,
    "create_folder": create_folder,
    "copy_file": copy_file,
    "extract_code_block": extract_code_block
}

# Tool schemas provided to the LLM
TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Reads text content from a file path.",
        "parameters": {"path": "string"},
    },
    {
        "name": "write_file",
        "description": "Writes text content to a file path.",
        "parameters": {"path": "string", "content": "string"},
    },
    {
        "name": "delete_file",
        "description": "Deletes a file",
        "parameters": {"path": "string"},
    },
    {
        "name": "create_folder",
        "description": "Creates a folder of the path name",
        "parameters": {"path": "string", "exist_ok=True": "bool"},
    },
    {
        "name": "copy_file",
        "description": "Copies a file's content to the destination file",
        "parameters": {"src": "string", "dest": "string"},
    },
    {
        "name": "extract_code_block",
        "description": "Extracts lines between two markers in a source_file and writes them to a dest file",
        "parameters": {"source_file": "string", "dest_file": "string", "start_marker": "string", "end_marker": "string or empty until EOF"},
    },
    {
        "name": "run_shell",
        "description": "Executes a safe shell command and inspects stdout/stderr.",
        "parameters": {"command": "string"},
    },
]