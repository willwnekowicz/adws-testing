"""Artifact management utilities."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manages test artifacts and output files."""

    def __init__(self, run_id: str, base_path: Path):
        """Initialize artifact manager.

        Args:
            run_id: Run identifier
            base_path: Base path for artifacts
        """
        self.run_id = run_id
        self.base_path = Path(base_path) / run_id
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        self.workspace_path = self.base_path / "workspace"
        self.logs_path = self.base_path / "logs"
        self.outputs_path = self.base_path / "outputs"
        self.checks_path = self.base_path / "checks"

        for path in [self.logs_path, self.outputs_path, self.checks_path]:
            path.mkdir(exist_ok=True)

        logger.info(f"ArtifactManager initialized for run: {run_id}")

    def save_json(self, data: Dict[str, Any], filename: str, subdir: Optional[str] = None) -> Path:
        """Save data as JSON file.

        Args:
            data: Data to save
            filename: File name (without extension)
            subdir: Optional subdirectory

        Returns:
            Path to saved file
        """
        if subdir:
            path = self.base_path / subdir
            path.mkdir(exist_ok=True)
        else:
            path = self.base_path

        file_path = path / f"{filename}.json"

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.debug(f"Saved JSON to {file_path}")
        return file_path

    def save_text(self, content: str, filename: str, subdir: Optional[str] = None) -> Path:
        """Save text content to file.

        Args:
            content: Text content to save
            filename: File name
            subdir: Optional subdirectory

        Returns:
            Path to saved file
        """
        if subdir:
            path = self.base_path / subdir
            path.mkdir(exist_ok=True)
        else:
            path = self.base_path

        file_path = path / filename

        with open(file_path, 'w') as f:
            f.write(content)

        logger.debug(f"Saved text to {file_path}")
        return file_path

    def copy_file(self, source: Path, dest_name: str, subdir: Optional[str] = None) -> Path:
        """Copy a file to artifacts.

        Args:
            source: Source file path
            dest_name: Destination file name
            subdir: Optional subdirectory

        Returns:
            Path to copied file
        """
        if subdir:
            path = self.base_path / subdir
            path.mkdir(exist_ok=True)
        else:
            path = self.base_path

        dest_path = path / dest_name

        shutil.copy2(source, dest_path)
        logger.debug(f"Copied {source} to {dest_path}")
        return dest_path

    def save_command_output(self, stdout: str, stderr: str, command: str,
                          test_name: str) -> Dict[str, Path]:
        """Save command output to files.

        Args:
            stdout: Standard output
            stderr: Standard error
            command: Command that was executed
            test_name: Name of the test

        Returns:
            Dictionary with paths to saved files
        """
        output_dir = self.outputs_path / test_name
        output_dir.mkdir(exist_ok=True)

        paths = {}

        # Save stdout
        if stdout:
            stdout_path = output_dir / "stdout.txt"
            stdout_path.write_text(stdout)
            paths["stdout"] = stdout_path

        # Save stderr
        if stderr:
            stderr_path = output_dir / "stderr.txt"
            stderr_path.write_text(stderr)
            paths["stderr"] = stderr_path

        # Save command
        command_path = output_dir / "command.txt"
        command_path.write_text(command)
        paths["command"] = command_path

        return paths

    def save_check_result(self, check_name: str, result: Dict[str, Any]) -> Path:
        """Save check result to file.

        Args:
            check_name: Name of the check
            result: Check result data

        Returns:
            Path to saved file
        """
        check_file = self.checks_path / f"{check_name}.json"

        with open(check_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        return check_file

    def save_run_summary(self, summary: Dict[str, Any]) -> Path:
        """Save run summary to file.

        Args:
            summary: Run summary data

        Returns:
            Path to saved file
        """
        summary_path = self.base_path / "summary.json"

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Run summary saved to {summary_path}")
        return summary_path

    def create_archive(self) -> Path:
        """Create an archive of all artifacts.

        Returns:
            Path to created archive
        """
        archive_name = f"run_{self.run_id}_{datetime.now():%Y%m%d_%H%M%S}"
        archive_path = self.base_path.parent / f"{archive_name}.tar.gz"

        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'gztar',
            self.base_path
        )

        logger.info(f"Created archive: {archive_path}")
        return archive_path

    def get_artifact_list(self) -> List[Dict[str, Any]]:
        """Get list of all artifacts.

        Returns:
            List of artifact information
        """
        artifacts = []

        for item in self.base_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(self.base_path)
                artifacts.append({
                    "path": str(relative_path),
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })

        return artifacts

    def cleanup(self, keep_archive: bool = True):
        """Clean up artifacts.

        Args:
            keep_archive: Whether to create and keep an archive
        """
        if keep_archive:
            self.create_archive()

        # Remove artifacts directory
        shutil.rmtree(self.base_path)
        logger.info(f"Cleaned up artifacts for run: {self.run_id}")

    def get_workspace_file(self, file_path: str) -> Optional[Path]:
        """Get a file from the workspace.

        Args:
            file_path: Relative path to file in workspace

        Returns:
            Full path to file if it exists
        """
        full_path = self.workspace_path / file_path

        if full_path.exists():
            return full_path

        return None

    def list_workspace_files(self) -> List[str]:
        """List all files in the workspace.

        Returns:
            List of relative file paths
        """
        if not self.workspace_path.exists():
            return []

        files = []
        for item in self.workspace_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(self.workspace_path)
                files.append(str(relative_path))

        return sorted(files)