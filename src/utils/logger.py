"""Logging utilities for the testing framework."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TestLogger:
    """Logger for test execution with file and console output."""

    def __init__(self, run_id: str, log_path: Path):
        """Initialize test logger.

        Args:
            run_id: Run identifier
            log_path: Path to store log files
        """
        self.run_id = run_id
        self.log_path = log_path
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Create logger instance
        self.logger = logging.getLogger(f"test_run_{run_id}")
        self.logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.logger.handlers.clear()

        # Create file handler
        log_file = self.log_path / f"test_run_{datetime.now():%Y%m%d_%H%M%S}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(file_handler)

        self.logger.info(f"Test logger initialized for run: {run_id}")

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def log_test_start(self, test_name: str):
        """Log test start."""
        self.logger.info(f"="*50)
        self.logger.info(f"Starting test: {test_name}")
        self.logger.info(f"="*50)

    def log_test_end(self, test_name: str, passed: bool, duration: float):
        """Log test end.

        Args:
            test_name: Name of the test
            passed: Whether test passed
            duration: Test duration in seconds
        """
        status = "PASSED" if passed else "FAILED"
        self.logger.info(f"="*50)
        self.logger.info(f"Test {test_name} {status} in {duration:.2f}s")
        self.logger.info(f"="*50)

    def log_check_result(self, check_name: str, passed: bool, details: Optional[str] = None):
        """Log check result.

        Args:
            check_name: Name of the check
            passed: Whether check passed
            details: Additional details
        """
        status = "✓" if passed else "✗"
        self.logger.info(f"  {status} {check_name}")
        if details:
            for line in details.split('\n'):
                if line.strip():
                    self.logger.info(f"    {line}")

    def log_command_execution(self, command: str):
        """Log command execution.

        Args:
            command: Command being executed
        """
        self.logger.info(f"Executing: {command}")

    def log_process_info(self, pid: int, command: str, status: str):
        """Log process information.

        Args:
            pid: Process ID
            command: Process command
            status: Process status
        """
        self.logger.debug(f"Process {pid}: {status} - {command}")

    def get_log_file_path(self) -> Optional[Path]:
        """Get the path to the current log file.

        Returns:
            Path to log file or None if no file handler
        """
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                return Path(handler.baseFilename)
        return None