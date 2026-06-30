# -*- coding: utf-8 -*-
"""
AegisOps Sandbox Environment Manager
====================================
API Grounding & Specifications:
* Compute Provisioning (ECS API): https://www.alibabacloud.com/help/en/ecs/developer-reference/
* Container Service (ACK API / Sandbox): https://www.alibabacloud.com/help/en/ack/developer-reference/
* SDK Code Generation Registry (OpenAPI Explorer): https://next.api.alibabacloud.com/home

This module manages the lifecycle of secure, resource-constrained container sandboxes 
to verify unit tests and patch remediations safely without affecting the host environment.
"""

import os
import sys
import uuid
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger("AegisOps.SandboxManager")

class SandboxManager:
    """Orchestrates isolated verification environments using local Docker containers."""

    def __init__(self) -> None:
        # Check if the Docker CLI is installed and running
        self.docker_available = False
        try:
            res = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                self.docker_available = True
        except Exception:
            pass

        self.active_sandboxes: Dict[str, Dict[str, Any]] = {}
        logger.info("SandboxManager initialized.")

    def _assert_docker_available(self) -> None:
        """Asserts that docker is available. Raises RuntimeError if not."""
        if not self.docker_available:
            raise RuntimeError(
                "Docker daemon is not running or accessible on the host machine. "
                "Ensure Docker Desktop is started and the CLI is available in PATH."
            )

    def provision_sandbox(self, target_dir_path: str) -> str:
        """
        Spins up an isolated sandbox container, copies targeted code, and aligns ownership permissions.

        Args:
            target_dir_path: Absolute path to the repository/code directory on the host.

        Returns:
            The container ID or name.
        """
        self._assert_docker_available()
        
        container_name = f"aegis-sb-{uuid.uuid4().hex[:8]}"
        logger.info(f"Provisioning sandbox container: {container_name}")

        try:
            # 1. Run container detached with network-isolation and resource caps
            run_cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "--network", "none",
                "-m", "512m",
                "--cpus", "0.5",
                "--user", "aegisrun",
                "--workdir", "/app",
                "aegisops-sandbox:latest",
                "tail", "-f", "/dev/null"
            ]
            res = subprocess.run(run_cmd, capture_output=True, text=True, check=True)
            container_id = res.stdout.strip()

            # 2. Copy targeted application code into the container's /app workspace
            logger.info(f"Copying code from {target_dir_path} to sandbox {container_name}")
            cp_cmd = ["docker", "cp", f"{target_dir_path}/.", f"{container_name}:/app/"]
            subprocess.run(cp_cmd, capture_output=True, text=True, check=True)

            # 3. Align permission boundaries: execute chown as root user inside container
            logger.info(f"Aligning workspace permissions inside sandbox {container_name}")
            chown_cmd = [
                "docker", "exec", "-u", "root",
                container_name, "chown", "-R", "aegisrun:aegisrun", "/app"
            ]
            subprocess.run(chown_cmd, capture_output=True, text=True, check=True)

            self.active_sandboxes[container_name] = {
                "container_id": container_id,
                "container_name": container_name,
                "target_dir": target_dir_path,
                "status": "PROVISIONED"
            }
            return container_name

        except subprocess.CalledProcessError as cpe:
            logger.error(f"Failed to provision sandbox: {cpe.stderr}")
            # Ensure cleanup on failure
            try:
                subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
            except Exception:
                pass
            raise RuntimeError(f"Sandbox provisioning failed: {cpe.stderr}") from cpe
        except Exception as e:
            logger.error(f"Unexpected failure during sandbox provisioning: {str(e)}")
            raise RuntimeError(f"Sandbox provisioning failed: {str(e)}") from e

    def execute_test_suite(self, container_id: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Executes pytest inside the sandbox container with strict timeout limits.

        Args:
            container_id: The identifier of the sandbox container.
            timeout_seconds: Hard execution timeout.

        Returns:
            Dict containing exit_code, stdout, stderr, and execution status.
        """
        self._assert_docker_available()
        logger.info(f"Running test suite in sandbox: {container_id}")

        exec_cmd = ["docker", "exec", container_id, "pytest"]

        try:
            res = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "status": "COMPLETED"
            }
        except subprocess.TimeoutExpired as te:
            logger.warning(f"Test suite execution timed out in sandbox {container_id} after {timeout_seconds}s.")
            return {
                "exit_code": -1,
                "stdout": te.stdout if te.stdout else "",
                "stderr": te.stderr if te.stderr else "TimeoutExpired: Test run exceeded execution limits.",
                "status": "TIMEOUT"
            }
        except subprocess.CalledProcessError as cpe:
            logger.error(f"Error running pytest in sandbox: {cpe.stderr}")
            return {
                "exit_code": cpe.returncode,
                "stdout": cpe.stdout,
                "stderr": cpe.stderr,
                "status": "FAILED"
            }
        except Exception as e:
            logger.error(f"Unexpected failure during test suite execution: {str(e)}")
            raise RuntimeError(f"Test execution failed: {str(e)}") from e

    def destroy_sandbox(self, container_id: str) -> None:
        """
        Stops and forcefully removes the sandbox container.

        Args:
            container_id: The identifier of the sandbox container.
        """
        self._assert_docker_available()
        logger.info(f"Destroying sandbox container: {container_id}")

        try:
            # Force stop and remove container
            subprocess.run(["docker", "stop", container_id], capture_output=True, text=True)
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, text=True)
            
            if container_id in self.active_sandboxes:
                del self.active_sandboxes[container_id]
                
            logger.info(f"Sandbox container {container_id} destroyed successfully.")
        except Exception as e:
            logger.error(f"Error destroying sandbox container {container_id}: {str(e)}")
            # Do not raise to ensure tear_down is resilient in loops, but log it

if __name__ == "__main__":
    # Local diagnostic verification run
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    manager = SandboxManager()
    print(f"Diagnostics: Docker available = {manager.docker_available}")
