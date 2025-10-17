"""Tests for build process integration."""

import os
import tempfile
from pathlib import Path
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.build_manager import BuildManager, BuildResult, BuildCache
from src.core.config import Config


class TestBuildManager(unittest.TestCase):
    """Test BuildManager functionality."""

    def setUp(self):
        """Set up test environment."""
        self.config = Mock(spec=Config)
        self.config.get_standard_config_path.return_value = Path("/fake/repo")
        self.config.standard_configuration = Mock()
        self.config.standard_configuration.build_script = "./scripts/build.sh"
        self.config.standard_configuration.build_timeout = 60
        self.config.standard_configuration.cache_builds = False
        self.config.standard_configuration.cache_dir = ".build-cache"
        self.config.standard_configuration.dist_path = "dist"
        self.config.standard_configuration.source_path = "src"

    def test_needs_build_no_dist(self):
        """Test needs_build when dist doesn't exist."""
        manager = BuildManager(self.config)

        with patch.object(manager, 'get_dist_path') as mock_dist:
            # Create mock Path object
            mock_dist_path = MagicMock(spec=Path)
            mock_dist.return_value = mock_dist_path

            # No dist directory
            mock_dist_path.exists.return_value = False

            self.assertTrue(manager.needs_build())

    def test_needs_build_empty_dist(self):
        """Test needs_build when dist exists but is empty."""
        manager = BuildManager(self.config)

        with patch.object(manager, 'get_dist_path') as mock_dist:
            # Create mock Path object
            mock_dist_path = MagicMock(spec=Path)
            mock_dist.return_value = mock_dist_path

            # Dist exists but is empty
            mock_dist_path.exists.return_value = True
            mock_dist_path.iterdir.return_value = []

            self.assertTrue(manager.needs_build())

    def test_needs_build_has_content(self):
        """Test needs_build when dist has content."""
        manager = BuildManager(self.config)

        with patch.object(manager, 'get_dist_path') as mock_dist:
            # Create mock Path object
            mock_dist_path = MagicMock(spec=Path)
            mock_dist.return_value = mock_dist_path

            # Dist exists with content
            mock_dist_path.exists.return_value = True
            mock_dist_path.iterdir.return_value = [Path("/fake/repo/dist/.claude")]

            self.assertFalse(manager.needs_build())

    def test_verify_build_output_success(self):
        """Test successful build output verification."""
        manager = BuildManager(self.config)

        with patch.object(manager, 'get_dist_path') as mock_dist:
            dist_path = MagicMock(spec=Path)
            dist_path.exists.return_value = True

            # Create mock subdirectories
            claude_dir = MagicMock(spec=Path)
            claude_dir.exists.return_value = True
            adws_dir = MagicMock(spec=Path)
            adws_dir.exists.return_value = True

            dist_path.__truediv__ = lambda self, key: claude_dir if key == ".claude" else adws_dir

            mock_dist.return_value = dist_path

            result = manager.verify_build_output()
            self.assertTrue(result)

    def test_verify_build_output_missing_dirs(self):
        """Test build output verification with missing directories."""
        manager = BuildManager(self.config)

        with patch.object(manager, 'get_dist_path') as mock_dist:
            dist_path = MagicMock(spec=Path)
            dist_path.exists.return_value = True

            # Create mock subdirectories - .claude missing
            claude_dir = MagicMock(spec=Path)
            claude_dir.exists.return_value = False
            adws_dir = MagicMock(spec=Path)
            adws_dir.exists.return_value = True

            dist_path.__truediv__ = lambda self, key: claude_dir if key == ".claude" else adws_dir

            mock_dist.return_value = dist_path

            result = manager.verify_build_output()
            self.assertFalse(result)

    @patch('subprocess.run')
    def test_build_success(self, mock_run):
        """Test successful build execution."""
        manager = BuildManager(self.config)

        # Mock subprocess for git and build
        mock_run.side_effect = [
            Mock(stdout="abc123\n", returncode=0),  # git rev-parse
            Mock(stdout="Build output", stderr="", returncode=0)  # build script
        ]

        with patch.object(manager, 'verify_build_output', return_value=True):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'chmod'):
                    with patch.object(manager, 'get_dist_path') as mock_dist:
                        dist_path = Path("/fake/repo/dist")
                        mock_dist.return_value = dist_path

                        with patch('pathlib.Path.rglob', return_value=['file1', 'file2']):
                            result = manager.build()

                            self.assertTrue(result.success)
                            self.assertEqual(result.output, "Build output")
                            self.assertEqual(result.files_built, 2)
                            self.assertIsNone(result.error)

    @patch('subprocess.run')
    def test_build_failure(self, mock_run):
        """Test failed build execution."""
        manager = BuildManager(self.config)

        # Mock subprocess for git and build
        mock_run.side_effect = [
            Mock(stdout="abc123\n", returncode=0),  # git rev-parse
            Mock(stdout="", stderr="Build error", returncode=1)  # build script failure
        ]

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'chmod'):
                result = manager.build()

                self.assertFalse(result.success)
                self.assertIn("Build failed", result.error)


class TestBuildCache(unittest.TestCase):
    """Test BuildCache functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.cache = BuildCache(self.cache_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = self.cache.get_cache_key(Path("/repo"), "abc123")
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 16)

        # Same inputs should produce same key
        key2 = self.cache.get_cache_key(Path("/repo"), "abc123")
        self.assertEqual(key, key2)

        # Different inputs should produce different keys
        key3 = self.cache.get_cache_key(Path("/repo"), "def456")
        self.assertNotEqual(key, key3)

    def test_cache_store_and_retrieve(self):
        """Test storing and retrieving from cache."""
        # Create a temporary dist directory
        dist_dir = Path(self.temp_dir) / "dist"
        dist_dir.mkdir()
        (dist_dir / "test.txt").write_text("test content")

        # Store in cache
        key = "test_key"
        self.assertTrue(self.cache.store(key, dist_dir))
        self.assertTrue(self.cache.is_cached(key))

        # Retrieve from cache
        target_dir = Path(self.temp_dir) / "retrieved"
        self.assertTrue(self.cache.retrieve(key, target_dir))

        # Verify content
        self.assertTrue(target_dir.exists())
        self.assertEqual((target_dir / "test.txt").read_text(), "test content")

    def test_cache_clean(self):
        """Test cleaning old cache entries."""
        # Create old cache entry
        key = "old_key"
        cache_path = self.cache.cache_dir / key
        cache_path.mkdir(parents=True)

        # Manipulate manifest to make it old
        self.cache.manifest[key] = {
            "timestamp": 0,  # Very old timestamp
            "source": str(cache_path)
        }
        self.cache._save_manifest()

        # Clean cache
        self.cache.clean(max_age_days=1)

        # Old entry should be removed
        self.assertFalse(self.cache.is_cached(key))
        self.assertFalse(cache_path.exists())




if __name__ == '__main__':
    unittest.main()