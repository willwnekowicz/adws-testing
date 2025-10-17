"""LLM-based check implementations for complex evaluations."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from openai import OpenAI
from .base import BaseCheck, CheckResult, CheckType
import logging

logger = logging.getLogger(__name__)


class LLMJudge(BaseCheck):
    """Base class for LLM-based evaluations using OpenAI."""

    def __init__(self, name: str, model: str = "gpt-4o-mini",
                 api_key: Optional[str] = None):
        """Initialize LLM judge.

        Args:
            name: Check name
            model: OpenAI model to use
            api_key: OpenAI API key (will use env var if not provided)
        """
        super().__init__(name, CheckType.LLM_JUDGE)
        self.model = model

        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=api_key)
        logger.info(f"LLMJudge initialized with model: {model}")

    def _call_llm(self, system_prompt: str, user_prompt: str,
                  temperature: float = 0.3) -> str:
        """Call the LLM with a prompt.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Temperature for generation

        Returns:
            LLM response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise


class OutputConformanceCheck(LLMJudge):
    """Check if output conforms to initial plan or requirements."""

    def __init__(self, name: str, plan_file: str,
                 output_file: str, model: str = "gpt-4o-mini"):
        """Initialize output conformance check.

        Args:
            name: Check name
            plan_file: Path to file containing the plan/requirements
            output_file: Path to file containing the output to check
            model: OpenAI model to use
        """
        super().__init__(name, model)
        self.plan_file = plan_file
        self.output_file = output_file

    def execute(self, **kwargs) -> CheckResult:
        """Check if output conforms to plan."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        # Read plan and output
        plan_path = self.workspace_path / self.plan_file
        output_path = self.workspace_path / self.output_file

        if not plan_path.exists():
            return self._create_result(
                passed=False,
                details=f"Plan file not found: {self.plan_file}"
            )

        if not output_path.exists():
            return self._create_result(
                passed=False,
                details=f"Output file not found: {self.output_file}"
            )

        try:
            plan = plan_path.read_text()
            output = output_path.read_text()

            system_prompt = """You are a testing judge evaluating if an output conforms to a plan.
Analyze the provided plan/requirements and the actual output.
Respond with a JSON object containing:
- "passed": boolean (true if output conforms to plan)
- "score": number 0-100 (conformance score)
- "details": string (explanation of your evaluation)
- "issues": list of strings (any issues found)"""

            user_prompt = f"""Plan/Requirements:
{plan}

Actual Output:
{output}

Evaluate if the output conforms to the plan. Be thorough but fair."""

            response = self._call_llm(system_prompt, user_prompt)

            # Parse LLM response
            try:
                evaluation = json.loads(response)
                passed = evaluation.get("passed", False)
                details = f"Score: {evaluation.get('score', 0)}/100\n"
                details += f"Evaluation: {evaluation.get('details', '')}\n"

                if evaluation.get("issues"):
                    details += "\nIssues found:\n"
                    for issue in evaluation["issues"]:
                        details += f"- {issue}\n"

                return self._create_result(
                    passed=passed,
                    details=details
                )

            except json.JSONDecodeError:
                # Fallback to text response
                return self._create_result(
                    passed="pass" in response.lower(),
                    details=response
                )

        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error during LLM evaluation: {e}"
            )


class CodeQualityCheck(LLMJudge):
    """Check code quality using LLM."""

    def __init__(self, name: str, file_patterns: List[str],
                 model: str = "gpt-4o-mini"):
        """Initialize code quality check.

        Args:
            name: Check name
            file_patterns: Patterns of files to check (e.g., ["*.py", "*.js"])
            model: OpenAI model to use
        """
        super().__init__(name, model)
        self.file_patterns = file_patterns

    def execute(self, **kwargs) -> CheckResult:
        """Check code quality."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        # Find files matching patterns
        files_to_check = []
        for pattern in self.file_patterns:
            files_to_check.extend(self.workspace_path.glob(pattern))

        if not files_to_check:
            return self._create_result(
                passed=True,
                details="No files found matching patterns"
            )

        issues = []
        total_score = 0

        for file_path in files_to_check[:5]:  # Limit to 5 files to avoid excessive API calls
            try:
                code = file_path.read_text()

                system_prompt = """You are a code quality reviewer.
Analyze the provided code and evaluate its quality.
Respond with a JSON object containing:
- "score": number 0-100 (quality score)
- "issues": list of strings (quality issues found)
- "suggestions": list of strings (improvement suggestions)"""

                user_prompt = f"""File: {file_path.name}
Code:
{code[:3000]}  # Limit code length

Evaluate the code quality, focusing on:
- Correctness and logic
- Code organization
- Error handling
- Best practices"""

                response = self._call_llm(system_prompt, user_prompt)

                try:
                    evaluation = json.loads(response)
                    total_score += evaluation.get("score", 0)

                    if evaluation.get("issues"):
                        issues.append(f"\n{file_path.name}:")
                        issues.extend(f"  - {issue}" for issue in evaluation["issues"])

                except json.JSONDecodeError:
                    issues.append(f"Could not parse evaluation for {file_path.name}")

            except Exception as e:
                issues.append(f"Error checking {file_path.name}: {e}")

        avg_score = total_score / len(files_to_check) if files_to_check else 0
        passed = avg_score >= 70  # Pass if average score is 70 or above

        details = f"Average quality score: {avg_score:.1f}/100\n"
        details += f"Files checked: {len(files_to_check)}\n"
        if issues:
            details += "\nIssues found:\n" + "\n".join(issues)

        return self._create_result(
            passed=passed,
            details=details
        )


class ScriptOutputCheck(LLMJudge):
    """Run a generated script and check its output."""

    def __init__(self, name: str, script_file: str,
                 expected_behavior: str, model: str = "gpt-4o-mini"):
        """Initialize script output check.

        Args:
            name: Check name
            script_file: Path to script to execute
            expected_behavior: Description of expected behavior
            model: OpenAI model to use
        """
        super().__init__(name, model)
        self.script_file = script_file
        self.expected_behavior = expected_behavior

    def execute(self, **kwargs) -> CheckResult:
        """Execute script and check output."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        script_path = self.workspace_path / self.script_file

        if not script_path.exists():
            return self._create_result(
                passed=False,
                details=f"Script not found: {self.script_file}"
            )

        # Execute the script
        import subprocess
        try:
            result = subprocess.run(
                ["python", str(script_path)],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            script_output = f"Exit code: {result.returncode}\n"
            script_output += f"Stdout:\n{result.stdout}\n"
            script_output += f"Stderr:\n{result.stderr}"

        except subprocess.TimeoutExpired:
            return self._create_result(
                passed=False,
                details="Script execution timed out after 30 seconds"
            )
        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error executing script: {e}"
            )

        # Evaluate the output
        system_prompt = """You are a testing judge evaluating if a script's output matches expected behavior.
Analyze the script execution results and expected behavior.
Respond with a JSON object containing:
- "passed": boolean (true if output matches expectations)
- "score": number 0-100 (how well it matches)
- "details": string (explanation)
- "issues": list of strings (any issues found)"""

        user_prompt = f"""Expected Behavior:
{self.expected_behavior}

Script Execution Results:
{script_output}

Evaluate if the script output matches the expected behavior."""

        try:
            response = self._call_llm(system_prompt, user_prompt)
            evaluation = json.loads(response)

            passed = evaluation.get("passed", False)
            details = f"Score: {evaluation.get('score', 0)}/100\n"
            details += f"Evaluation: {evaluation.get('details', '')}\n"
            details += f"\nScript output:\n{script_output}"

            if evaluation.get("issues"):
                details += "\nIssues:\n"
                for issue in evaluation["issues"]:
                    details += f"- {issue}\n"

            return self._create_result(
                passed=passed,
                details=details
            )

        except json.JSONDecodeError:
            return self._create_result(
                passed=False,
                details=f"Could not parse LLM response\nScript output:\n{script_output}"
            )
        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error during evaluation: {e}"
            )


class SemanticComparisonCheck(LLMJudge):
    """Compare two texts for semantic similarity."""

    def __init__(self, name: str, file1: str, file2: str,
                 similarity_threshold: float = 0.8,
                 model: str = "gpt-4o-mini"):
        """Initialize semantic comparison check.

        Args:
            name: Check name
            file1: First file to compare
            file2: Second file to compare
            similarity_threshold: Minimum similarity score (0-1)
            model: OpenAI model to use
        """
        super().__init__(name, model)
        self.file1 = file1
        self.file2 = file2
        self.similarity_threshold = similarity_threshold

    def execute(self, **kwargs) -> CheckResult:
        """Compare files semantically."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        path1 = self.workspace_path / self.file1
        path2 = self.workspace_path / self.file2

        if not path1.exists() or not path2.exists():
            return self._create_result(
                passed=False,
                details=f"One or both files not found"
            )

        try:
            text1 = path1.read_text()[:2000]  # Limit text length
            text2 = path2.read_text()[:2000]

            system_prompt = """You are a semantic similarity judge.
Compare two texts and evaluate their semantic similarity.
Respond with a JSON object containing:
- "similarity_score": number 0-1 (semantic similarity)
- "passed": boolean (true if similarity >= threshold)
- "differences": list of key differences
- "similarities": list of key similarities"""

            user_prompt = f"""Compare these two texts for semantic similarity.
Threshold: {self.similarity_threshold}

Text 1:
{text1}

Text 2:
{text2}"""

            response = self._call_llm(system_prompt, user_prompt)
            evaluation = json.loads(response)

            score = evaluation.get("similarity_score", 0)
            passed = score >= self.similarity_threshold

            details = f"Similarity score: {score:.2f} (threshold: {self.similarity_threshold})\n"

            if evaluation.get("similarities"):
                details += "\nSimilarities:\n"
                for sim in evaluation["similarities"]:
                    details += f"- {sim}\n"

            if evaluation.get("differences"):
                details += "\nDifferences:\n"
                for diff in evaluation["differences"]:
                    details += f"- {diff}\n"

            return self._create_result(
                passed=passed,
                details=details
            )

        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error during comparison: {e}"
            )