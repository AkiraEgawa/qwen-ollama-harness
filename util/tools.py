import shutil
from pathlib import Path
import subprocess
import shlex
import os
import re

ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "grep", "find", "wc",
    "mkdir", "cp", "mv", "touch", "echo", "pwd",
    "python", "python3", "pytest", "git",
}

def _resolve_safe_path(root: Path, user_path: str) -> Path:
    """Resolves a path inside root and blocks traversal, home expansion, and drive escapes."""
    if not user_path or not isinstance(user_path, str):
        raise ValueError("Path must be a non-empty string.")

    # Block home shortcuts (~), env vars ($HOME, %USERPROFILE%), and explicit Windows drive letters (C:\)
    if (
        user_path.startswith("~")
        or "$" in user_path
        or "%" in user_path
        or re.match(r"^[a-zA-Z]:", user_path)
    ):
        raise PermissionError(f"Access denied: '{user_path}' uses disallowed path expansion or drive letters.")

    # Strip accidental leading slashes so "/src/utils" stays inside root
    clean_rel = user_path.lstrip("/\\") or "."
    target = (root / clean_rel).resolve()

    if not target.is_relative_to(root):
        raise PermissionError(f"Access denied: '{user_path}' escapes workspace root.")

    return target

# --- 1. Tool Implementations ---

def create_workspace_tools(root_dir: str) -> dict:
    """
    Sandboxes agent tools so that it can't access anything beyond root directory, ever
    """
    root = Path(root_dir).resolve()
    if not root.is_dir():
        raise ValueError(f"Workspace root does not exist: {root}")
    
    def read_file(path: str) -> str:
        """Reads content from a specified file."""
        target = _resolve_safe_path(root, path)
        if not target.is_file():
            return f"Error: '{path}' does not exist."
        return target.read_text(encoding="utf-8", errors="replace")
    
    def copy_file(src: str, dst: str) -> str:
        """Copies a file from src to dst"""
        try:
            target = _resolve_safe_path(root, src)
            destination = _resolve_safe_path(root, dst)
            if not target.exists():
                return f"Error copying file: Source '{src}' does not exist."
            if target.is_dir():
                return f"Error copying file: Source '{src}' is a directory, not a file."
            if destination.is_dir():
                destination = destination / target.name
            destination.parent.mkdir(parents=True, exist_ok=True) # Just in case

            shutil.copyfile(target, destination)

            return f"Successfully copied {src} to {dst}"
        except Exception as e:
            return f"Error copying file: {e}"
        
    def extract_code_block(source_file: str, dest_file: str, start_marker: str, end_marker: str, include_markers: bool = True) -> str:
        """Extracts lines between two markers in a source_file and writes them to a dest file"""
        try:
            if not start_marker:
                return "Extraction error: start_marker cannot be empty."
            target = _resolve_safe_path(root, source_file)
            destination = _resolve_safe_path(root, dest_file)

            if not target.exists():
                return f"Extraction error: Source '{source_file}' does not exist."
            if target.is_dir():
                return f"Extraction error: Source '{source_file}' is a directory, not a file."
            if destination.is_dir():
                return f"Extraction error: Destination '{dest_file}' is a directory, not a file."

            lines = target.read_text(encoding="utf-8").splitlines(keepends=True)

            recording = False
            found_end = False
            extracted = list[str] = []

            for line in lines:
                if not recording:
                    # Find the start marker
                    if start_marker in line:
                        recording = True
                        if include_markers:
                            extracted.append(line)
                    # it doesn't have marker
                    continue
                if end_marker and end_marker in line:
                    if include_markers:
                        extracted.append(line)
                    found_end = True
                    break

                extracted.append(line)
            
            if not recording:
                # You somehow reached the end without finding a start
                return f"Extraction error: Start marker '{start_marker}' not found in '{source_file}'."
            if end_marker and not found_end:
                return f"Extraction error: End marker '{end_marker}' not found in '{source_file}'."

            # Make sure destination exists
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text("".join(extracted), encoding="utf-8")

            return f"Successfully wrote {len(extracted)} lines to {dest_file}."
        except UnicodeDecodeError:
            return f"Extraction error: '{source_file}' is not a valid UTF-8 text file."
        except Exception as e:
            return f"Extraction error: {e}"
        
    def write_file(path: str, content: str) -> str:
        """Writes content to a specified file."""
        try:
            target = _resolve_safe_path(root, path)
            if target.is_dir():
                return f"Error writing to file: Path '{path}' is a directory, not a file."

            target.parent.mkdir(parents=True, exist_ok=True)

            target.write_text(content, encoding="utf-8")

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
            target = _resolve_safe_path(root, path)
            if target.is_file():
                return f"Error: A file already exists at '{path}'"
            target.mkdir(parents=True, exist_ok=exist_ok)
            return f"Successfully created directory: {path}"
        except FileExistsError:
            return f"Error: Directory already exists at {path}"
        except Exception as e:
            return f"Error creating directory: {e}"

    def run_shell(command: str) -> str:
        """Runs an allowlisted command inside the sandboxed root directory."""
        try:
            # Parse arguments
            args = shlex.split(command)
            if not args:
                return "Error: Empty command."

            # Make sure it's allowed
            executable = Path(args[0]).name
            if executable not in ALLOWED_COMMANDS:
                return f"Error: Command '{executable}' is not allowed."

            # No leaking my API Keys, thank you very much
            safe_env = {
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": str(root),
                "LANG": "C.UTF-8",
                "PYTHONDONTWRITEBYTECODE": "1",
            }

            # working directory is forever root
            res = subprocess.run(
                args,
                shell=False,
                cwd=root,
                env=safe_env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=15,
            )

            # Combine stdout and stderr so errors are never hidden behind partial stdout
            parts = []
            if res.stdout:
                parts.append(res.stdout.strip())
            if res.stderr:
                parts.append(f"[stderr]\n{res.stderr.strip()}")
            output = "\n".join(parts)

            # 6. Truncate by both line count and total characters
            lines = output.splitlines()
            if len(lines) > 25:
                output = "\n".join(lines[:10] + ["... [truncated] ..."] + lines[-10:])
            if len(output) > 4000:
                output = output[:2000] + "\n... [truncated] ...\n" + output[-2000:]

            status = f"[exit code: {res.returncode}]"
            return f"{status}\n{output}" if output else f"{status} [Empty output]"

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 15 seconds."
        except ValueError as e:
            return f"Error parsing command: {e}"
        except Exception as e:
            return f"Command execution error: {e}"
        
    def delete_file(path: str) -> str:
        """Deletes a file at the specified path."""
        try:
            target = _resolve_safe_path(root, path)
            if target == root.resolve():
                return "Error deleting file: cannot delete root directory."
            if not target.exists() and not target.is_symlink():
                return f"Error deleting file: path '{path}' does not exist."
            if target.is_dir():
                return f"Error deleting file: path '{path}' is a directory, not a file."
            target.unlink()
            return f"Successfully deleted {path}"
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

    return TOOL_REGISTRY

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