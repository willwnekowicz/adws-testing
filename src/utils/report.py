"""JSON report generator for test results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates JSON reports for test runs."""

    def __init__(self, db_manager):
        """Initialize report generator.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def generate_run_report(self, run_id: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate a detailed report for a single run.

        Args:
            run_id: Run identifier
            output_path: Optional path to save the report

        Returns:
            Report dictionary
        """
        session = self.db_manager.get_session()
        try:
            from ..models.database import Run
            run = session.query(Run).filter_by(id=run_id).first()

            if not run:
                logger.error(f"Run not found: {run_id}")
                return {}

            report = {
                "metadata": {
                    "report_version": "1.0",
                    "generated_at": datetime.utcnow().isoformat(),
                    "framework": "ADWS Testing Framework"
                },
                "run": {
                    "id": run.id,
                    "commit_hash": run.commit_hash,
                    "branch": run.branch,
                    "model": run.model,
                    "status": run.status,
                    "start_time": run.start_time.isoformat() if run.start_time else None,
                    "end_time": run.end_time.isoformat() if run.end_time else None,
                    "duration_seconds": self._calculate_duration(run.start_time, run.end_time),
                    "configuration": run.config
                },
                "test_cases": [],
                "summary": {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "total_checks": 0,
                    "passed_checks": 0,
                    "failed_checks": 0
                }
            }

            # Add test cases
            for test_case in run.test_cases:
                tc_data = {
                    "id": test_case.id,
                    "name": test_case.name,
                    "status": test_case.status,
                    "command": test_case.command,
                    "start_time": test_case.start_time.isoformat() if test_case.start_time else None,
                    "end_time": test_case.end_time.isoformat() if test_case.end_time else None,
                    "duration_seconds": test_case.duration,
                    "results": []
                }

                # Track statistics
                test_passed = True
                checks_passed = 0
                checks_failed = 0

                # Add test results
                for result in test_case.results:
                    tc_data["results"].append({
                        "id": result.id,
                        "check_name": result.check_name,
                        "check_type": result.check_type,
                        "passed": result.passed,
                        "details": result.details,
                        "artifacts_path": result.artifacts_path,
                        "created_at": result.created_at.isoformat() if result.created_at else None
                    })

                    if result.passed:
                        checks_passed += 1
                    else:
                        checks_failed += 1
                        test_passed = False

                tc_data["passed"] = test_passed
                tc_data["checks_summary"] = {
                    "total": checks_passed + checks_failed,
                    "passed": checks_passed,
                    "failed": checks_failed
                }

                report["test_cases"].append(tc_data)

                # Update summary
                report["summary"]["total_tests"] += 1
                if test_passed:
                    report["summary"]["passed_tests"] += 1
                else:
                    report["summary"]["failed_tests"] += 1
                report["summary"]["total_checks"] += checks_passed + checks_failed
                report["summary"]["passed_checks"] += checks_passed
                report["summary"]["failed_checks"] += checks_failed

                # Add process logs if available
                if test_case.process_logs:
                    tc_data["process_logs"] = []
                    for log in test_case.process_logs:
                        tc_data["process_logs"].append({
                            "pid": log.pid,
                            "command": log.command,
                            "start_time": log.start_time.isoformat() if log.start_time else None,
                            "end_time": log.end_time.isoformat() if log.end_time else None,
                            "exit_code": log.exit_code,
                            "stdout_path": log.stdout_path,
                            "stderr_path": log.stderr_path
                        })

            # Calculate pass rate
            if report["summary"]["total_checks"] > 0:
                report["summary"]["pass_rate"] = round(
                    report["summary"]["passed_checks"] / report["summary"]["total_checks"] * 100, 2
                )
            else:
                report["summary"]["pass_rate"] = 0

            # Save to file if path provided
            if output_path:
                self._save_report(report, output_path)

            return report

        finally:
            session.close()

    def generate_comparison_report(self, run_ids: List[str],
                                 output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate a comparison report for multiple runs.

        Args:
            run_ids: List of run identifiers
            output_path: Optional path to save the report

        Returns:
            Comparison report dictionary
        """
        report = {
            "metadata": {
                "report_version": "1.0",
                "generated_at": datetime.utcnow().isoformat(),
                "framework": "ADWS Testing Framework",
                "report_type": "comparison"
            },
            "runs": [],
            "comparison": {
                "models": {},
                "commits": {},
                "overall": {
                    "total_runs": len(run_ids),
                    "all_passed": True,
                    "best_pass_rate": 0,
                    "worst_pass_rate": 100
                }
            }
        }

        for run_id in run_ids:
            run_report = self.generate_run_report(run_id)
            if run_report:
                report["runs"].append(run_report)

                # Update comparison data
                model = run_report["run"]["model"]
                if model not in report["comparison"]["models"]:
                    report["comparison"]["models"][model] = {
                        "runs": 0,
                        "passed": 0,
                        "total_checks": 0,
                        "passed_checks": 0
                    }

                model_stats = report["comparison"]["models"][model]
                model_stats["runs"] += 1
                if run_report["run"]["status"] == "completed":
                    model_stats["passed"] += 1
                model_stats["total_checks"] += run_report["summary"]["total_checks"]
                model_stats["passed_checks"] += run_report["summary"]["passed_checks"]

                # Track overall statistics
                pass_rate = run_report["summary"]["pass_rate"]
                if pass_rate < 100:
                    report["comparison"]["overall"]["all_passed"] = False
                if pass_rate > report["comparison"]["overall"]["best_pass_rate"]:
                    report["comparison"]["overall"]["best_pass_rate"] = pass_rate
                if pass_rate < report["comparison"]["overall"]["worst_pass_rate"]:
                    report["comparison"]["overall"]["worst_pass_rate"] = pass_rate

        # Calculate model pass rates
        for model, stats in report["comparison"]["models"].items():
            if stats["total_checks"] > 0:
                stats["pass_rate"] = round(
                    stats["passed_checks"] / stats["total_checks"] * 100, 2
                )
            else:
                stats["pass_rate"] = 0

        # Save to file if path provided
        if output_path:
            self._save_report(report, output_path)

        return report

    def generate_junit_xml(self, run_id: str, output_path: Path):
        """Generate JUnit XML report for CI/CD integration.

        Args:
            run_id: Run identifier
            output_path: Path to save the XML file
        """
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        run_report = self.generate_run_report(run_id)
        if not run_report:
            return

        # Create root element
        testsuites = Element('testsuites')
        testsuites.set('name', 'ADWS Testing Framework')
        testsuites.set('tests', str(run_report['summary']['total_checks']))
        testsuites.set('failures', str(run_report['summary']['failed_checks']))
        testsuites.set('time', str(run_report['run']['duration_seconds'] or 0))

        # Create testsuite for each test case
        for test_case in run_report['test_cases']:
            testsuite = SubElement(testsuites, 'testsuite')
            testsuite.set('name', test_case['name'])
            testsuite.set('tests', str(test_case['checks_summary']['total']))
            testsuite.set('failures', str(test_case['checks_summary']['failed']))
            testsuite.set('time', str(test_case['duration_seconds'] or 0))

            # Add test cases
            for result in test_case['results']:
                testcase = SubElement(testsuite, 'testcase')
                testcase.set('name', result['check_name'])
                testcase.set('classname', f"{test_case['name']}.{result['check_type']}")
                testcase.set('time', '0')

                if not result['passed']:
                    failure = SubElement(testcase, 'failure')
                    failure.set('message', f"Check failed: {result['check_name']}")
                    failure.text = result['details'] or 'No details available'

        # Pretty print XML
        xml_string = minidom.parseString(tostring(testsuites)).toprettyxml(indent="  ")

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(xml_string)

        logger.info(f"JUnit XML report saved to {output_path}")

    def _calculate_duration(self, start_time, end_time) -> Optional[float]:
        """Calculate duration between two timestamps.

        Args:
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Duration in seconds or None
        """
        if start_time and end_time:
            return (end_time - start_time).total_seconds()
        return None

    def _save_report(self, report: Dict[str, Any], output_path: Path):
        """Save report to JSON file.

        Args:
            report: Report dictionary
            output_path: Path to save the report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report saved to {output_path}")

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get test statistics for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            Statistics dictionary
        """
        from datetime import timedelta
        session = self.db_manager.get_session()

        try:
            from ..models.database import Run, TestCase, TestResult

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get runs in the period
            runs = session.query(Run).filter(
                Run.start_time >= cutoff_date
            ).all()

            stats = {
                "period_days": days,
                "total_runs": len(runs),
                "by_model": {},
                "by_status": {"completed": 0, "failed": 0, "running": 0},
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "average_duration": 0
            }

            total_duration = 0
            duration_count = 0

            for run in runs:
                # Count by status
                stats["by_status"][run.status] = stats["by_status"].get(run.status, 0) + 1

                # Count by model
                if run.model not in stats["by_model"]:
                    stats["by_model"][run.model] = {
                        "runs": 0,
                        "passed": 0,
                        "failed": 0
                    }

                stats["by_model"][run.model]["runs"] += 1
                if run.status == "completed":
                    stats["by_model"][run.model]["passed"] += 1
                else:
                    stats["by_model"][run.model]["failed"] += 1

                # Calculate duration
                if run.start_time and run.end_time:
                    duration = (run.end_time - run.start_time).total_seconds()
                    total_duration += duration
                    duration_count += 1

                # Count checks
                for test_case in run.test_cases:
                    for result in test_case.results:
                        stats["total_checks"] += 1
                        if result.passed:
                            stats["passed_checks"] += 1
                        else:
                            stats["failed_checks"] += 1

            # Calculate averages
            if duration_count > 0:
                stats["average_duration"] = round(total_duration / duration_count, 2)

            if stats["total_checks"] > 0:
                stats["overall_pass_rate"] = round(
                    stats["passed_checks"] / stats["total_checks"] * 100, 2
                )
            else:
                stats["overall_pass_rate"] = 0

            return stats

        finally:
            session.close()