#!/bin/bash
set -e

TARGET_DIR="${1:-.}"

if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' does not exist"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Copying MemoryGraph hooks to $TARGET_DIR..."

# Create .claude directory if needed
mkdir -p "$TARGET_DIR/.claude/hooks"

# Copy files
cp "$SCRIPT_DIR/.claude/settings.json" "$TARGET_DIR/.claude/"
cp "$SCRIPT_DIR/.claude/hooks/install-memorygraph.sh" "$TARGET_DIR/.claude/hooks/"

# Make hook executable
chmod +x "$TARGET_DIR/.claude/hooks/install-memorygraph.sh"

echo "Done! MemoryGraph hooks installed."
echo ""
echo "Next steps:"
echo "  1. Commit .claude/ to your repository"
echo "  2. Open project in Claude Code Web"
echo "  3. MemoryGraph will auto-install on session start"
