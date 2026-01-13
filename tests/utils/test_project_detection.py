"""
Tests for src/memorygraph/utils/project_detection.py

Following TDD approach to achieve 100% coverage.
"""
import os
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from memorygraph.utils.project_detection import (
    detect_project_context,
    _detect_from_git,
    get_project_from_memories,
)


class TestDetectProjectContext:
    """Test detect_project_context function."""

    @patch("memorygraph.utils.project_detection._detect_from_git")
    def test_detect_with_git_repo(self, mock_git):
        """Test detection in a git repository."""
        mock_git.return_value = {
            "project_name": "test-project",
            "project_path": "/path/to/test-project",
            "git_remote": "https://github.com/user/test-project.git",
        }

        result = detect_project_context("/path/to/test-project")

        assert result is not None
        assert result["project_name"] == "test-project"
        assert result["is_git_repo"] is True
        assert result["git_remote"] == "https://github.com/user/test-project.git"

    @patch("memorygraph.utils.project_detection._detect_from_git")
    def test_detect_without_git_fallback_to_dir_name(self, mock_git):
        """Test fallback to directory name when not a git repo."""
        mock_git.return_value = None

        result = detect_project_context("/path/to/my-project")

        assert result is not None
        assert result["project_name"] == "my-project"
        assert result["is_git_repo"] is False
        assert result["project_path"] == os.path.abspath("/path/to/my-project")

    @patch("memorygraph.utils.project_detection._detect_from_git")
    @patch("os.getcwd")
    def test_detect_uses_current_dir_when_no_cwd(self, mock_getcwd, mock_git):
        """Test that it uses os.getcwd() when cwd is None."""
        mock_getcwd.return_value = "/current/working/dir"
        mock_git.return_value = None

        result = detect_project_context(None)

        assert result is not None
        mock_getcwd.assert_called_once()
        assert "working/dir" in result["project_path"] or result["project_name"] == "dir"


class TestDetectFromGit:
    """Test _detect_from_git function."""

    @patch("subprocess.run")
    def test_git_check_returns_none_when_not_git_repo(self, mock_run):
        """Test return None when git check fails (line 76)."""
        # Mock git check to fail
        mock_run.return_value = MagicMock(returncode=1)

        result = _detect_from_git("/some/path")

        assert result is None
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_git_toplevel_returns_none_when_fails(self, mock_run):
        """Test return None when git toplevel fails (line 88)."""
        # First call (git check) succeeds, second call (toplevel) fails
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git rev-parse --is-inside-work-tree succeeds
            MagicMock(returncode=1),  # git rev-parse --show-toplevel fails
        ]

        result = _detect_from_git("/some/path")

        assert result is None
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_git_remote_timeout_handled_gracefully(self, mock_run):
        """Test that git remote timeout is handled (lines 110-111)."""
        # Mock successful git checks but timeout on remote
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git check succeeds
            MagicMock(returncode=0, stdout="  /path/to/repo\n"),  # toplevel succeeds
            subprocess.TimeoutExpired(cmd="git remote", timeout=2),  # remote times out
        ]

        result = _detect_from_git("/path/to/repo")

        # Should still return result without git_remote
        assert result is not None
        assert result["project_name"] == "repo"
        assert "git_remote" not in result

    @patch("subprocess.run")
    def test_git_remote_file_not_found_handled(self, mock_run):
        """Test that git command not found is handled (lines 110-111)."""
        # Mock successful git checks but FileNotFoundError on remote
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git check succeeds
            MagicMock(returncode=0, stdout="  /path/to/repo\n"),  # toplevel succeeds
            FileNotFoundError("git not found"),  # remote fails
        ]

        result = _detect_from_git("/path/to/repo")

        # Should still return result without git_remote
        assert result is not None
        assert result["project_name"] == "repo"
        assert "git_remote" not in result

    @patch("subprocess.run")
    def test_successful_git_detection_with_remote(self, mock_run):
        """Test successful git detection with all info."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git check succeeds
            MagicMock(returncode=0, stdout="  /path/to/my-repo  \n"),  # toplevel
            MagicMock(
                returncode=0, stdout="  https://github.com/user/my-repo.git  \n"
            ),  # remote
        ]

        result = _detect_from_git("/path/to/my-repo")

        assert result is not None
        assert result["project_name"] == "my-repo"
        assert result["project_path"] == "/path/to/my-repo"
        assert result["git_remote"] == "https://github.com/user/my-repo.git"

    @patch("subprocess.run")
    def test_git_detection_handles_general_exception(self, mock_run):
        """Test that general exceptions during git detection are handled."""
        # Mock to raise OSError
        mock_run.side_effect = OSError("Permission denied")

        result = _detect_from_git("/some/path")

        assert result is None


class TestGetProjectFromMemories:
    """Test get_project_from_memories function."""

    def test_get_project_from_memories_returns_none(self):
        """Test that get_project_from_memories returns None (line 133)."""
        mock_db = MagicMock()

        result = get_project_from_memories(mock_db, limit=50)

        # Currently not implemented, should return None
        assert result is None

    def test_get_project_from_memories_with_custom_limit(self):
        """Test get_project_from_memories with custom limit."""
        mock_db = MagicMock()

        result = get_project_from_memories(mock_db, limit=100)

        assert result is None
