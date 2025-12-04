#!/usr/bin/env python3
"""
Build script for creating MemoryGraph .mcpb bundle.

Usage:
    python scripts/build_mcpb.py

This creates a memorygraph-{version}.mcpb file in the dist/ directory.
"""

import json
import os
import shutil
import zipfile
from pathlib import Path


def build_mcpb():
    """Build the .mcpb bundle file."""
    # Get project root
    project_root = Path(__file__).parent.parent

    # Read manifest to get version
    manifest_path = project_root / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    version = manifest["version"]
    name = manifest["name"]

    # Create dist directory
    dist_dir = project_root / "dist"
    dist_dir.mkdir(exist_ok=True)

    # Output file
    output_file = dist_dir / f"{name}-{version}.mcpb"

    # Files to include in the bundle
    include_files = [
        "manifest.json",
        "pyproject.toml",
        "README.md",
        "LICENSE",
    ]

    # Directories to include
    include_dirs = [
        "src/memorygraph",
        "assets",
    ]

    print(f"Building {name} v{version} bundle...")

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add individual files
        for file in include_files:
            file_path = project_root / file
            if file_path.exists():
                zf.write(file_path, file)
                print(f"  Added: {file}")
            else:
                print(f"  Warning: {file} not found, skipping")

        # Add directories
        for dir_name in include_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                for root, dirs, files in os.walk(dir_path):
                    # Skip __pycache__ and other unwanted directories
                    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', '.pytest_cache', 'node_modules')]

                    for file in files:
                        # Skip unwanted files
                        if file.endswith(('.pyc', '.pyo', '.egg-info')):
                            continue

                        file_path = Path(root) / file
                        arcname = file_path.relative_to(project_root)
                        zf.write(file_path, arcname)
                print(f"  Added directory: {dir_name}")
            else:
                print(f"  Warning: {dir_name} not found, skipping")

    # Get file size
    size_kb = output_file.stat().st_size / 1024

    print(f"\n✅ Bundle created: {output_file}")
    print(f"   Size: {size_kb:.1f} KB")
    print(f"\nTo install in Claude Desktop:")
    print(f"   Double-click {output_file.name}")
    print(f"   Or use: mcpb install {output_file}")


if __name__ == "__main__":
    build_mcpb()
