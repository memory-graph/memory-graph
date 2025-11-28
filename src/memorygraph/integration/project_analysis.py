"""
Project-Aware Memory for Claude Code Integration.

Provides project detection, codebase analysis, and file change tracking:
- Project detection from directory structure
- Codebase analysis (languages, frameworks, structure)
- File change tracking with git integration
- Code pattern identification
"""

import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ..backends.base import GraphBackend


class ProjectInfo(BaseModel):
    """Project information."""

    project_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Project name")
    path: str = Field(..., description="Project directory path")
    project_type: str = Field(..., description="Project type (e.g., 'python', 'typescript', 'mixed')")
    git_remote: Optional[str] = Field(None, description="Git remote URL if available")
    description: Optional[str] = Field(None, description="Project description")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")


class CodebaseInfo(BaseModel):
    """Codebase analysis results."""

    total_files: int = Field(..., description="Total number of files")
    file_types: dict[str, int] = Field(
        default_factory=dict, description="File count by extension"
    )
    languages: list[str] = Field(default_factory=list, description="Programming languages detected")
    frameworks: list[str] = Field(default_factory=list, description="Frameworks detected")
    structure: dict[str, Any] = Field(default_factory=dict, description="Directory structure")
    config_files: list[str] = Field(default_factory=list, description="Configuration files found")


class FileChange(BaseModel):
    """File change information."""

    file_path: str = Field(..., description="Path to changed file")
    change_type: str = Field(..., description="Type of change (added, modified, deleted)")
    timestamp: datetime = Field(default_factory=datetime.now)
    lines_added: int = Field(default=0, description="Lines added")
    lines_removed: int = Field(default=0, description="Lines removed")


class Pattern(BaseModel):
    """Code pattern identified."""

    pattern_id: str = Field(default_factory=lambda: str(uuid4()))
    pattern_type: str = Field(..., description="Type of pattern")
    description: str = Field(..., description="Pattern description")
    examples: list[str] = Field(default_factory=list, description="Example occurrences")
    frequency: int = Field(default=1, description="Frequency of pattern")
    confidence: float = Field(default=0.5, description="Confidence in pattern")


# File patterns to ignore
IGNORE_PATTERNS = [
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    ".DS_Store",
    "thumbs.db",
]

# Config file patterns for project type detection
PROJECT_CONFIGS = {
    "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock"],
    "typescript": ["package.json", "tsconfig.json", "yarn.lock", "pnpm-lock.yaml"],
    "javascript": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
    "rust": ["Cargo.toml", "Cargo.lock"],
    "go": ["go.mod", "go.sum"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "ruby": ["Gemfile", "Gemfile.lock"],
    "php": ["composer.json", "composer.lock"],
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "react": ["react", "@types/react"],
    "vue": ["vue", "@vue/"],
    "angular": ["@angular/"],
    "next": ["next", "next.config"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "express": ["express"],
    "nestjs": ["@nestjs/"],
    "spring": ["spring-boot", "springframework"],
}


async def detect_project(backend: GraphBackend, directory: str) -> Optional[ProjectInfo]:
    """
    Detect project from directory and return project information.

    Args:
        backend: Database backend
        directory: Directory path to analyze

    Returns:
        ProjectInfo if project detected, None otherwise

    Example:
        >>> project = await detect_project(backend, "/Users/me/my-app")
        >>> print(project.name, project.project_type)
    """
    directory = os.path.abspath(os.path.expanduser(directory))

    if not os.path.isdir(directory):
        return None

    # Extract project name from directory
    project_name = os.path.basename(directory)

    # Check for git remote
    git_remote = None
    try:
        result = subprocess.run(
            ["git", "-C", directory, "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_remote = result.stdout.strip()
            # Extract repo name from git URL if available
            if git_remote:
                match = re.search(r"[/:]([^/]+?)(?:\.git)?$", git_remote)
                if match:
                    project_name = match.group(1)
    except Exception:
        pass

    # Detect project type from config files
    project_type = "unknown"
    config_files = []
    technologies = []

    for lang, configs in PROJECT_CONFIGS.items():
        for config in configs:
            config_path = os.path.join(directory, config)
            if os.path.isfile(config_path):
                config_files.append(config)
                if project_type == "unknown":
                    project_type = lang

                # Parse config file for more details
                if config == "package.json":
                    try:
                        with open(config_path) as f:
                            package_data = json.load(f)
                            dependencies = {
                                **package_data.get("dependencies", {}),
                                **package_data.get("devDependencies", {}),
                            }

                            # Detect frameworks
                            for framework, patterns in FRAMEWORK_PATTERNS.items():
                                if any(p in dep for dep in dependencies for p in patterns):
                                    technologies.append(framework)
                    except Exception:
                        pass

                elif config == "pyproject.toml":
                    try:
                        with open(config_path) as f:
                            content = f.read()
                            # Detect Python frameworks
                            for framework, patterns in FRAMEWORK_PATTERNS.items():
                                if any(p in content for p in patterns):
                                    technologies.append(framework)
                    except Exception:
                        pass

    # If multiple config types found, mark as mixed (but handle TypeScript special case)
    detected_types = [
        lang for lang, configs in PROJECT_CONFIGS.items() if any(c in config_files for c in configs)
    ]

    # Special case: if tsconfig.json is present, it's TypeScript (not mixed with JavaScript)
    # because TypeScript projects also use package.json
    if "tsconfig.json" in config_files:
        project_type = "typescript"
        detected_types = ["typescript"]
    elif len(detected_types) > 1:
        project_type = "mixed"
        technologies.extend(detected_types)

    project = ProjectInfo(
        name=project_name,
        path=directory,
        project_type=project_type,
        git_remote=git_remote,
        technologies=list(set(technologies)),  # Remove duplicates
    )

    # Check if project already exists in database
    existing = await backend.search_nodes(
        "Entity", {"type": "project", "name": project_name, "path": directory}
    )

    if existing:
        project.project_id = existing[0]["id"]
        # Update existing project
        await backend.execute_query(
            """
            MATCH (p:Entity {id: $project_id})
            SET p.git_remote = $git_remote,
                p.project_type = $project_type,
                p.technologies = $technologies,
                p.updated_at = datetime()
            """,
            {
                "project_id": project.project_id,
                "git_remote": git_remote,
                "project_type": project_type,
                "technologies": technologies,
            },
        )
    else:
        # Create new project entity
        properties = {
            "id": project.project_id,
            "type": "project",
            "name": project_name,
            "path": directory,
            "project_type": project_type,
            "git_remote": git_remote,
            "technologies": technologies,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        await backend.store_node("Entity", properties)

    return project


async def analyze_codebase(backend: GraphBackend, directory: str) -> CodebaseInfo:
    """
    Analyze codebase structure and characteristics.

    Args:
        backend: Database backend
        directory: Directory path to analyze

    Returns:
        CodebaseInfo with analysis results

    Example:
        >>> info = await analyze_codebase(backend, "/Users/me/my-app")
        >>> print(f"Total files: {info.total_files}")
        >>> print(f"Languages: {', '.join(info.languages)}")
    """
    directory = os.path.abspath(os.path.expanduser(directory))

    file_types: Counter = Counter()
    config_files = []
    total_files = 0

    # Walk directory tree
    for root, dirs, files in os.walk(directory):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS and not d.startswith(".")]

        for file in files:
            # Skip ignored patterns
            if any(file.endswith(pattern.replace("*", "")) for pattern in IGNORE_PATTERNS):
                continue

            total_files += 1
            ext = os.path.splitext(file)[1]
            if ext:
                file_types[ext] += 1

            # Check if it's a config file
            for configs in PROJECT_CONFIGS.values():
                if file in configs:
                    config_files.append(os.path.join(root, file))

    # Map extensions to languages
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".swift": "swift",
        ".kt": "kotlin",
    }

    languages = list({ext_to_lang.get(ext, "other") for ext in file_types if ext in ext_to_lang})

    # Detect frameworks from file analysis
    frameworks = []

    codebase_info = CodebaseInfo(
        total_files=total_files,
        file_types=dict(file_types),
        languages=languages,
        frameworks=frameworks,
        config_files=config_files,
    )

    return codebase_info


async def track_file_changes(
    backend: GraphBackend, repo_path: str, project_id: str
) -> list[FileChange]:
    """
    Track file changes using git diff.

    Args:
        backend: Database backend
        repo_path: Path to git repository
        project_id: Project ID

    Returns:
        List of FileChange objects

    Example:
        >>> changes = await track_file_changes(
        ...     backend,
        ...     "/Users/me/my-app",
        ...     "project-123"
        ... )
        >>> for change in changes:
        ...     print(f"{change.change_type}: {change.file_path}")
    """
    repo_path = os.path.abspath(os.path.expanduser(repo_path))

    changes = []

    try:
        # Get git status for changed files
        result = subprocess.run(
            ["git", "-C", repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return changes

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            status = line[:2].strip()
            file_path = line[3:].strip()

            # Map git status to change type
            change_type = "modified"
            if status in ["A", "??"]:
                change_type = "added"
            elif status == "D":
                change_type = "deleted"
            elif status in ["M", "MM"]:
                change_type = "modified"

            # Get diff stats for modified files
            lines_added = 0
            lines_removed = 0

            if change_type == "modified" and os.path.isfile(os.path.join(repo_path, file_path)):
                try:
                    diff_result = subprocess.run(
                        ["git", "-C", repo_path, "diff", "--numstat", "HEAD", file_path],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if diff_result.returncode == 0 and diff_result.stdout:
                        parts = diff_result.stdout.strip().split("\t")
                        if len(parts) >= 2:
                            lines_added = int(parts[0]) if parts[0].isdigit() else 0
                            lines_removed = int(parts[1]) if parts[1].isdigit() else 0
                except Exception:
                    pass

            file_change = FileChange(
                file_path=file_path,
                change_type=change_type,
                lines_added=lines_added,
                lines_removed=lines_removed,
            )
            changes.append(file_change)

            # Store file change as observation
            properties = {
                "id": str(uuid4()),
                "type": "file_change",
                "title": f"File {change_type}: {file_path}",
                "content": f"File: {file_path}\nChange: {change_type}\n"
                f"Lines added: {lines_added}\nLines removed: {lines_removed}",
                "context": {
                    "file_path": file_path,
                    "change_type": change_type,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "project_id": project_id,
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            memory_id = await backend.store_node("Memory", properties)

            # Link to project
            await backend.store_relationship(
                memory_id,
                project_id,
                "PART_OF",
                {"created_at": datetime.now(), "strength": 1.0},
            )

            # Create or get file entity and link
            file_entity = await backend.execute_query(
                """
                MERGE (f:Entity {name: $file_path, type: 'file'})
                ON CREATE SET f.id = $file_id, f.created_at = datetime()
                RETURN f.id as id
                """,
                {"file_path": file_path, "file_id": str(uuid4())},
            )

            if file_entity:
                file_id = file_entity[0]["id"]
                await backend.store_relationship(
                    memory_id,
                    file_id,
                    "MODIFIES" if change_type == "modified" else "CREATES",
                    {"created_at": datetime.now(), "strength": 1.0},
                )

    except Exception as e:
        # Git not available or not a git repo - return empty list
        pass

    return changes


async def identify_code_patterns(
    backend: GraphBackend, project_id: str, files: list[str]
) -> list[Pattern]:
    """
    Identify code patterns in files.

    Args:
        backend: Database backend
        project_id: Project ID
        files: List of file paths to analyze

    Returns:
        List of identified patterns

    Example:
        >>> patterns = await identify_code_patterns(
        ...     backend,
        ...     "project-123",
        ...     ["src/api/users.py", "src/api/posts.py"]
        ... )
    """
    patterns: list[Pattern] = []

    # Common code patterns to identify
    pattern_regexes = {
        "api_endpoint": r"@(app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)",
        "class_definition": r"class\s+(\w+)(?:\(.*?\))?:",
        "function_definition": r"(?:async\s+)?def\s+(\w+)\s*\(",
        "import_statement": r"(?:from\s+[\w.]+\s+)?import\s+([\w, ]+)",
        "error_handling": r"try:|except\s+(\w+(?:Error|Exception)):",
        "async_await": r"\basync\s+def\b|\bawait\b",
        "type_annotation": r":\s*([A-Z][\w\[\], ]+)(?:\s*=)?",
    }

    pattern_counts: Counter = Counter()
    pattern_examples: dict[str, list[str]] = {}

    for file_path in files:
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

                for pattern_type, regex in pattern_regexes.items():
                    matches = re.findall(regex, content)
                    if matches:
                        pattern_counts[pattern_type] += len(matches)
                        if pattern_type not in pattern_examples:
                            pattern_examples[pattern_type] = []
                        # Store first few examples
                        pattern_examples[pattern_type].extend(
                            [str(m)[:100] for m in matches[:3]]
                        )
        except Exception:
            continue

    # Create pattern objects for significant patterns
    for pattern_type, count in pattern_counts.items():
        if count >= 2:  # Only patterns that occur at least twice
            pattern = Pattern(
                pattern_type=pattern_type,
                description=f"Code pattern: {pattern_type}",
                examples=pattern_examples.get(pattern_type, [])[:5],
                frequency=count,
                confidence=min(0.5 + (count * 0.05), 0.95),
            )

            # Store pattern as memory
            properties = {
                "id": pattern.pattern_id,
                "type": "code_pattern",
                "title": f"Pattern: {pattern_type}",
                "content": f"Pattern Type: {pattern_type}\n"
                f"Frequency: {count}\n\n"
                f"Examples:\n" + "\n".join(f"- {ex}" for ex in pattern.examples),
                "context": {
                    "pattern_type": pattern_type,
                    "frequency": count,
                    "confidence": pattern.confidence,
                    "project_id": project_id,
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            memory_id = await backend.store_node("Memory", properties)

            # Link to project
            await backend.store_relationship(
                memory_id,
                project_id,
                "FOUND_IN",
                {"created_at": datetime.now(), "strength": pattern.confidence},
            )

            patterns.append(pattern)

    return patterns
