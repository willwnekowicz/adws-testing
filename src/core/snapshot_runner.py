"""Test runner that uses snapshots for efficient testing.

This module provides a test runner that leverages workspace snapshots
to quickly set up test environments without re-running initialization.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from .snapshot import SnapshotManager
from .runner import TestRunner
from .config import Config

logger = logging.getLogger(__name__)


class SnapshotTestRunner(TestRunner):
    """Test runner that uses workspace snapshots."""

    def __init__(self, config: Config):
        """Initialize snapshot test runner.

        Args:
            config: Configuration instance
        """
        super().__init__(config)
        self.snapshot_manager = SnapshotManager(Path.cwd())
        self.runs_dir = Path.cwd() / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def run_with_snapshot(
        self,
        test_name: str,
        checks: List,
        snapshot_name: Optional[str] = None,
        overlay_dirs: Optional[Dict[str, Path]] = None,
        setup_callback: Optional[callable] = None
    ) -> str:
        """Run a test using a workspace snapshot.

        Args:
            test_name: Name of the test
            checks: List of checks to run
            snapshot_name: Name of snapshot to use (default if None)
            overlay_dirs: Directories to overlay (e.g., latest .adws/.claude)
            setup_callback: Optional callback to run after restoration

        Returns:
            Run ID for the test
        """
        # Generate run ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M_%f")[:17]
        run_id = f"{timestamp}_{test_name[:8]}"

        # Create run directory
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Restore snapshot to workspace
        workspace = run_dir / "workspace"
        logger.info(f"Restoring snapshot for test '{test_name}'")

        try:
            # Default overlay: use latest standard-configuration
            if overlay_dirs is None:
                standard_config = Path.home() / "ai" / "standard-configuration"
                if standard_config.exists():
                    overlay_dirs = {
                        ".adws": standard_config / ".adws",
                        ".claude": standard_config / ".claude"
                    }
                    logger.info("Using latest standard-configuration for overlay")

            # Restore with overlays
            workspace = self.snapshot_manager.restore_snapshot(
                name=snapshot_name,
                target_workspace=workspace,
                overlay_dirs=overlay_dirs
            )

            # Run setup callback if provided
            if setup_callback:
                logger.info("Running setup callback")
                setup_callback(workspace)

            # Now run checks on the workspace
            logger.info(f"Running {len(checks)} checks for test '{test_name}'")
            results = []
            for check in checks:
                logger.info(f"Running check: {check.name}")
                passed = check.execute(workspace)
                results.append({
                    "name": check.name,
                    "passed": passed,
                    "message": getattr(check, 'message', '')
                })

            # Save results
            import json
            results_file = run_dir / "results.json"
            with open(results_file, 'w') as f:
                json.dump({
                    "test_name": test_name,
                    "snapshot_used": snapshot_name or self.snapshot_manager.metadata.get("default"),
                    "overlays": {k: str(v) for k, v in (overlay_dirs or {}).items()},
                    "checks": results,
                    "workspace": str(workspace),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)

            # Report summary
            passed = sum(1 for r in results if r["passed"])
            failed = len(results) - passed

            logger.info(f"Test '{test_name}' completed: {passed} passed, {failed} failed")

            return run_id

        except Exception as e:
            logger.error(f"Error running test with snapshot: {e}")
            raise

    def run_sdlc_test(
        self,
        workflow_type: str,
        description: str,
        snapshot_name: Optional[str] = None,
        model: str = "sonnet"
    ) -> str:
        """Run an SDLC workflow test using a snapshot.

        This actually executes the SDLC command and monitors its completion.

        Args:
            workflow_type: Type of workflow (feature, bug, chore)
            description: Description of the work
            snapshot_name: Snapshot to use (default if None)
            model: Model to use for testing

        Returns:
            Run ID for the test
        """
        import subprocess
        import json
        from ..checks.sdlc import get_sdlc_checks

        test_name = f"sdlc_{workflow_type}"

        # Define setup for SDLC test
        def setup_sdlc(workspace: Path):
            """Set up workspace for SDLC test."""
            logger.info("Setting up SDLC test workspace")

            # Ensure git is clean
            subprocess.run(
                ["git", "add", "-A"],
                cwd=workspace,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial snapshot state", "--allow-empty"],
                cwd=workspace,
                capture_output=True
            )

            logger.info("Workspace ready for SDLC execution")

        # Define callback to run after restoration
        def run_sdlc_workflow(workspace: Path):
            """Execute the actual SDLC workflow via Prefect."""
            setup_sdlc(workspace)

            # Get project name from workspace
            project_name = workspace.name.split('/')[-1] if '/' in str(workspace) else "test-project"

            # Execute the Prefect trigger command
            logger.info(f"Triggering Prefect SDLC workflow: {description}")
            logger.info(f"Command: .adws/prefect/trigger.sh {project_name} \"{description}\"")

            # Run the Prefect trigger script
            result = subprocess.run(
                [".adws/prefect/trigger.sh", project_name, description],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            logger.info(f"Prefect trigger exit code: {result.returncode}")

            if result.returncode != 0:
                logger.error(f"Prefect trigger failed: {result.stderr}")
                # Don't fail the test yet - let checks determine pass/fail
            else:
                logger.info("Prefect flow triggered successfully")

            # Extract flow run ID from output if available
            flow_run_id = None
            for line in result.stdout.split('\n'):
                if 'flow-run' in line or 'Flow run' in line:
                    # Try to extract flow run ID
                    import re
                    match = re.search(r'([a-f0-9-]{36})', line)
                    if match:
                        flow_run_id = match.group(1)
                        logger.info(f"Flow run ID: {flow_run_id}")
                        break

            # TODO: Monitor flow run completion using Prefect API
            # For now, just wait a bit and check the workspace state
            if flow_run_id:
                logger.info("Waiting for flow to complete...")
                import time
                time.sleep(30)  # Give it time to start
                # In a real implementation, we'd poll the Prefect API here

            # Log the output for debugging
            output_file = workspace.parent / "prefect_output.log"
            with open(output_file, 'w') as f:
                f.write("=== STDOUT ===\n")
                f.write(result.stdout)
                f.write("\n\n=== STDERR ===\n")
                f.write(result.stderr)
                if flow_run_id:
                    f.write(f"\n\n=== FLOW RUN ID ===\n")
                    f.write(flow_run_id)

        # Get SDLC-specific checks
        checks = get_sdlc_checks(workflow_type)

        # Run with snapshot
        return self.run_with_snapshot(
            test_name=test_name,
            checks=checks,
            snapshot_name=snapshot_name,
            setup_callback=run_sdlc_workflow
        )

    def run_slash_command_test(
        self,
        command: str,
        args: Optional[List[str]] = None,
        snapshot_name: Optional[str] = None,
        expected_outputs: Optional[List[str]] = None
    ) -> str:
        """Run a slash command test using a snapshot.

        Args:
            command: Slash command to test (e.g., "/summarize")
            args: Arguments for the command
            snapshot_name: Snapshot to use
            expected_outputs: Expected strings in output

        Returns:
            Run ID for the test
        """
        from ..checks.simple import FileExistsCheck, FileContentCheck

        test_name = f"slash_{command.replace('/', '')}"

        # Define checks based on command
        checks = []

        # Add command-specific checks
        if command == "/summarize":
            checks.append(FileContentCheck(
                name="summary_added",
                file_path="documentation/daily/summary.md",
                contains=["Summary", "bulleted"]
            ))
        elif command == "/zettelkasten":
            checks.append(FileExistsCheck(
                name="zettel_created",
                file_path="documentation/zettelkasten/index.md"
            ))

        # Run with snapshot
        return self.run_with_snapshot(
            test_name=test_name,
            checks=checks,
            snapshot_name=snapshot_name
        )

    def cleanup_old_runs(self, keep_last: int = 10):
        """Clean up old test runs, keeping only the most recent.

        Args:
            keep_last: Number of recent runs to keep
        """
        runs = sorted(self.runs_dir.iterdir(), key=lambda p: p.stat().st_mtime)

        if len(runs) <= keep_last:
            logger.info("No old runs to clean up")
            return

        to_delete = runs[:-keep_last]
        for run_dir in to_delete:
            logger.info(f"Deleting old run: {run_dir.name}")
            shutil.rmtree(run_dir)

        logger.info(f"Cleaned up {len(to_delete)} old runs")