"""Docker Sandbox Execution Service.

Key fixes applied:
- execute_code_async(): async wrapper using asyncio.to_thread() to unblock event loop.
- Image existence pre-check: warns clearly if image is missing (avoids silent 5-min pulls).
- Subprocess fallback: when Docker is not running, code runs via local subprocess so the
  app works without Docker at all (users only need Python installed).
- All blocking calls (containers.run, container.wait) run in thread pool.
"""

import os
import shutil
import tempfile
import asyncio
import subprocess
from typing import Optional
from dataclasses import dataclass
from app.core.config import settings

try:
    import docker
    from docker.errors import DockerException, ImageNotFound
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


@dataclass
class ExecutionResult:
    """Encapsulates the raw output from a sandboxed container run."""
    stdout: str
    stderr: str
    exit_code: int
    error_trace: Optional[str] = None


class DockerSandbox:
    """Manages ephemeral container lifecycles for secure code execution."""

    def __init__(self):
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                print("[DockerSandbox] Docker daemon connected successfully.", flush=True)
            except Exception as e:
                self.client = None
                print(f"[DockerSandbox] Docker unavailable: {e}", flush=True)
        else:
            self.client = None

    async def execute_code_async(
        self,
        code: str,
        timeout_seconds: Optional[int] = None,
        image_name: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Async wrapper: runs Docker SDK (blocking I/O) in a thread pool.
        
        FIX: Without this, container.wait() blocks the FastAPI event loop for the
        entire execution duration, making the server appear frozen.
        """
        return await asyncio.to_thread(
            self.execute_code, code, timeout_seconds, image_name
        )

    def execute_code(
        self,
        code: str,
        timeout_seconds: Optional[int] = None,
        image_name: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Runs code in an isolated, ephemeral Docker container.

        Security Safeguards:
          - Read-only script mount (:ro)
          - 512MB RAM ceiling
          - 1 CPU core quota
          - network_mode="none" (no SSRF / exfiltration)
          - PID limit 100 (no fork bombs)
          - no-new-privileges security opt
          - Guaranteed cleanup via finally block
        """
        timeout = timeout_seconds or settings.EXECUTION_TIMEOUT_SECONDS
        image = image_name or settings.DOCKER_SANDBOX_IMAGE

        print(f"  [Docker] Preparing sandbox (image={image}, timeout={timeout}s)...", flush=True)

        if not self.client:
            print("  [Docker] Not connected — using subprocess fallback.", flush=True)
            return self._subprocess_execution_fallback(code, timeout)

        # FIX: Pre-check if the image exists locally.
        # If missing, containers.run() will silently pull it (takes minutes and freezes the request).
        try:
            self.client.images.get(image)
            print(f"  [Docker] Image '{image}' found locally.", flush=True)
        except ImageNotFound:
            return ExecutionResult(
                stdout="",
                stderr=(
                    f"Docker image '{image}' not found locally.\n"
                    f"Run this command to fix it:\n\n"
                    f"  docker pull {image}\n\n"
                    f"Or set DOCKER_SANDBOX_IMAGE in .env to an already-pulled image."
                ),
                exit_code=-2,
                error_trace=f"ImageNotFound: '{image}' not available locally. Pull it first.",
            )
        except DockerException as de:
            return ExecutionResult(
                stdout="", stderr=str(de), exit_code=-1, error_trace=str(de)
            )

        temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")
        script_path = os.path.join(temp_dir, "script.py")
        container = None

        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            volumes = {temp_dir: {"bind": "/sandbox", "mode": "ro"}}

            print(f"  [Docker] Launching container...", flush=True)
            container = self.client.containers.run(
                image=image,
                command=["python", "/sandbox/script.py"],
                volumes=volumes,
                working_dir="/sandbox",
                network_mode=settings.SANDBOX_NETWORK_MODE,
                mem_limit=settings.MAX_CONTAINER_MEMORY,
                cpu_quota=settings.CPU_QUOTA_MICROS,
                pids_limit=100,
                security_opt=["no-new-privileges:true"],
                detach=True,
                stdout=True,
                stderr=True,
            )

            print(f"  [Docker] Container {container.short_id} running...", flush=True)
            try:
                wait_result = container.wait(timeout=timeout)
                exit_code = wait_result.get("StatusCode", 1)
            except Exception as wait_err:
                try:
                    container.kill()
                except Exception:
                    pass
                return ExecutionResult(
                    stdout="",
                    stderr=f"Execution timed out after {timeout}s.",
                    exit_code=124,
                    error_trace=f"TimeoutError: exceeded {timeout}s limit.",
                )

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            status = "✓ SUCCESS" if exit_code == 0 else f"✗ FAILED (exit={exit_code})"
            print(f"  [Docker] Container finished — {status}", flush=True)

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                error_trace=stderr if exit_code != 0 else None,
            )

        except DockerException as de:
            return ExecutionResult(
                stdout="", stderr=f"Docker runtime error: {de}", exit_code=-1, error_trace=str(de)
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _subprocess_execution_fallback(self, code: str, timeout: int) -> ExecutionResult:
        """
        Runs user code as a local subprocess when Docker is unavailable.

        This lets the app work without Docker Desktop installed — anyone with
        Python can run the backend and get real code execution results.

        Security note: no container isolation here. Code runs as the current OS
        user. Only use in trusted / dev environments or when Docker is absent.
        """
        print("  [Subprocess] Executing code locally (no Docker)...", flush=True)

        # Write code to a temp file (avoids shell injection vs -c flag)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_path = f.name
        except Exception as e:
            return ExecutionResult(
                stdout="", stderr=f"Could not write temp file: {e}",
                exit_code=-1, error_trace=str(e),
            )

        try:
            proc = subprocess.run(
                ["python", tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            status = "SUCCESS" if proc.returncode == 0 else f"FAILED (exit={proc.returncode})"
            print(f"  [Subprocess] {status}", flush=True)
            return ExecutionResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                error_trace=proc.stderr if proc.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution timed out after {timeout}s.",
                exit_code=124,
                error_trace=f"TimeoutError: exceeded {timeout}s limit.",
            )
        except FileNotFoundError:
            # 'python' not on PATH — try 'python3'
            try:
                proc = subprocess.run(
                    ["python3", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return ExecutionResult(
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    exit_code=proc.returncode,
                    error_trace=proc.stderr if proc.returncode != 0 else None,
                )
            except Exception as e2:
                return ExecutionResult(
                    stdout="", stderr=f"Python interpreter not found: {e2}",
                    exit_code=-1, error_trace=str(e2),
                )
        except Exception as e:
            return ExecutionResult(
                stdout="", stderr=str(e), exit_code=-1, error_trace=str(e)
            )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _mock_execution_fallback(self, code: str) -> ExecutionResult:
        """Legacy mock — kept for backward compatibility in tests."""
        return ExecutionResult(
            stdout="[MOCK MODE — Docker not connected]\nCode received and accepted.",
            stderr="",
            exit_code=0,
            error_trace=None,
        )


docker_sandbox = DockerSandbox()
