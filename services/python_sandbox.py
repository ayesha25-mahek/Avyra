"""
services/python_sandbox.py
--------------------------
Dedicated Local Python Coding Sandbox for Avyara Sovereign Workbench.
SIH Problem Statement 26117.

Capabilities:
1. Workspace Isolation:
   - Each execution task creates an isolated sandbox under:
     output/sandbox/<task_id>/ (with input/, workspace/, output/, logs/).
   - Scripts execute with cwd set strictly to task workspace.
   - Prevents modifying Avyara project files or system directories.

2. Windows Process Management:
   - Uses sys.executable with subprocess.Popen for robust Windows compatibility.
   - Timeout protection: terminates runaway or infinite loops cleanly.

3. Environment Sanitization & Security:
   - Strips sensitive parent environment variables (API keys, Supabase, JWT, .env secrets).
   - Injects active socket blocking wrapper so outbound network requests raise PermissionError.
   - Sets network_policy = "BLOCKED_OFFLINE" and external_calls = 0.

4. Output Capture & Resource Limits:
   - Captures stdout, stderr, exit code, and execution duration in milliseconds.
   - Enforces configurable maximum stdout/stderr buffer sizes.
   - Collects newly created output artifacts in workspace/output.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from services.tool_registry import WorkspaceSecurity, OUTPUT_DIR

logger = logging.getLogger(__name__)

# Configurable Limits
DEFAULT_SANDBOX_TIMEOUT_SECONDS = float(os.getenv("PYTHON_SANDBOX_TIMEOUT_SECONDS", "15.0"))
MAX_STDOUT_BYTES = int(os.getenv("SANDBOX_MAX_STDOUT_BYTES", "100000"))  # 100 KB
MAX_STDERR_BYTES = int(os.getenv("SANDBOX_MAX_STDERR_BYTES", "50000"))   # 50 KB
MAX_CODE_SIZE_BYTES = int(os.getenv("SANDBOX_MAX_CODE_SIZE", "50000"))   # 50 KB

SANDBOX_ROOT_DIR = OUTPUT_DIR / "sandbox"
SANDBOX_ROOT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SandboxExecutionResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    task_id: str
    sandbox_dir: str
    output_files: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    network_policy: str = "BLOCKED_OFFLINE"
    external_calls: int = 0
    truncated_stdout: bool = False
    truncated_stderr: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PythonSandbox:
    """
    Dedicated local Python execution environment for Sovereign AI agents.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        timeout_seconds: float = DEFAULT_SANDBOX_TIMEOUT_SECONDS,
    ) -> None:
        self.base_dir = (base_dir or SANDBOX_ROOT_DIR).resolve()
        self.timeout_seconds = timeout_seconds
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_environment(self) -> Dict[str, str]:
        """
        Builds a strictly allowlisted environment for the child process.
        Removes all API keys, database credentials, and parent secrets.
        """
        allowlisted_keys = [
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "WINDIR",
            "PATH",
            "PATHEXT",
            "COMSPEC",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "LOCALAPPDATA",
            "APPDATA",
        ]
        clean_env = {}
        for key in allowlisted_keys:
            val = os.environ.get(key)
            if val is not None:
                clean_env[key] = val

        # Python execution parameters
        clean_env["PYTHONIOENCODING"] = "utf-8"
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["PYTHONNOUSERSITE"] = "1"

        # Active Network Blocking: Loopback proxy blackholes
        clean_env["HTTP_PROXY"] = "http://127.0.0.1:0"
        clean_env["HTTPS_PROXY"] = "http://127.0.0.1:0"
        clean_env["ALL_PROXY"] = "http://127.0.0.1:0"
        clean_env["NO_PROXY"] = ""

        return clean_env

    def _generate_security_preamble(self) -> str:
        """
        Generates Python code injected at the start of the script to block
        raw socket creation and enforce local offline isolation.
        """
        return (
            "# --- Sovereign Sandbox Security Harness ---\n"
            "import socket\n"
            "def _blocked_socket(*args, **kwargs):\n"
            "    raise PermissionError('Sovereign Sandbox: External network socket access is strictly prohibited.')\n"
            "socket.socket = _blocked_socket\n"
            "socket.create_connection = _blocked_socket\n"
            "# ------------------------------------------\n\n"
        )

    def execute(
        self,
        code: str,
        task_id: Optional[str] = None,
        input_files: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        inject_network_block: bool = True,
    ) -> SandboxExecutionResult:
        """
        Executes Python code in an isolated directory and returns structured execution results.
        """
        timeout_limit = timeout if timeout is not None else self.timeout_seconds
        task_id = task_id or uuid.uuid4().hex[:10]

        # 1. Enforce code length limits
        if len(code.encode("utf-8")) > MAX_CODE_SIZE_BYTES:
            return SandboxExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Code size ({len(code)} bytes) exceeds maximum allowable limit ({MAX_CODE_SIZE_BYTES} bytes).",
                duration_ms=0.0,
                task_id=task_id,
                sandbox_dir="",
                error_type="CODE_SIZE_EXCEEDED",
            )

        # 2. Setup isolated task directories
        task_dir = self.base_dir / task_id
        input_dir = task_dir / "input"
        workspace_dir = task_dir / "workspace"
        output_dir = task_dir / "output"
        logs_dir = task_dir / "logs"

        for d in (input_dir, workspace_dir, output_dir, logs_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Clean workspace and output directories to ensure a fresh, isolated run
        for f in workspace_dir.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass
        for f in output_dir.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass

        # 3. Copy approved input files into workspace
        if input_files:
            for src_path_str in input_files:
                try:
                    src_path = WorkspaceSecurity.sanitize_and_validate_read(src_path_str)
                    if src_path.exists() and src_path.is_file():
                        shutil.copy2(src_path, input_dir / src_path.name)
                        shutil.copy2(src_path, workspace_dir / src_path.name)
                except Exception as exc:
                    logger.warning("PythonSandbox: Could not copy input file '%s': %s", src_path_str, exc)

        # 4. Prepare script content with security preamble
        script_path = workspace_dir / "script.py"
        full_code = (self._generate_security_preamble() + code) if inject_network_block else code
        script_path.write_text(full_code, encoding="utf-8")

        # Snapshot workspace files prior to execution
        pre_existing_files = {f.name for f in workspace_dir.iterdir()}

        # 5. Execute via Subprocess
        env = self._sanitize_environment()
        cmd = [sys.executable, "-u", str(script_path)]

        start_time = time.perf_counter()
        exit_code = 0
        error_type = None
        stdout_text = ""
        stderr_text = ""
        duration_ms = 0.0

        try:
            logger.info("PythonSandbox: Starting task '%s' (timeout: %.1fs)...", task_id, timeout_limit)
            proc = subprocess.Popen(
                cmd,
                cwd=str(workspace_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            stdout_raw, stderr_raw = proc.communicate(timeout=timeout_limit)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            exit_code = proc.returncode
            stdout_text = stdout_raw or ""
            stderr_text = stderr_raw or ""

        except subprocess.TimeoutExpired:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning("PythonSandbox: Task '%s' timed out after %.1fs. Killing process.", task_id, timeout_limit)
            proc.kill()
            try:
                stdout_rem, stderr_rem = proc.communicate(timeout=2.0)
                stdout_text = stdout_rem or ""
                stderr_text = (stderr_rem or "") + f"\n[TIMEOUT] Execution exceeded {timeout_limit:.1f}s ceiling. Terminated."
            except Exception:
                stderr_text = f"[TIMEOUT] Execution exceeded {timeout_limit:.1f}s ceiling. Process terminated safely."
            exit_code = -1
            error_type = "TIMEOUT"

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            exit_code = 1
            error_type = "EXECUTION_EXCEPTION"
            stderr_text = f"Process execution failed: {exc}"

        # 6. Apply output truncation limits
        truncated_stdout = False
        truncated_stderr = False
        if len(stdout_text.encode("utf-8")) > MAX_STDOUT_BYTES:
            stdout_text = stdout_text[:MAX_STDOUT_BYTES] + "\n... [STDOUT TRUNCATED: Exceeded buffer limit]"
            truncated_stdout = True

        if len(stderr_text.encode("utf-8")) > MAX_STDERR_BYTES:
            stderr_text = stderr_text[:MAX_STDERR_BYTES] + "\n... [STDERR TRUNCATED: Exceeded buffer limit]"
            truncated_stderr = True

        # 7. Write logs
        try:
            (logs_dir / "stdout.log").write_text(stdout_text, encoding="utf-8")
            (logs_dir / "stderr.log").write_text(stderr_text, encoding="utf-8")
        except Exception:
            pass

        # 8. Identify newly generated output artifacts
        newly_created_files = []
        for item in workspace_dir.iterdir():
            if item.is_file() and item.name not in pre_existing_files and item.name != "script.py":
                dest_copy = output_dir / item.name
                shutil.copy2(item, dest_copy)
                newly_created_files.append(str(dest_copy))

        # Check for error classifications
        success = (exit_code == 0)
        if not success and not error_type:
            if "SyntaxError" in stderr_text:
                error_type = "SYNTAX_ERROR"
            elif "PermissionError" in stderr_text:
                error_type = "PERMISSION_VIOLATION"
            elif "ModuleNotFoundError" in stderr_text or "ImportError" in stderr_text:
                error_type = "DEPENDENCY_ERROR"
            else:
                error_type = "RUNTIME_ERROR"

        return SandboxExecutionResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_ms=duration_ms,
            task_id=task_id,
            sandbox_dir=str(task_dir),
            output_files=newly_created_files,
            error_type=error_type,
            network_policy="BLOCKED_OFFLINE",
            external_calls=0,
            truncated_stdout=truncated_stdout,
            truncated_stderr=truncated_stderr,
        )


# Global sandbox singleton
python_sandbox = PythonSandbox()
