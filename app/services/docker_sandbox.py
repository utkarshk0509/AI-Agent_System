"""Runs generated Python code in a throwaway Docker container.

If Docker isn't running, the code runs as a normal local subprocess instead,
so the app still works with just Python installed (but without isolation).
"""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional

from docker.errors import DockerException, ImageNotFound

import docker
from app.core.config import settings


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    error_trace: Optional[str] = None


def timeout_result(timeout: int) -> ExecutionResult:
    return ExecutionResult(
        stdout="",
        stderr=f"Execution timed out after {timeout}s.",
        exit_code=124,
        error_trace=f"TimeoutError: exceeded {timeout}s limit.",
    )


class DockerSandbox:
    def __init__(self):
        try:
            self.client = docker.from_env()
            print("[DockerSandbox] Docker daemon connected successfully.", flush=True)
        except Exception as e:
            self.client = None
            print(f"[DockerSandbox] Docker unavailable: {e}", flush=True)

    async def execute_code_async(self, code: str, timeout_seconds: Optional[int] = None) -> ExecutionResult:
        # The Docker SDK calls block, so run them in a thread. Otherwise the whole
        # FastAPI server freezes while a container is running.
        return await asyncio.to_thread(self.execute_code, code, timeout_seconds)

    def execute_code(self, code: str, timeout_seconds: Optional[int] = None) -> ExecutionResult:
        """Run the code in a locked-down container.

        The container has no network, limited memory/CPU, at most 100 processes,
        a read-only mount for the script and no-new-privileges. It is always
        removed afterwards.
        """
        timeout = timeout_seconds or settings.EXECUTION_TIMEOUT_SECONDS
        image = settings.DOCKER_SANDBOX_IMAGE

        print(f"  [Docker] Preparing sandbox (image={image}, timeout={timeout}s)...", flush=True)

        if not self.client:
            print("  [Docker] Not connected — using subprocess fallback.", flush=True)
            return self.run_in_subprocess(code, timeout)

        # containers.run() would silently pull a missing image, which can take minutes
        # and leaves the request hanging. Fail fast with a clear message instead.
        try:
            self.client.images.get(image)
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
        except DockerException as e:
            return ExecutionResult(stdout="", stderr=str(e), exit_code=-1, error_trace=str(e))

        if settings.SANDBOX_SHARED_VOLUME:
            # Backend runs in a container: hand the script over through a named volume.
            os.makedirs(settings.SANDBOX_WORK_DIR, exist_ok=True)
            temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_", dir=settings.SANDBOX_WORK_DIR)
            os.chmod(temp_dir, 0o755)  # readable by a non-root sandbox user
            sandbox_dir = f"/sandbox/{os.path.basename(temp_dir)}"
            volumes = {settings.SANDBOX_SHARED_VOLUME: {"bind": "/sandbox", "mode": "ro"}}
        else:
            temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")
            sandbox_dir = "/sandbox"
            volumes = {temp_dir: {"bind": "/sandbox", "mode": "ro"}}

        container = None
        try:
            with open(os.path.join(temp_dir, "script.py"), "w", encoding="utf-8") as f:
                f.write(code)

            container = self.client.containers.run(
                image=image,
                command=["python", f"{sandbox_dir}/script.py"],
                volumes=volumes,
                working_dir=sandbox_dir,
                network_mode=settings.SANDBOX_NETWORK_MODE,
                mem_limit=settings.MAX_CONTAINER_MEMORY,
                cpu_quota=settings.CPU_QUOTA_MICROS,
                pids_limit=100,
                environment={"PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
                security_opt=["no-new-privileges:true"],
                detach=True,
                stdout=True,
                stderr=True,
            )
            print(f"  [Docker] Container {container.short_id} running...", flush=True)

            try:
                exit_code = container.wait(timeout=timeout).get("StatusCode", 1)
            except Exception:
                # wait() raises when the timeout is hit
                try:
                    container.kill()
                except Exception:
                    pass
                return timeout_result(timeout)

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
        except DockerException as e:
            return ExecutionResult(
                stdout="", stderr=f"Docker runtime error: {e}", exit_code=-1, error_trace=str(e)
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            shutil.rmtree(temp_dir, ignore_errors=True)

    def run_in_subprocess(self, code: str, timeout: int) -> ExecutionResult:
        """Fallback when Docker isn't available.

        There is no isolation here: the code runs as the current OS user.
        Only use it on your own machine.
        """
        print("  [Subprocess] Executing code locally (no Docker)...", flush=True)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            script_path = f.name

        # sys.executable instead of "python": on Windows a bare "python" can hit the
        # Microsoft Store stub. UTF-8 env vars stop non-ASCII prints from crashing on cp1252.
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
                cwd=tempfile.gettempdir(),
            )
        except subprocess.TimeoutExpired:
            return timeout_result(timeout)
        except Exception as e:
            return ExecutionResult(stdout="", stderr=str(e), exit_code=-1, error_trace=str(e))
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass

        status = "SUCCESS" if proc.returncode == 0 else f"FAILED (exit={proc.returncode})"
        print(f"  [Subprocess] {status}", flush=True)
        return ExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            error_trace=proc.stderr if proc.returncode != 0 else None,
        )


docker_sandbox = DockerSandbox()
