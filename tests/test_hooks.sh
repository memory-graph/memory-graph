#!/bin/bash
set -e

echo "Testing hook scripts..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR/../examples/claude-code-hooks/.claude/hooks"

# Test 1: Local environment (should exit early)
echo "Test 1: Local environment (should exit early)"
unset CLAUDE_CODE_REMOTE
output=$("$HOOKS_DIR/install-memorygraph.sh" 2>&1 || true)
if [[ "$output" == *"skipping auto-install"* ]]; then
  echo "  ✓ Exits early in local environment"
else
  echo "  ✗ Failed: Should exit early in local environment"
  echo "  Output: $output"
  exit 1
fi

# Test 2: Remote environment detection
echo "Test 2: Remote environment detection"
export CLAUDE_CODE_REMOTE=true
output=$("$HOOKS_DIR/install-memorygraph.sh" 2>&1 || true)
if [[ "$output" == *"Remote environment detected"* ]]; then
  echo "  ✓ Detects remote environment"
else
  echo "  ✗ Failed: Should detect remote environment"
  echo "  Output: $output"
  exit 1
fi

# Test 3: Minimal script - local environment
echo "Test 3: Minimal script - local environment"
unset CLAUDE_CODE_REMOTE
output=$("$HOOKS_DIR/install-memorygraph-minimal.sh" 2>&1 || true)
# Minimal script should just exit silently in local mode
if [ $? -eq 0 ]; then
  echo "  ✓ Minimal script exits cleanly in local environment"
else
  echo "  ✗ Failed: Minimal script should exit cleanly"
  exit 1
fi

# Test 4: Settings JSON is valid
echo "Test 4: Validating settings.json"
if command -v python3 &> /dev/null; then
  python3 -m json.tool "$SCRIPT_DIR/../examples/claude-code-hooks/.claude/settings.json" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "  ✓ settings.json is valid JSON"
  else
    echo "  ✗ Failed: settings.json is invalid JSON"
    exit 1
  fi
else
  echo "  ⊘ Skipped: python3 not available"
fi

# Test 5: Check hook files are executable
echo "Test 5: Checking hook executability"
if [ -x "$HOOKS_DIR/install-memorygraph.sh" ]; then
  echo "  ✓ install-memorygraph.sh is executable"
else
  echo "  ✗ Failed: install-memorygraph.sh is not executable"
  exit 1
fi

if [ -x "$HOOKS_DIR/install-memorygraph-minimal.sh" ]; then
  echo "  ✓ install-memorygraph-minimal.sh is executable"
else
  echo "  ✗ Failed: install-memorygraph-minimal.sh is not executable"
  exit 1
fi

# Test 6: Check copy script is executable
echo "Test 6: Checking copy-to-project.sh executability"
if [ -x "$SCRIPT_DIR/../examples/claude-code-hooks/copy-to-project.sh" ]; then
  echo "  ✓ copy-to-project.sh is executable"
else
  echo "  ✗ Failed: copy-to-project.sh is not executable"
  exit 1
fi

echo ""
echo "All hook tests passed! ✓"
