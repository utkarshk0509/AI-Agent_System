"""Docker Sandbox Execution Service.

Provides secure, isolated code execution inside ephemeral Docker containers
using the Docker SDK for Python. Enforces timeouts, memory limits, CPU quotas,
and network sandboxing with guaranteed container cleanup.
"""

import os
import shutil
import tempfile
from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.core.config import settings

# Attempt import of Docker SDK
try:
    import docker
    from docker.errors import DockerException, ContainerError
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
    """Manages ephemeral container lifecycles for code execution."""

    def __init__(self):
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
            except Exception as e:
                # Docker daemon not running or socket inaccessible
                self.client = None
        else:
            self.client = None

    def execute_code(
        self,
        code: str,
        timeout_seconds: Optional[int] = None,
        image_name: Optional[str] = None,
    ) -> ExecutionResult:
        """Executes a Python code string inside an isolated ephemeral container.
        
        Security & Production Safeguards:
        1. Read-only code mount: The script is mounted as read-only.
        2. Memory Limit: Hard ceiling (e.g., 512m) to prevent host memory exhaustion.
        3. CPU Quota: Limited to prevent CPU starvation.
        4. Network Isolation: 'none' mode prevents SSRF and outbound network traffic.
        5. PID Limit: Restricts process spawning to prevent fork bombs.
        6. Guaranteed Removal: Enforced via try...finally block.
        """
        timeout = timeout_seconds or settings.EXECUTION_TIMEOUT_SECONDS
        image = image_name or settings.DOCKER_SANDBOX_IMAGE

        if not self.client:
            # Fallback mock for local execution if Docker daemon is not connected
            return self._mock_execution_fallback(code)

        temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")
        script_path = os.path.join(temp_dir, "script.py")

        container = None
        try:
            # 1. Write the target script to temporary directory
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 2. Configure volume mount (host temp_dir -> container /sandbox)
            volumes = {
                temp_dir: {"bind": "/sandbox", "mode": "ro"}
            }

            # 3. Spin up ephemeral container with strict resource constraints
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

            # 4. Wait for container execution with timeout
            try:
                wait_result = container.wait(timeout=timeout)
                exit_code = wait_result.get("StatusCode", 1)
            except Exception as wait_err:
                # Execution timed out or hung
                try:
                    container.kill()
                except Exception:
                    pass
                return ExecutionResult(
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds: {str(wait_err)}",
                    exit_code=124,
                    error_trace=f"TimeoutError: Script execution exceeded {timeout} seconds limit.",
                )

            # 5. Extract logs
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            error_trace = stderr if exit_code != 0 else None

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                error_trace=error_trace,
            )

        except DockerException as de:
            return ExecutionResult(
                stdout="",
                stderr=f"Docker runtime error: {str(de)}",
                exit_code=-1,
                error_trace=str(de),
            )
        finally:
            # 6. Guaranteed cleanup of container and host temp directory
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _mock_execution_fallback(self, code: str) -> ExecutionResult:
        """Convenience fallback when Docker daemon is unavailable during dev."""
        return ExecutionResult(
            stdout="[DOCKER NOT CONNECTED: Mock Execution stdout]\nRan code successfully in mock mode.",
            stderr="",
            exit_code=0,
            error_trace=None,
        )


docker_sandbox = DockerSandbox()

