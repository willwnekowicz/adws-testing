"""Process management for tracking and monitoring background processes."""

import os
import subprocess
import psutil
import time
import signal
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages and tracks processes spawned during test execution."""

    def __init__(self, run_id: str, artifacts_path: str = "./runs"):
        """Initialize ProcessManager.

        Args:
            run_id: Unique run identifier
            artifacts_path: Base path for storing artifacts
        """
        self.run_id = run_id
        self.artifacts_path = Path(artifacts_path) / run_id
        self.artifacts_path.mkdir(parents=True, exist_ok=True)

        self.tracked_processes: Dict[int, dict] = {}
        self.main_process: Optional[subprocess.Popen] = None

        logger.info(f"ProcessManager initialized for run: {run_id}")

    def execute_command(self, command: List[str], working_dir: Optional[Path] = None,
                       env: Optional[dict] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """Execute a command and track all spawned processes.

        Args:
            command: Command to execute as list of strings
            working_dir: Working directory for command execution
            env: Environment variables
            timeout: Maximum execution time in seconds

        Returns:
            Tuple of (return_code, stdout_path, stderr_path)
        """
        # Create output files
        stdout_path = self.artifacts_path / "stdout.log"
        stderr_path = self.artifacts_path / "stderr.log"

        logger.info(f"Executing command: {' '.join(command)}")

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Start the main process
        with open(stdout_path, 'w') as stdout_file, open(stderr_path, 'w') as stderr_file:
            try:
                self.main_process = subprocess.Popen(
                    command,
                    cwd=working_dir,
                    env=process_env,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True
                )

                # Track the main process
                self._track_process(self.main_process.pid, ' '.join(command))

                # Start monitoring child processes
                start_time = time.time()

                # Wait for main process with timeout
                try:
                    return_code = self.main_process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Command timed out after {timeout} seconds")
                    self._terminate_all_processes()
                    return_code = -1

                # Wait for background processes to complete
                self._wait_for_background_processes(
                    max_wait=timeout - (time.time() - start_time) if timeout else 300
                )

                logger.info(f"Command completed with return code: {return_code}")
                return return_code, str(stdout_path), str(stderr_path)

            except Exception as e:
                logger.error(f"Error executing command: {e}")
                self._terminate_all_processes()
                raise
            finally:
                self.main_process = None

    def _track_process(self, pid: int, command: str):
        """Track a process.

        Args:
            pid: Process ID
            command: Command that started the process
        """
        try:
            process = psutil.Process(pid)
            self.tracked_processes[pid] = {
                "command": command,
                "start_time": datetime.utcnow().isoformat(),
                "status": "running",
                "children": []
            }

            # Track child processes
            for child in process.children(recursive=True):
                self.tracked_processes[child.pid] = {
                    "command": ' '.join(child.cmdline()),
                    "start_time": datetime.utcnow().isoformat(),
                    "status": "running",
                    "parent": pid
                }
                self.tracked_processes[pid]["children"].append(child.pid)

            logger.debug(f"Tracking process {pid}: {command}")
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} no longer exists")

    def _wait_for_background_processes(self, max_wait: float = 300):
        """Wait for all background processes to complete.

        Args:
            max_wait: Maximum time to wait in seconds
        """
        start_time = time.time()
        logger.info("Waiting for background processes to complete...")

        while time.time() - start_time < max_wait:
            active_processes = []

            for pid in list(self.tracked_processes.keys()):
                if self._is_process_running(pid):
                    active_processes.append(pid)
                else:
                    self._mark_process_completed(pid)

            if not active_processes:
                logger.info("All background processes completed")
                break

            logger.debug(f"Active processes: {active_processes}")
            time.sleep(1)

        if active_processes:
            logger.warning(f"Some processes still running after {max_wait}s: {active_processes}")

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is still running.

        Args:
            pid: Process ID

        Returns:
            True if process is running
        """
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False

    def _mark_process_completed(self, pid: int):
        """Mark a process as completed.

        Args:
            pid: Process ID
        """
        if pid in self.tracked_processes:
            self.tracked_processes[pid]["status"] = "completed"
            self.tracked_processes[pid]["end_time"] = datetime.utcnow().isoformat()

            try:
                process = psutil.Process(pid)
                self.tracked_processes[pid]["exit_code"] = process.wait(0)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                self.tracked_processes[pid]["exit_code"] = None

    def _terminate_all_processes(self):
        """Terminate all tracked processes."""
        logger.warning("Terminating all tracked processes")

        for pid in self.tracked_processes:
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    process.terminate()
                    try:
                        process.wait(5)
                    except psutil.TimeoutExpired:
                        process.kill()
                    logger.info(f"Terminated process {pid}")
            except psutil.NoSuchProcess:
                pass

    def get_process_tree(self) -> dict:
        """Get the complete process tree.

        Returns:
            Dictionary representing the process tree
        """
        return self.tracked_processes

    def save_process_info(self):
        """Save process information to a JSON file."""
        info_path = self.artifacts_path / "process_info.json"

        with open(info_path, 'w') as f:
            json.dump(self.tracked_processes, f, indent=2)

        logger.info(f"Process information saved to {info_path}")

    def find_agent_processes(self) -> List[int]:
        """Find processes that appear to be Claude agents.

        Returns:
            List of PIDs for agent processes
        """
        agent_pids = []

        for pid, info in self.tracked_processes.items():
            command = info.get("command", "").lower()
            if any(keyword in command for keyword in ["agent", "claude", "assistant"]):
                agent_pids.append(pid)

        return agent_pids

    def wait_for_specific_process(self, pid: int, timeout: float = 60) -> bool:
        """Wait for a specific process to complete.

        Args:
            pid: Process ID to wait for
            timeout: Maximum wait time in seconds

        Returns:
            True if process completed, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self._is_process_running(pid):
                self._mark_process_completed(pid)
                return True
            time.sleep(0.5)

        return False

    def get_process_output(self, pid: int) -> Tuple[Optional[str], Optional[str]]:
        """Get output files for a specific process if available.

        Args:
            pid: Process ID

        Returns:
            Tuple of (stdout_content, stderr_content)
        """
        # This would need to be implemented based on how processes write output
        # For now, return the main process output
        stdout_path = self.artifacts_path / "stdout.log"
        stderr_path = self.artifacts_path / "stderr.log"

        stdout_content = None
        stderr_content = None

        if stdout_path.exists():
            stdout_content = stdout_path.read_text()

        if stderr_path.exists():
            stderr_content = stderr_path.read_text()

        return stdout_content, stderr_content

    def cleanup(self):
        """Clean up any remaining processes."""
        self._terminate_all_processes()
        self.save_process_info()