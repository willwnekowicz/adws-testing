"""ADW (AI Developer Workflow) test runner."""

import subprocess
import time
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
import logging
import ast
import re

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class AdwResult:
    """Result of ADW execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    claude_executed: bool = False
    error_message: Optional[str] = None


class AdwRunner:
    """Executes ADW Python scripts via uv."""

    def __init__(self, config: Config):
        """Initialize ADW runner.

        Args:
            config: Configuration instance
        """
        self.config = config
        logger.info("AdwRunner initialized")

    def get_adw_path(self, adw_name: str) -> Path:
        """Get the full path to an ADW script.

        Args:
            adw_name: Name of the ADW script (e.g., "adw_init.py")

        Returns:
            Path to the ADW script

        Raises:
            FileNotFoundError: If the ADW script doesn't exist
        """
        # Build path relative to standard-configuration
        sc_path = self.config.get_standard_config_path()
        adw_dir = sc_path / self.config.adw.adw_directory
        adw_path = adw_dir / adw_name

        if not adw_path.exists():
            raise FileNotFoundError(f"ADW script not found: {adw_path}")

        return adw_path

    def validate_adw_script(self, script_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate an ADW script.

        Args:
            script_path: Path to the ADW script

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not script_path.exists():
            return False, f"Script does not exist: {script_path}"

        if not script_path.is_file():
            return False, f"Script is not a file: {script_path}"

        # Read script content
        try:
            content = script_path.read_text()
        except Exception as e:
            return False, f"Cannot read script: {e}"

        # Check for shebang
        lines = content.split('\n')
        if not lines or not lines[0].startswith('#!'):
            return False, "Script missing shebang line"

        # Check Python syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            return False, f"Invalid Python syntax: {e}"

        # Check for uv dependencies block (PEP 723)
        # Look for: # /// script
        has_uv_block = '# /// script' in content or '# /// pyproject' in content
        if not has_uv_block:
            logger.warning(f"Script {script_path.name} missing uv dependencies block")
            # Not a hard failure, but worth noting

        return True, None

    def execute_adw(
        self,
        script_path: Path,
        args: Optional[List[str]] = None,
        workspace: Optional[Path] = None,
        timeout: Optional[int] = None,
        dry_run: bool = False
    ) -> AdwResult:
        """Execute an ADW script.

        Args:
            script_path: Path to the ADW script
            args: Additional arguments to pass to the script
            workspace: Working directory for execution
            timeout: Execution timeout in seconds (None = use config default)
            dry_run: Whether to run in dry-run mode

        Returns:
            AdwResult with execution details
        """
        start_time = time.time()

        # Validate script first
        is_valid, error = self.validate_adw_script(script_path)
        if not is_valid:
            return AdwResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=0.0,
                error_message=error
            )

        # Build command
        command = [
            self.config.adw.uv_command,
            "run",
            "--python",
            self.config.adw.python_version,
            str(script_path)
        ]

        # Add dry-run flag if requested
        if dry_run:
            command.append("--dry-run")

        # Add additional args
        if args:
            command.extend(args)

        # Set working directory
        cwd = workspace if workspace else Path.cwd()

        logger.info(f"Executing ADW: {' '.join(command)}")
        logger.info(f"Working directory: {cwd}")

        # Execute command
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout or self.config.adw.adw_timeout
            )

            duration = time.time() - start_time
            stdout = result.stdout
            stderr = result.stderr

            # Detect if Claude was executed (look for Claude CLI indicators in output)
            claude_executed = self._detect_claude_execution(stdout, stderr)

            success = result.returncode == 0

            logger.info(f"ADW execution completed: exit_code={result.returncode}, duration={duration:.2f}s")

            return AdwResult(
                success=success,
                exit_code=result.returncode,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                claude_executed=claude_executed
            )

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            logger.error(f"ADW execution timed out after {duration:.2f}s")

            return AdwResult(
                success=False,
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                duration=duration,
                error_message=f"Execution timed out after {timeout or self.config.adw.adw_timeout}s"
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error executing ADW: {e}")

            return AdwResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                error_message=str(e)
            )

    def _detect_claude_execution(self, stdout: str, stderr: str) -> bool:
        """Detect if Claude CLI was executed based on output.

        Args:
            stdout: Standard output
            stderr: Standard error

        Returns:
            True if Claude execution was detected
        """
        # Look for common Claude CLI indicators
        indicators = [
            "claude",  # Command name
            "anthropic",  # Company name
            "model:",  # Model selection output
            "sonnet",  # Model name
            "haiku",  # Model name
            "streaming",  # Common in Claude output
            "token",  # Token usage
        ]

        combined = (stdout + stderr).lower()

        # Check if any indicators are present
        for indicator in indicators:
            if indicator in combined:
                logger.debug(f"Detected Claude execution via indicator: {indicator}")
                return True

        return False

    def get_script_metadata(self, script_path: Path) -> dict:
        """Extract metadata from ADW script.

        Args:
            script_path: Path to the ADW script

        Returns:
            Dictionary with script metadata
        """
        metadata = {
            "name": script_path.name,
            "path": str(script_path),
            "python_version_required": None,
            "dependencies": [],
            "description": None
        }

        try:
            content = script_path.read_text()

            # Extract Python version from dependencies block
            version_match = re.search(r'requires-python\s*=\s*"([^"]+)"', content)
            if version_match:
                metadata["python_version_required"] = version_match.group(1)

            # Extract dependencies
            dep_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if dep_match:
                deps_str = dep_match.group(1)
                deps = [d.strip().strip('"\'') for d in deps_str.split(',') if d.strip()]
                metadata["dependencies"] = deps

            # Extract docstring as description
            lines = content.split('\n')
            in_docstring = False
            docstring_lines = []
            for line in lines:
                if '"""' in line or "'''" in line:
                    if in_docstring:
                        break
                    in_docstring = True
                    continue
                if in_docstring:
                    docstring_lines.append(line)

            if docstring_lines:
                metadata["description"] = '\n'.join(docstring_lines).strip()

        except Exception as e:
            logger.warning(f"Error extracting metadata from {script_path}: {e}")

        return metadata
