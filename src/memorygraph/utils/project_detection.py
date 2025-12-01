"""
Project context detection utilities.

Auto-detects project name and context from environment.
"""

import os
import subprocess
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def detect_project_context(cwd: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Detect project context from current working directory or git repository.

    Args:
        cwd: Current working directory (defaults to os.getcwd())

    Returns:
        Dictionary with project information:
        - project_name: Name of the project
        - project_path: Absolute path to project root
        - is_git_repo: Whether this is a git repository
        - git_remote: Git remote URL (if available)

        Returns None if project cannot be detected.
    """
    if cwd is None:
        cwd = os.getcwd()

    cwd = os.path.abspath(cwd)

    result = {
        "project_path": cwd,
        "is_git_repo": False
    }

    # Try to detect from git repository
    git_info = _detect_from_git(cwd)
    if git_info:
        result.update(git_info)
        result["is_git_repo"] = True
        return result

    # Fallback: use directory name
    project_name = os.path.basename(cwd)
    result["project_name"] = project_name

    return result


def _detect_from_git(cwd: str) -> Optional[Dict[str, Any]]:
    """
    Detect project information from git repository.

    Args:
        cwd: Current working directory

    Returns:
        Dictionary with git-based project info, or None if not a git repo
    """
    try:
        # Check if this is a git repository
        git_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2
        )

        if git_check.returncode != 0:
            return None

        # Get repository root
        repo_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2
        )

        if repo_root.returncode != 0:
            return None

        project_path = repo_root.stdout.strip()
        project_name = os.path.basename(project_path)

        result = {
            "project_name": project_name,
            "project_path": project_path
        }

        # Try to get git remote (optional)
        try:
            remote = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2
            )

            if remote.returncode == 0:
                result["git_remote"] = remote.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Git remote is optional

        return result

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug(f"Git detection failed: {e}")
        return None


def get_project_from_memories(db, limit: int = 50) -> Optional[str]:
    """
    Infer current project from frequently mentioned project paths in recent memories.

    Args:
        db: Database instance
        limit: Number of recent memories to analyze

    Returns:
        Most common project path, or None if cannot determine
    """
    # This would require database access, which we'll implement later
    # For now, return None
    return None
