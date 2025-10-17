"""Build manager for handling standard-configuration build process."""

import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import logging
import json
import hashlib
import shutil

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    output: str
    error: Optional[str] = None
    duration: float = 0.0
    dist_path: Optional[Path] = None
    cache_hit: bool = False
    files_built: int = 0


class BuildCache:
    """Manages build output caching."""

    def __init__(self, cache_dir: Path):
        """Initialize build cache.

        Args:
            cache_dir: Directory to store cached builds
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.cache_dir / "manifest.json"
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load cache manifest."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache manifest: {e}")
        return {}

    def _save_manifest(self):
        """Save cache manifest."""
        try:
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache manifest: {e}")

    def get_cache_key(self, repo_path: Path, commit: str) -> str:
        """Generate cache key for build output.

        Args:
            repo_path: Path to repository
            commit: Git commit hash

        Returns:
            Cache key string
        """
        # Include repo path and commit in key
        key_data = f"{repo_path.absolute()}:{commit}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def is_cached(self, key: str) -> bool:
        """Check if build output is cached.

        Args:
            key: Cache key

        Returns:
            True if cached and valid
        """
        if key not in self.manifest:
            return False

        cache_path = self.cache_dir / key
        if not cache_path.exists():
            # Clean up invalid manifest entry
            del self.manifest[key]
            self._save_manifest()
            return False

        return True

    def store(self, key: str, dist_path: Path) -> bool:
        """Store build output in cache.

        Args:
            key: Cache key
            dist_path: Path to dist directory to cache

        Returns:
            True if stored successfully
        """
        try:
            cache_path = self.cache_dir / key

            # Remove existing cache entry
            if cache_path.exists():
                shutil.rmtree(cache_path)

            # Copy dist to cache
            shutil.copytree(dist_path, cache_path)

            # Update manifest
            self.manifest[key] = {
                "timestamp": time.time(),
                "source": str(dist_path),
                "files": len(list(cache_path.rglob("*")))
            }
            self._save_manifest()

            logger.info(f"Cached build output: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache build output: {e}")
            return False

    def retrieve(self, key: str, target_path: Path) -> bool:
        """Retrieve cached build output.

        Args:
            key: Cache key
            target_path: Where to restore the cached build

        Returns:
            True if retrieved successfully
        """
        if not self.is_cached(key):
            return False

        try:
            cache_path = self.cache_dir / key

            # Remove target if it exists
            if target_path.exists():
                shutil.rmtree(target_path)

            # Copy from cache
            shutil.copytree(cache_path, target_path)

            logger.info(f"Retrieved build from cache: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to retrieve cached build: {e}")
            return False

    def clean(self, max_age_days: int = 7):
        """Clean old cache entries.

        Args:
            max_age_days: Maximum age of cache entries in days
        """
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        cleaned = 0
        for key, info in list(self.manifest.items()):
            age = current_time - info.get("timestamp", 0)
            if age > max_age_seconds:
                cache_path = self.cache_dir / key
                if cache_path.exists():
                    shutil.rmtree(cache_path)
                del self.manifest[key]
                cleaned += 1

        if cleaned > 0:
            self._save_manifest()
            logger.info(f"Cleaned {cleaned} old cache entries")


class BuildManager:
    """Manages the build process for standard-configuration."""

    def __init__(self, config):
        """Initialize build manager.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.repo_path = config.get_standard_config_path()

        # Initialize cache if enabled
        self.cache = None
        if getattr(config.standard_configuration, 'cache_builds', True):
            cache_dir = Path(getattr(config.standard_configuration, 'cache_dir', '.build-cache'))
            self.cache = BuildCache(cache_dir)

    def build(self, commit: Optional[str] = None, force_rebuild: bool = False) -> BuildResult:
        """Execute build process for standard-configuration.

        Args:
            commit: Specific commit to build (uses current if None)
            force_rebuild: Force rebuild even if cached

        Returns:
            BuildResult with status and information
        """
        start_time = time.time()

        # Get current commit if not specified
        if not commit:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit = result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return BuildResult(
                    success=False,
                    output="",
                    error=f"Failed to get current commit: {e}",
                    duration=time.time() - start_time
                )

        # Check cache if not forcing rebuild
        if self.cache and not force_rebuild:
            cache_key = self.cache.get_cache_key(self.repo_path, commit)
            if self.cache.is_cached(cache_key):
                dist_path = self.repo_path / "dist"
                if self.cache.retrieve(cache_key, dist_path):
                    return BuildResult(
                        success=True,
                        output="Retrieved from cache",
                        duration=time.time() - start_time,
                        dist_path=dist_path,
                        cache_hit=True,
                        files_built=len(list(dist_path.rglob("*")))
                    )

        # Execute build
        build_result = self._execute_build()
        build_result.duration = time.time() - start_time

        # Cache successful build
        if build_result.success and self.cache and commit:
            cache_key = self.cache.get_cache_key(self.repo_path, commit)
            self.cache.store(cache_key, build_result.dist_path)

        return build_result

    def _execute_build(self) -> BuildResult:
        """Execute the actual build process.

        Returns:
            BuildResult with build status
        """
        # Determine build script
        build_script = getattr(
            self.config.standard_configuration,
            'build_script',
            './scripts/build.sh'
        )
        build_script_path = self.repo_path / build_script

        # Check if build script exists
        if not build_script_path.exists():
            # Check if dist already exists (may not need build)
            dist_path = self.get_dist_path()
            if dist_path.exists() and any(dist_path.iterdir()):
                logger.info("Build script not found but dist/ exists - assuming pre-built")
                return BuildResult(
                    success=True,
                    output="Using existing dist/ directory",
                    dist_path=dist_path,
                    files_built=len(list(dist_path.rglob("*")))
                )

            return BuildResult(
                success=False,
                output="",
                error=f"Build script not found: {build_script_path}"
            )

        # Make script executable
        build_script_path.chmod(0o755)

        # Run build script
        logger.info(f"Executing build script: {build_script}")
        try:
            result = subprocess.run(
                [str(build_script_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=getattr(self.config.standard_configuration, 'build_timeout', 60)
            )

            if result.returncode == 0:
                dist_path = self.get_dist_path()
                if not self.verify_build_output():
                    return BuildResult(
                        success=False,
                        output=result.stdout,
                        error="Build completed but dist/ validation failed"
                    )

                return BuildResult(
                    success=True,
                    output=result.stdout,
                    dist_path=dist_path,
                    files_built=len(list(dist_path.rglob("*")))
                )
            else:
                return BuildResult(
                    success=False,
                    output=result.stdout,
                    error=f"Build failed with exit code {result.returncode}: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                output="",
                error=f"Build timed out after {self.config.standard_configuration.build_timeout} seconds"
            )
        except Exception as e:
            return BuildResult(
                success=False,
                output="",
                error=f"Build failed with error: {e}"
            )

    def verify_build_output(self) -> bool:
        """Verify that dist/ contains expected structure.

        Returns:
            True if build output is valid
        """
        dist_path = self.get_dist_path()

        if not dist_path.exists():
            logger.error(f"Dist directory does not exist: {dist_path}")
            return False

        # Check for required directories
        required_dirs = [
            dist_path / ".claude",
            dist_path / ".adws"
        ]

        for required_dir in required_dirs:
            if not required_dir.exists():
                logger.error(f"Required directory missing: {required_dir}")
                return False

        # Check for project-init command specifically
        project_init_path = dist_path / ".claude" / "commands" / "project-init.md"
        if not project_init_path.exists():
            logger.warning(f"project-init.md not found at: {project_init_path}")
            # Don't fail - it might be in a different location

        logger.info(f"Build output verified at: {dist_path}")
        return True

    def get_dist_path(self) -> Path:
        """Get path to dist directory.

        Returns:
            Path to dist directory
        """
        dist_path = getattr(self.config.standard_configuration, 'dist_path', 'dist')
        return self.repo_path / dist_path

    def get_source_path(self) -> Path:
        """Get path to source directory.

        Returns:
            Path to source directory
        """
        source_path = getattr(self.config.standard_configuration, 'source_path', 'src')
        return self.repo_path / source_path

    def needs_build(self) -> bool:
        """Check if build is needed.

        Returns:
            True if dist doesn't exist or is empty
        """
        dist_path = self.get_dist_path()
        if not dist_path.exists():
            return True
        # Check if dist has any content
        return not any(dist_path.iterdir())

    def clean_dist(self) -> bool:
        """Clean the dist directory.

        Returns:
            True if cleaned successfully
        """
        dist_path = self.get_dist_path()
        if dist_path.exists():
            try:
                shutil.rmtree(dist_path)
                logger.info(f"Cleaned dist directory: {dist_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to clean dist directory: {e}")
                return False
        return True