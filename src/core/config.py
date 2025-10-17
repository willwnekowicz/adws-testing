"""Configuration management for the testing framework."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClaudeConfig:
    """Claude command configuration."""
    command: str = "claude"
    models: Dict[str, str] = field(default_factory=lambda: {
        "sonnet": "claude-3-5-sonnet-latest",
        "haiku": "claude-3-5-haiku-latest"
    })
    default_model: str = "claude-3-5-sonnet-latest"
    default_args: List[str] = field(default_factory=lambda: [
        "--stream-json",
        "--verbose",
        "-p"
    ])


@dataclass
class OpenAIConfig:
    """OpenAI configuration for LLM judge."""
    api_key: Optional[str] = None
    judge_model: str = "gpt-4o-mini"


@dataclass
class ProcessConfig:
    """Process management configuration."""
    max_wait_time: int = 300  # seconds
    poll_interval: int = 1     # seconds


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///test_runs.db"


@dataclass
class ArtifactsConfig:
    """Artifacts storage configuration."""
    base_path: str = "./runs"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class StandardConfigurationConfig:
    """Standard configuration project settings."""
    path: str = "~/ai/standard-configuration"


class Config:
    """Main configuration manager."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_file: Path to YAML configuration file
        """
        # Load environment variables
        load_dotenv()

        # Load default configuration
        self.claude = ClaudeConfig()
        self.openai = OpenAIConfig()
        self.process = ProcessConfig()
        self.database = DatabaseConfig()
        self.artifacts = ArtifactsConfig()
        self.logging = LoggingConfig()
        self.standard_configuration = StandardConfigurationConfig()

        # Load from config file if provided
        if config_file:
            self.load_from_file(config_file)
        elif Path("config.yaml").exists():
            self.load_from_file("config.yaml")

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Setup logging
        self._setup_logging()

        logger.info("Configuration loaded")

    def load_from_file(self, config_file: str):
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file
        """
        config_path = Path(config_file)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_file}")
            return

        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)

            # Update Claude configuration
            if "claude" in data:
                claude_data = data["claude"]
                self.claude.command = claude_data.get("command", self.claude.command)
                if "models" in claude_data:
                    self.claude.models.update(claude_data["models"])
                self.claude.default_model = claude_data.get("default_model", self.claude.default_model)
                if "default_args" in claude_data:
                    self.claude.default_args = claude_data["default_args"]

            # Update OpenAI configuration
            if "openai" in data:
                openai_data = data["openai"]
                self.openai.api_key = self._expand_env(openai_data.get("api_key"))
                self.openai.judge_model = openai_data.get("judge_model", self.openai.judge_model)

            # Update Process configuration
            if "process" in data:
                process_data = data["process"]
                self.process.max_wait_time = process_data.get("max_wait_time", self.process.max_wait_time)
                self.process.poll_interval = process_data.get("poll_interval", self.process.poll_interval)

            # Update Database configuration
            if "database" in data:
                database_data = data["database"]
                self.database.url = database_data.get("url", self.database.url)

            # Update Artifacts configuration
            if "artifacts" in data:
                artifacts_data = data["artifacts"]
                self.artifacts.base_path = artifacts_data.get("base_path", self.artifacts.base_path)

            # Update Logging configuration
            if "logging" in data:
                logging_data = data["logging"]
                self.logging.level = logging_data.get("level", self.logging.level)
                self.logging.format = logging_data.get("format", self.logging.format)

            # Update Standard Configuration settings
            if "standard_configuration" in data:
                sc_data = data["standard_configuration"]
                self.standard_configuration.path = sc_data.get("path", self.standard_configuration.path)

            logger.info(f"Configuration loaded from {config_file}")

        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
            raise

    def _expand_env(self, value: Optional[str]) -> Optional[str]:
        """Expand environment variables in configuration values.

        Args:
            value: Configuration value that might contain ${VAR} references

        Returns:
            Expanded value or original if no expansion needed
        """
        if not value:
            return value

        if value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var)

        return value

    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # OpenAI API key override
        if not self.openai.api_key:
            self.openai.api_key = os.getenv("OPENAI_API_KEY")

        # Database URL override
        if os.getenv("DATABASE_URL"):
            self.database.url = os.getenv("DATABASE_URL")

        # Artifacts path override
        if os.getenv("ARTIFACTS_PATH"):
            self.artifacts.base_path = os.getenv("ARTIFACTS_PATH")

        # Standard configuration path override
        if os.getenv("STANDARD_CONFIG_PATH"):
            self.standard_configuration.path = os.getenv("STANDARD_CONFIG_PATH")

    def _setup_logging(self):
        """Setup logging configuration."""
        import colorlog

        # Create color formatter
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s" + self.logging.format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )

        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.logging.level))

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add console handler with color
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        root_logger.addHandler(console_handler)

    def get_claude_command(self, model: Optional[str] = None,
                          additional_args: Optional[List[str]] = None) -> List[str]:
        """Build Claude command with arguments.

        Args:
            model: Model to use (defaults to default_model)
            additional_args: Additional command arguments

        Returns:
            Complete command as list of strings
        """
        # Resolve model
        if model and model in self.claude.models:
            model_id = self.claude.models[model]
        elif model:
            model_id = model  # Use as-is if not in mapping
        else:
            model_id = self.claude.default_model

        # Build command
        command = [self.claude.command]
        command.extend(self.claude.default_args)
        command.extend(["--model", model_id])

        if additional_args:
            command.extend(additional_args)

        return command

    def get_artifacts_path(self, run_id: str) -> Path:
        """Get artifacts path for a specific run.

        Args:
            run_id: Run identifier

        Returns:
            Path to run artifacts directory
        """
        path = Path(self.artifacts.base_path) / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_workspace_path(self, run_id: str) -> Path:
        """Get workspace path for a specific run.

        Args:
            run_id: Run identifier

        Returns:
            Path to run workspace directory
        """
        path = Path(self.artifacts.base_path) / run_id / "workspace"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_standard_config_path(self) -> Path:
        """Get resolved path to standard-configuration project.

        Returns:
            Path to standard-configuration
        """
        return Path(self.standard_configuration.path).expanduser().resolve()

    def validate(self) -> List[str]:
        """Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check standard configuration path
        sc_path = self.get_standard_config_path()
        if not sc_path.exists():
            errors.append(f"Standard configuration path does not exist: {sc_path}")
        elif not (sc_path / ".git").exists():
            errors.append(f"Standard configuration path is not a git repository: {sc_path}")

        # Check OpenAI API key if needed
        if not self.openai.api_key:
            errors.append("OpenAI API key not configured (required for LLM judge)")

        # Check Claude command is available
        import shutil
        if not shutil.which(self.claude.command):
            errors.append(f"Claude command not found in PATH: {self.claude.command}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "claude": {
                "command": self.claude.command,
                "models": self.claude.models,
                "default_model": self.claude.default_model,
                "default_args": self.claude.default_args
            },
            "openai": {
                "judge_model": self.openai.judge_model,
                "api_key_configured": bool(self.openai.api_key)
            },
            "process": {
                "max_wait_time": self.process.max_wait_time,
                "poll_interval": self.process.poll_interval
            },
            "database": {
                "url": self.database.url
            },
            "artifacts": {
                "base_path": self.artifacts.base_path
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format
            },
            "standard_configuration": {
                "path": self.standard_configuration.path
            }
        }