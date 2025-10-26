"""Main test runner for orchestrating test execution."""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import uuid

from ..models.database import DatabaseManager
from ..utils.logger import TestLogger
from ..utils.artifacts import ArtifactManager
from .config import Config
from .git_manager import GitManager
from .process_manager import ProcessManager
from .build_manager import BuildManager
from .adw_runner import AdwRunner, AdwResult
from ..checks.base import CheckRegistry, CheckResult

logger = logging.getLogger(__name__)


class TestRunner:
    """Main test runner that orchestrates test execution."""

    def __init__(self, config: Config):
        """Initialize test runner.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.db_manager = DatabaseManager(config.database.url)
        self.db_manager.create_tables()
        self.check_registry = CheckRegistry()
        self.build_manager = BuildManager(config)
        self.adw_runner = AdwRunner(config)

        logger.info("TestRunner initialized")

    def run_test(self, test_name: str, model: str,
                commit: Optional[str] = None,
                branch: Optional[str] = None,
                checks: Optional[List[Any]] = None,
                build: Optional[bool] = None,
                dry_run: bool = False,
                adw_args: Optional[List[str]] = None) -> str:
        """Run a single test.

        Args:
            test_name: Name of the test
            model: Model to use (sonnet or haiku)
            commit: Specific commit to test (optional)
            branch: Specific branch to test (optional)
            checks: List of check instances to run
            build: Whether to build before testing (None=auto-detect)
            dry_run: Whether to run ADW in dry-run mode (ADW tests only)
            adw_args: Arguments to pass to ADW script (ADW tests only)

        Returns:
            Run ID
        """
        # Generate timestamp-based run ID (format: YYYYMMDD_HHMM_shortUUID)
        now = datetime.now()
        timestamp_prefix = now.strftime("%Y%m%d_%H%M")
        # Add a short UUID suffix to ensure uniqueness for runs in the same minute
        short_uuid = str(uuid.uuid4())[:8]
        run_id = f"{timestamp_prefix}_{short_uuid}"
        start_time = datetime.utcnow()

        # Detect test type: ADW tests start with "adw-" or "adw_"
        is_adw_test = test_name.startswith("adw-") or test_name.startswith("adw_")

        # If this is an ADW test, delegate to ADW test runner
        if is_adw_test:
            return self._run_adw_test(
                test_name=test_name,
                model=model,
                commit=commit,
                branch=branch,
                checks=checks,
                build=build,
                dry_run=dry_run,
                adw_args=adw_args,
                run_id=run_id
            )

        # Initialize components for slash command tests
        git_manager = GitManager(self.config.get_standard_config_path())
        artifact_manager = ArtifactManager(run_id, Path(self.config.artifacts.base_path))
        test_logger = TestLogger(run_id, artifact_manager.logs_path)
        process_manager = ProcessManager(run_id, self.config.artifacts.base_path)

        test_logger.info(f"Starting test run: {run_id}")
        test_logger.info(f"Test: {test_name}")
        test_logger.info(f"Model: {model}")

        # Get current git info
        original_commit, original_branch = git_manager.get_current_info()

        # Checkout specific commit/branch if requested
        if commit:
            test_commit = git_manager.checkout(commit)
        elif branch:
            test_commit = git_manager.checkout(branch)
        else:
            test_commit = original_commit

        test_logger.info(f"Testing commit: {test_commit}")

        # Determine whether to build
        should_build = build
        if should_build is None:
            # Use configuration setting (default is True)
            should_build = self.config.standard_configuration.build_required

        if should_build:
            # Check if build is actually needed
            if not self.build_manager.needs_build():
                test_logger.info("Build output already exists, skipping build")
                should_build = False

        # Create run in database first
        db_run_id = self.db_manager.create_run(
            commit_hash=test_commit,
            branch=branch or original_branch,
            model=model,
            config=self.config.to_dict()
        )

        # Execute build if needed
        build_result = None
        build_id = None
        if should_build:
            test_logger.info("Executing build process...")
            build_result = self.build_manager.build(commit=test_commit)

            # Record build in database
            build_status = 'success' if build_result.success else 'failed'
            build_id = self.db_manager.add_build(
                run_id=db_run_id,
                commit_hash=test_commit,
                build_script=self.config.standard_configuration.build_script,
                status=build_status,
                duration_seconds=build_result.duration,
                output_path=str(build_result.dist_path) if build_result.dist_path else None,
                error_message=build_result.error,
                cache_hit=build_result.cache_hit,
                files_built=build_result.files_built
            )

            if not build_result.success:
                test_logger.error(f"Build failed: {build_result.error}")
                self.db_manager.complete_run(db_run_id, "failed")
                raise Exception(f"Build failed: {build_result.error}")

            test_logger.info(f"Build completed successfully (cache_hit={build_result.cache_hit}, files={build_result.files_built})")
            if build_result.cache_hit:
                test_logger.info("Build was retrieved from cache")

        # Create test workspace
        # Use temp directory for project-init to ensure complete isolation
        use_temp = (test_name == "project-init")
        # Always use dist directory (we ensure it exists via build)
        use_dist = True
        workspace_path = git_manager.create_test_workspace(
            run_id,
            self.config.artifacts.base_path,
            use_temp_dir=use_temp,
            use_dist=use_dist
        )
        test_logger.info(f"Created workspace: {workspace_path}")

        # Add test case to database
        test_case_id = self.db_manager.add_test_case(
            run_id=db_run_id,
            name=test_name,
            command=f"Test: {test_name} with model: {model}"
        )

        # Track test execution
        test_start = time.time()
        test_logger.log_test_start(test_name)

        try:
            # Prepare workspace based on test requirements
            if test_name == "project-init":
                git_manager.prepare_for_project_init(workspace_path)

            # Build and execute command
            command = self._build_command(test_name, model)
            test_logger.log_command_execution(' '.join(command))

            return_code, stdout_path, stderr_path = process_manager.execute_command(
                command=command,
                working_dir=workspace_path,
                timeout=self.config.process.max_wait_time
            )

            # Save command output
            stdout_content = Path(stdout_path).read_text() if Path(stdout_path).exists() else ""
            stderr_content = Path(stderr_path).read_text() if Path(stderr_path).exists() else ""

            artifact_manager.save_command_output(
                stdout=stdout_content,
                stderr=stderr_content,
                command=' '.join(command),
                test_name=test_name
            )

            # Run checks if provided
            check_results = []
            if checks:
                test_logger.info("Running checks...")
                for check in checks:
                    self.check_registry.register(check)

                check_results = self.check_registry.execute_checks(
                    check_names=[check.name for check in checks],
                    workspace_path=workspace_path,
                    artifacts_path=artifact_manager.checks_path,
                    duration=time.time() - test_start
                )

                # Log and save check results
                for result in check_results:
                    test_logger.log_check_result(
                        check_name=result.name,
                        passed=result.passed,
                        details=result.details
                    )

                    artifact_manager.save_check_result(
                        check_name=result.name,
                        result=result.to_dict()
                    )

                    self.db_manager.add_test_result(
                        test_case_id=test_case_id,
                        check_name=result.name,
                        check_type=result.check_type.value,
                        passed=result.passed,
                        details=result.details
                    )

            # Determine overall test status
            test_passed = all(r.passed for r in check_results) if check_results else return_code == 0
            test_duration = time.time() - test_start

            test_logger.log_test_end(test_name, test_passed, test_duration)

            # Save process information
            process_manager.save_process_info()

            # Create run summary
            summary = self._create_run_summary(
                run_id=run_id,
                test_name=test_name,
                model=model,
                commit=test_commit,
                branch=branch or original_branch,
                passed=test_passed,
                duration=test_duration,
                checks=len(check_results),
                checks_passed=sum(1 for r in check_results if r.passed)
            )

            artifact_manager.save_run_summary(summary)

            # Update database
            self.db_manager.complete_run(
                run_id=db_run_id,
                status="completed" if test_passed else "failed"
            )

            return run_id

        except Exception as e:
            test_logger.error(f"Error during test execution: {e}")
            self.db_manager.complete_run(db_run_id, "failed")
            raise

        finally:
            # Cleanup
            process_manager.cleanup()

            # Reset git to original state
            git_manager.reset_to_original(original_commit, original_branch)

    def run_multiple_tests(self, test_name: str,
                          models: Optional[List[str]] = None,
                          commit: Optional[str] = None,
                          branch: Optional[str] = None,
                          checks: Optional[List[Any]] = None,
                          build: Optional[bool] = None) -> List[str]:
        """Run tests with multiple models.

        Args:
            test_name: Name of the test
            models: List of models to test (defaults to all configured)
            commit: Specific commit to test
            branch: Specific branch to test
            checks: List of check instances to run
            build: Whether to build before testing (None=auto-detect)

        Returns:
            List of run IDs
        """
        if not models:
            models = list(self.config.claude.models.keys())

        run_ids = []
        for model in models:
            try:
                logger.info(f"Running test {test_name} with model {model}")
                run_id = self.run_test(
                    test_name=test_name,
                    model=model,
                    commit=commit,
                    branch=branch,
                    checks=checks,
                    build=build
                )
                run_ids.append(run_id)
            except Exception as e:
                logger.error(f"Failed to run test with model {model}: {e}")

        return run_ids

    def _build_command(self, test_name: str, model: str) -> List[str]:
        """Build command for test execution.

        Args:
            test_name: Name of the test
            model: Model to use

        Returns:
            Command as list of strings
        """
        if test_name == "project-init":
            command = self.config.get_claude_command(
                model=model,
                additional_args=["--", "/project-init"]
            )
        elif test_name == "init-git":
            command = self.config.get_claude_command(
                model=model,
                additional_args=["--", "/init-git"]
            )
        elif test_name == "init-cloudflare":
            command = self.config.get_claude_command(
                model=model,
                additional_args=["--", "/init-cloudflare"]
            )
        else:
            # Add other test commands as needed
            command = self.config.get_claude_command(model=model)

        return command

    def _run_adw_test(
        self,
        test_name: str,
        model: str,
        commit: Optional[str],
        branch: Optional[str],
        checks: Optional[List[Any]],
        build: Optional[bool],
        dry_run: bool,
        adw_args: Optional[List[str]],
        run_id: str
    ) -> str:
        """Run an ADW test.

        Args:
            test_name: Name of the ADW test (e.g., "adw-init")
            model: Model to use
            commit: Specific commit to test
            branch: Specific branch to test
            checks: List of check instances
            build: Whether to build before testing
            dry_run: Whether to run in dry-run mode
            adw_args: Arguments to pass to ADW script
            run_id: Pre-generated run ID

        Returns:
            Run ID
        """
        # Initialize components
        git_manager = GitManager(self.config.get_standard_config_path())
        artifact_manager = ArtifactManager(run_id, Path(self.config.artifacts.base_path))
        test_logger = TestLogger(run_id, artifact_manager.logs_path)

        test_logger.info(f"Starting ADW test run: {run_id}")
        test_logger.info(f"Test: {test_name}")
        test_logger.info(f"Model: {model}")

        # Get current git info
        original_commit, original_branch = git_manager.get_current_info()

        # Checkout specific commit/branch if requested
        if commit:
            test_commit = git_manager.checkout(commit)
        elif branch:
            test_commit = git_manager.checkout(branch)
        else:
            test_commit = original_commit

        test_logger.info(f"Testing commit: {test_commit}")

        # Determine whether to build
        should_build = build
        if should_build is None:
            should_build = self.config.standard_configuration.build_required

        if should_build and not self.build_manager.needs_build():
            test_logger.info("Build output already exists, skipping build")
            should_build = False

        # Create run in database
        db_run_id = self.db_manager.create_run(
            commit_hash=test_commit,
            branch=branch or original_branch,
            model=model,
            config=self.config.to_dict()
        )

        # Execute build if needed
        if should_build:
            test_logger.info("Executing build process...")
            build_result = self.build_manager.build(commit=test_commit)

            build_status = 'success' if build_result.success else 'failed'
            self.db_manager.add_build(
                run_id=db_run_id,
                commit_hash=test_commit,
                build_script=self.config.standard_configuration.build_script,
                status=build_status,
                duration_seconds=build_result.duration,
                output_path=str(build_result.dist_path) if build_result.dist_path else None,
                error_message=build_result.error,
                cache_hit=build_result.cache_hit,
                files_built=build_result.files_built
            )

            if not build_result.success:
                test_logger.error(f"Build failed: {build_result.error}")
                self.db_manager.complete_run(db_run_id, "failed")
                raise Exception(f"Build failed: {build_result.error}")

            test_logger.info(f"Build completed successfully")

        # Create test workspace
        workspace_path = git_manager.create_test_workspace(
            run_id,
            self.config.artifacts.base_path,
            use_temp_dir=True,  # ADW tests use temp directories
            use_dist=True  # Ensure dist directory is available
        )
        test_logger.info(f"Created workspace: {workspace_path}")

        # Add test case to database
        test_case_id = self.db_manager.add_test_case(
            run_id=db_run_id,
            name=test_name,
            command=f"ADW Test: {test_name}"
        )

        # Update test type to ADW
        self.db_manager.update_test_case_type(test_case_id, "adw")

        # Track test execution
        test_start = time.time()
        test_logger.log_test_start(test_name)

        try:
            # Convert test name to script name (e.g., "adw-init" -> "adw_init.py")
            adw_script_name = test_name.replace("-", "_") + ".py"

            # Get ADW script path
            adw_script_path = self.adw_runner.get_adw_path(adw_script_name)
            test_logger.info(f"ADW script: {adw_script_path}")

            # Execute ADW script
            test_logger.info(f"Executing ADW with args: {adw_args}")
            adw_result = self.adw_runner.execute_adw(
                script_path=adw_script_path,
                args=adw_args or [],
                workspace=workspace_path,
                dry_run=dry_run
            )

            # Save ADW output to artifacts
            artifact_manager.save_command_output(
                stdout=adw_result.stdout,
                stderr=adw_result.stderr,
                command=f"ADW: {adw_script_name}",
                test_name=test_name
            )

            # Record ADW test in database
            adw_test_id = self.db_manager.add_adw_test(
                test_case_id=test_case_id,
                adw_script_name=adw_script_name,
                python_version=self.config.adw.python_version,
                script_execution_status="success" if adw_result.success else "failed",
                claude_execution_status="success" if adw_result.claude_executed else "not_run",
                dry_run=dry_run,
                script_output_path=str(artifact_manager.logs_path / "stdout.log")
            )

            # Run checks if provided
            check_results = []
            if checks:
                test_logger.info("Running checks...")
                for check in checks:
                    self.check_registry.register(check)

                check_results = self.check_registry.execute_checks(
                    check_names=[check.name for check in checks],
                    workspace_path=workspace_path,
                    artifacts_path=artifact_manager.checks_path,
                    adw_result=adw_result,
                    script_path=adw_script_path,
                    duration=time.time() - test_start
                )

                # Log and save check results
                for result in check_results:
                    test_logger.log_check_result(
                        check_name=result.name,
                        passed=result.passed,
                        details=result.details
                    )

                    artifact_manager.save_check_result(
                        check_name=result.name,
                        result=result.to_dict()
                    )

                    self.db_manager.add_test_result(
                        test_case_id=test_case_id,
                        check_name=result.name,
                        check_type=result.check_type.value,
                        passed=result.passed,
                        details=result.details
                    )

            # Determine overall test status
            test_passed = all(r.passed for r in check_results) if check_results else adw_result.success
            test_duration = time.time() - test_start

            test_logger.log_test_end(test_name, test_passed, test_duration)

            # Create run summary
            summary = self._create_run_summary(
                run_id=run_id,
                test_name=test_name,
                model=model,
                commit=test_commit,
                branch=branch or original_branch,
                passed=test_passed,
                duration=test_duration,
                checks=len(check_results),
                checks_passed=sum(1 for r in check_results if r.passed)
            )

            # Add ADW-specific info to summary
            summary["adw"] = {
                "script_name": adw_script_name,
                "python_version": self.config.adw.python_version,
                "dry_run": dry_run,
                "claude_executed": adw_result.claude_executed
            }

            artifact_manager.save_run_summary(summary)

            # Update database
            self.db_manager.complete_run(
                run_id=db_run_id,
                status="completed" if test_passed else "failed"
            )

            return run_id

        except Exception as e:
            test_logger.error(f"Error during ADW test execution: {e}")
            self.db_manager.complete_run(db_run_id, "failed")
            raise

        finally:
            # Reset git to original state
            git_manager.reset_to_original(original_commit, original_branch)

    def _create_run_summary(self, run_id: str, test_name: str, model: str,
                          commit: str, branch: str, passed: bool,
                          duration: float, checks: int,
                          checks_passed: int) -> Dict[str, Any]:
        """Create run summary.

        Args:
            run_id: Run ID
            test_name: Test name
            model: Model used
            commit: Commit tested
            branch: Branch tested
            passed: Whether test passed
            duration: Test duration
            checks: Total checks run
            checks_passed: Checks that passed

        Returns:
            Summary dictionary
        """
        return {
            "run_id": run_id,
            "test_name": test_name,
            "model": model,
            "commit": commit[:8] if commit else None,
            "branch": branch,
            "status": "passed" if passed else "failed",
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "total": checks,
                "passed": checks_passed,
                "failed": checks - checks_passed
            }
        }

    def get_run_results(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific run.

        Args:
            run_id: Run ID

        Returns:
            Run results or None if not found
        """
        session = self.db_manager.get_session()
        try:
            from ..models.database import Run
            run = session.query(Run).filter_by(id=run_id).first()

            if not run:
                return None

            results = {
                "run_id": run.id,
                "commit": run.commit_hash,
                "branch": run.branch,
                "model": run.model,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "test_cases": []
            }

            for test_case in run.test_cases:
                tc_data = {
                    "name": test_case.name,
                    "status": test_case.status,
                    "duration": test_case.duration,
                    "results": []
                }

                for result in test_case.results:
                    tc_data["results"].append({
                        "check_name": result.check_name,
                        "check_type": result.check_type,
                        "passed": result.passed,
                        "details": result.details
                    })

                results["test_cases"].append(tc_data)

            return results

        finally:
            session.close()

    def list_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summaries
        """
        session = self.db_manager.get_session()
        try:
            from ..models.database import Run
            runs = session.query(Run).order_by(Run.start_time.desc()).limit(limit).all()

            return [
                {
                    "run_id": run.id,
                    "commit": run.commit_hash[:8] if run.commit_hash else None,
                    "branch": run.branch,
                    "model": run.model,
                    "status": run.status,
                    "start_time": run.start_time.isoformat() if run.start_time else None
                }
                for run in runs
            ]

        finally:
            session.close()