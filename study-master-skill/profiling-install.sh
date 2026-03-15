#!/usr/bin/env bash
# Install study-master profiling (diagnostic mode)

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_DIR="$CLAUDE_DIR/settings"
SETTINGS_FILE="$SETTINGS_DIR/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SKILL_NAME="study-master"
TARGET_DIR="$SKILLS_DIR/$SKILL_NAME"

echo "🔬 Installing study-master profiling mode..."
echo ""

# 1. Backup original SKILL.md
echo "📦 Backing up original SKILL.md..."
if [ ! -f "$TARGET_DIR/SKILL.md" ]; then
    echo "❌ Error: $TARGET_DIR/SKILL.md not found."
    echo "   Please run install.sh first to install the base skill."
    exit 1
fi

if [ -f "$TARGET_DIR/SKILL.md.bak" ]; then
    echo "⚠️  Backup already exists, skipping (previous profiling install?)"
else
    cp "$TARGET_DIR/SKILL.md" "$TARGET_DIR/SKILL.md.bak"
    echo "✅ Backed up: SKILL.md -> SKILL.md.bak"
fi
echo ""

# 2. Replace with profiling version
echo "📝 Installing profiling SKILL.md..."
if [ ! -f "$SCRIPT_DIR/SKILL-profiling.md" ]; then
    echo "❌ Error: $SCRIPT_DIR/SKILL-profiling.md not found."
    exit 1
fi
cp "$SCRIPT_DIR/SKILL-profiling.md" "$TARGET_DIR/SKILL.md"
echo "✅ Replaced SKILL.md with profiling version"
echo ""

# 3. Install hook and report generator
echo "🔧 Installing profiling hook and report generator..."
mkdir -p "$HOOKS_DIR"

cp "$SCRIPT_DIR/hooks/profiling_hook.sh" "$HOOKS_DIR/profiling_hook.sh"
chmod +x "$HOOKS_DIR/profiling_hook.sh"
echo "✅ Installed: profiling_hook.sh"

cp "$SCRIPT_DIR/hooks/generate_profiling_report.py" "$HOOKS_DIR/generate_profiling_report.py"
echo "✅ Installed: generate_profiling_report.py"
echo ""

# 4. Register profiling hook in settings.json
echo "📝 Registering profiling hook in settings.json..."
mkdir -p "$SETTINGS_DIR"

# Initialize settings.json if not exists
[ ! -f "$SETTINGS_FILE" ] && echo '{}' > "$SETTINGS_FILE"

# Use Python to safely merge hook configuration
python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings/settings.json")
hooks_dir = os.path.expanduser("~/.claude/hooks")

# Read existing settings
with open(settings_file, 'r') as f:
    settings = json.load(f)

# Ensure hooks array exists
if 'hooks' not in settings:
    settings['hooks'] = []

# Profiling hook configuration (no tool filter - fires on ALL tools)
hook_config = {
    "name": "study-master-profiling",
    "event": "PostToolUse",
    "command": f"{hooks_dir}/profiling_hook.sh"
}

existing = next((h for h in settings['hooks'] if h.get('name') == hook_config['name']), None)
if existing:
    existing.update(hook_config)
    print("✅ Updated hook: study-master-profiling")
else:
    settings['hooks'].append(hook_config)
    print("✅ Added hook: study-master-profiling")

# Write back
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
PYTHON_SCRIPT

echo ""

# 5. Clear old tool log
echo "🧹 Clearing old profiling log..."
rm -f /tmp/study-master-tool.log
echo "✅ Cleared: /tmp/study-master-tool.log"
echo ""

# 6. Success message
echo "🎉 Profiling mode installed!"
echo ""
echo "Installed components:"
echo "  * SKILL.md replaced with profiling version (original backed up)"
echo "  * Hook: $HOOKS_DIR/profiling_hook.sh"
echo "  * Report generator: $HOOKS_DIR/generate_profiling_report.py"
echo "  * Hook registered: study-master-profiling (PostToolUse, all tools)"
echo ""
echo "📖 How to use:"
echo "  1. Start a new Claude Code session"
echo "  2. Run /study-master on any topic as usual"
echo "  3. Tool calls are logged to /tmp/study-master-tool.log"
echo "  4. At the end, the profiling SKILL instructs Claude to generate a report"
echo ""
echo "📊 To generate a report manually:"
echo "  python3 $HOOKS_DIR/generate_profiling_report.py"
echo ""
echo "🧹 To uninstall profiling mode:"
echo "  $SCRIPT_DIR/profiling-cleanup.sh"
