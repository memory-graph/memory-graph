"""Tests for project analysis functionality."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from memorygraph.integration.project_analysis import (
    ProjectInfo,
    CodebaseInfo,
    FileChange,
    Pattern,
    detect_project,
    analyze_codebase,
    track_file_changes,
    identify_code_patterns,
)


class TestProjectInfo:
    """Test ProjectInfo model."""

    def test_project_info_creation(self):
        """Test creating a ProjectInfo."""
        project = ProjectInfo(
            name="my-app",
            path="/Users/me/my-app",
            project_type="python",
            git_remote="https://github.com/user/my-app.git",
        )

        assert project.name == "my-app"
        assert project.path == "/Users/me/my-app"
        assert project.project_type == "python"
        assert project.git_remote is not None
        assert project.project_id is not None


class TestCodebaseInfo:
    """Test CodebaseInfo model."""

    def test_codebase_info_creation(self):
        """Test creating a CodebaseInfo."""
        info = CodebaseInfo(
            total_files=150,
            file_types={".py": 80, ".md": 10, ".txt": 60},
            languages=["python"],
            frameworks=["fastapi"],
        )

        assert info.total_files == 150
        assert len(info.file_types) == 3
        assert "python" in info.languages


class TestFileChange:
    """Test FileChange model."""

    def test_file_change_creation(self):
        """Test creating a FileChange."""
        change = FileChange(
            file_path="src/api.py",
            change_type="modified",
            lines_added=15,
            lines_removed=8,
        )

        assert change.file_path == "src/api.py"
        assert change.change_type == "modified"
        assert change.lines_added == 15
        assert change.lines_removed == 8


class TestPattern:
    """Test Pattern model."""

    def test_pattern_creation(self):
        """Test creating a Pattern."""
        pattern = Pattern(
            pattern_type="api_endpoint",
            description="REST API endpoint pattern",
            examples=["@app.get('/users')", "@app.post('/posts')"],
            frequency=25,
            confidence=0.9,
        )

        assert pattern.pattern_type == "api_endpoint"
        assert len(pattern.examples) == 2
        assert pattern.frequency == 25


@pytest.mark.asyncio
class TestDetectProject:
    """Test detect_project function."""

    async def test_detect_python_project(self):
        """Test detecting a Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pyproject.toml
            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text("[tool.poetry]\nname = 'test-project'\n")

            backend = AsyncMock()
            backend.search_nodes = AsyncMock(return_value=[])
            backend.store_node = AsyncMock(return_value="project-123")

            project = await detect_project(backend, tmpdir)

            assert project is not None
            assert project.project_type == "python"
            assert project.path == tmpdir

    async def test_detect_typescript_project(self):
        """Test detecting a TypeScript project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json and tsconfig.json
            package_path = Path(tmpdir) / "package.json"
            package_path.write_text('{"name": "test-app", "dependencies": {}}')

            tsconfig_path = Path(tmpdir) / "tsconfig.json"
            tsconfig_path.write_text('{"compilerOptions": {}}')

            backend = AsyncMock()
            backend.search_nodes = AsyncMock(return_value=[])
            backend.store_node = AsyncMock(return_value="project-123")

            project = await detect_project(backend, tmpdir)

            assert project is not None
            assert project.project_type == "typescript"

    async def test_detect_mixed_project(self):
        """Test detecting a mixed-language project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both Python and TypeScript configs
            (Path(tmpdir) / "pyproject.toml").write_text("[tool.poetry]\n")
            (Path(tmpdir) / "package.json").write_text('{"name": "test"}')

            backend = AsyncMock()
            backend.search_nodes = AsyncMock(return_value=[])
            backend.store_node = AsyncMock(return_value="project-123")

            project = await detect_project(backend, tmpdir)

            assert project is not None
            assert project.project_type == "mixed"
            assert "python" in project.technologies or "typescript" in project.technologies

    async def test_detect_project_with_git(self):
        """Test detecting project with git remote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "pyproject.toml").write_text("[tool.poetry]\n")

            backend = AsyncMock()
            backend.search_nodes = AsyncMock(return_value=[])
            backend.store_node = AsyncMock(return_value="project-123")

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="https://github.com/user/repo.git\n"
                )

                project = await detect_project(backend, tmpdir)

                assert project is not None
                assert project.git_remote == "https://github.com/user/repo.git"
                assert project.name == "repo"

    async def test_detect_project_updates_existing(self):
        """Test that existing project is updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "pyproject.toml").write_text("[tool.poetry]\n")

            backend = AsyncMock()
            backend.search_nodes = AsyncMock(
                return_value=[{"id": "existing-project", "name": "test"}]
            )
            backend.execute_query = AsyncMock()

            project = await detect_project(backend, tmpdir)

            assert project is not None
            assert project.project_id == "existing-project"
            # Should update existing project
            backend.execute_query.assert_called_once()

    async def test_detect_project_nonexistent_dir(self):
        """Test detecting project in nonexistent directory."""
        backend = AsyncMock()

        project = await detect_project(backend, "/nonexistent/path")

        assert project is None

    async def test_detect_react_framework(self):
        """Test detecting React framework."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json with React
            package_path = Path(tmpdir) / "package.json"
            package_path.write_text(
                '{"name": "test-app", "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}'
            )

            backend = AsyncMock()
            backend.search_nodes = AsyncMock(return_value=[])
            backend.store_node = AsyncMock(return_value="project-123")

            project = await detect_project(backend, tmpdir)

            assert project is not None
            assert "react" in project.technologies


@pytest.mark.asyncio
class TestAnalyzeCodebase:
    """Test analyze_codebase function."""

    async def test_analyze_codebase_basic(self):
        """Test basic codebase analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "main.py").write_text("print('hello')")
            (Path(tmpdir) / "test.py").write_text("def test(): pass")
            (Path(tmpdir) / "README.md").write_text("# Project")

            backend = AsyncMock()

            info = await analyze_codebase(backend, tmpdir)

            assert info.total_files == 3
            assert ".py" in info.file_types
            assert info.file_types[".py"] == 2
            assert "python" in info.languages

    async def test_analyze_codebase_ignores_patterns(self):
        """Test that analysis ignores certain directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in ignored directories
            node_modules = Path(tmpdir) / "node_modules"
            node_modules.mkdir()
            (node_modules / "package.js").write_text("module.exports = {}")

            pycache = Path(tmpdir) / "__pycache__"
            pycache.mkdir()
            (pycache / "module.pyc").write_text("")

            # Create normal file
            (Path(tmpdir) / "main.py").write_text("print('hello')")

            backend = AsyncMock()

            info = await analyze_codebase(backend, tmpdir)

            # Should only count main.py
            assert info.total_files == 1
            assert ".py" in info.file_types
            assert info.file_types[".py"] == 1

    async def test_analyze_codebase_multiple_languages(self):
        """Test analyzing codebase with multiple languages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("print('hello')")
            (Path(tmpdir) / "app.ts").write_text("console.log('hello')")
            (Path(tmpdir) / "styles.css").write_text("body { }")
            (Path(tmpdir) / "main.go").write_text('package main\nfunc main() {}')

            backend = AsyncMock()

            info = await analyze_codebase(backend, tmpdir)

            assert info.total_files == 4
            assert "python" in info.languages
            assert "typescript" in info.languages
            assert "go" in info.languages


@pytest.mark.asyncio
class TestTrackFileChanges:
    """Test track_file_changes function."""

    async def test_track_file_changes_no_git(self):
        """Test tracking changes in non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = AsyncMock()

            changes = await track_file_changes(backend, tmpdir, "project-123")

            assert changes == []

    async def test_track_file_changes_with_git(self):
        """Test tracking changes with git."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[{"id": "file-123"}])

        with patch("subprocess.run") as mock_run:
            # Mock git status
            mock_run.return_value = MagicMock(
                returncode=0, stdout="M  src/api.py\nA  src/new.py\nD  old.py\n"
            )

            changes = await track_file_changes(backend, "/fake/path", "project-123")

            assert len(changes) == 3
            assert any(c.change_type == "modified" for c in changes)
            assert any(c.change_type == "added" for c in changes)
            assert any(c.change_type == "deleted" for c in changes)

    async def test_track_file_changes_creates_memories(self):
        """Test that file changes create memory nodes."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[{"id": "file-123"}])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="M  src/api.py\n")

            changes = await track_file_changes(backend, "/fake/path", "project-123")

            # Should create memory for the change
            backend.store_node.assert_called()
            call_args = backend.store_node.call_args[0][1]
            assert call_args["type"] == "file_change"


@pytest.mark.asyncio
class TestIdentifyCodePatterns:
    """Test identify_code_patterns function."""

    async def test_identify_api_endpoints(self):
        """Test identifying API endpoint patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with API endpoints
            api_file = Path(tmpdir) / "api.py"
            api_file.write_text(
                """
from fastapi import FastAPI
app = FastAPI()

@app.get('/users')
def get_users():
    pass

@app.post('/users')
def create_user():
    pass

@app.get('/posts')
def get_posts():
    pass
"""
            )

            backend = AsyncMock()
            backend.store_node = AsyncMock(return_value="pattern-123")
            backend.store_relationship = AsyncMock()

            patterns = await identify_code_patterns(
                backend, "project-123", [str(api_file)]
            )

            # Should find API endpoint pattern
            assert len(patterns) > 0
            api_patterns = [p for p in patterns if p.pattern_type == "api_endpoint"]
            assert len(api_patterns) > 0
            assert api_patterns[0].frequency >= 3

    async def test_identify_class_definitions(self):
        """Test identifying class definition patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = Path(tmpdir) / "models.py"
            code_file.write_text(
                """
class UserModel:
    pass

class PostModel:
    pass

class CommentModel:
    pass
"""
            )

            backend = AsyncMock()
            backend.store_node = AsyncMock(return_value="pattern-123")
            backend.store_relationship = AsyncMock()

            patterns = await identify_code_patterns(
                backend, "project-123", [str(code_file)]
            )

            class_patterns = [p for p in patterns if p.pattern_type == "class_definition"]
            assert len(class_patterns) > 0
            assert class_patterns[0].frequency >= 3

    async def test_identify_async_patterns(self):
        """Test identifying async/await patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = Path(tmpdir) / "async_code.py"
            code_file.write_text(
                """
async def fetch_data():
    data = await db.query()
    return data

async def process():
    result = await fetch_data()
    await save(result)
"""
            )

            backend = AsyncMock()
            backend.store_node = AsyncMock(return_value="pattern-123")
            backend.store_relationship = AsyncMock()

            patterns = await identify_code_patterns(
                backend, "project-123", [str(code_file)]
            )

            async_patterns = [p for p in patterns if p.pattern_type == "async_await"]
            assert len(async_patterns) > 0

    async def test_identify_patterns_creates_memories(self):
        """Test that patterns create memory nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = Path(tmpdir) / "code.py"
            code_file.write_text("def func1(): pass\ndef func2(): pass\ndef func3(): pass")

            backend = AsyncMock()
            backend.store_node = AsyncMock(return_value="pattern-123")
            backend.store_relationship = AsyncMock()

            patterns = await identify_code_patterns(
                backend, "project-123", [str(code_file)]
            )

            if patterns:
                # Should create memory node for pattern
                backend.store_node.assert_called()
                call_args = backend.store_node.call_args[0][1]
                assert call_args["type"] == "code_pattern"
                # Should link to project
                backend.store_relationship.assert_called()

    async def test_identify_patterns_minimum_frequency(self):
        """Test that patterns need minimum frequency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = Path(tmpdir) / "code.py"
            # Only one function - should not create pattern
            code_file.write_text("def func1(): pass")

            backend = AsyncMock()
            backend.store_node = AsyncMock()
            backend.store_relationship = AsyncMock()

            patterns = await identify_code_patterns(
                backend, "project-123", [str(code_file)]
            )

            # Should not create patterns for single occurrences
            assert len(patterns) == 0

    async def test_identify_patterns_nonexistent_file(self):
        """Test identifying patterns in nonexistent file."""
        backend = AsyncMock()

        patterns = await identify_code_patterns(
            backend, "project-123", ["/nonexistent/file.py"]
        )

        assert patterns == []
