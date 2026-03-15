#!/usr/bin/env bash
# Uninstall study-master profiling (restore original mode)

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_DIR="$CLAUDE_DIR/settings"
SETTINGS_FILE="$SETTINGS_DIR/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SKILL_NAME="study-master"
TARGET_DIR="$SKILLS_DIR/$SKILL_NAME"

echo "🧹 Removing study-master profiling mode..."
echo ""

# 1. Restore original SKILL.md
echo "📦 Restoring original SKILL.md..."
if [ -f "$TARGET_DIR/SKILL.md.bak" ]; then
    mv "$TARGET_DIR/SKILL.md.bak" "$TARGET_DIR/SKILL.md"
    echo "✅ Restored: SKILL.md from backup"
else
    echo "⚠️  No backup found at $TARGET_DIR/SKILL.md.bak"
    echo "   SKILL.md left unchanged (may need manual restore via install.sh)"
fi
echo ""

# 2. Remove profiling files from hooks dir
echo "🔧 Removing profiling hooks..."
rm -f "$HOOKS_DIR/profiling_hook.sh"
echo "✅ Removed: profiling_hook.sh"
rm -f "$HOOKS_DIR/generate_profiling_report.py"
echo "✅ Removed: generate_profiling_report.py"
echo ""

# 3. Unregister hook from settings.json
echo "📝 Unregistering profiling hook from settings.json..."
if [ -f "$SETTINGS_FILE" ]; then
    python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings/settings.json")

# Read existing settings
with open(settings_file, 'r') as f:
    settings = json.load(f)

# Remove profiling hook entry
if 'hooks' in settings:
    original_count = len(settings['hooks'])
    settings['hooks'] = [h for h in settings['hooks'] if h.get('name') != 'study-master-profiling']
    removed = original_count - len(settings['hooks'])
    if removed > 0:
        print(f"✅ Removed hook: study-master-profiling ({removed} entry)")
    else:
        print("⚠️  Hook study-master-profiling not found in settings")

    # Clean up empty hooks array
    if len(settings['hooks']) == 0:
        del settings['hooks']
else:
    print("⚠️  No hooks array in settings.json")

# Write back
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
PYTHON_SCRIPT
else
    echo "⚠️  No settings.json found, skipping hook removal"
fi
echo ""

# 4. Success message
echo "🎉 Profiling mode removed!"
echo ""
echo "Restored components:"
echo "  * SKILL.md restored to original version"
echo "  * Profiling hook and report generator removed"
echo "  * Hook unregistered from settings.json"
echo ""
echo "📊 Profiling logs are preserved:"
echo "  * Tool log: /tmp/study-master-tool.log"
echo "  * Phase log: study/<topic>/.profiling.log (in your project)"
echo "  * Report:    study/<topic>/.profiling-report.md (in your project)"
echo ""
echo "To clean up the tool log manually:"
echo "  rm -f /tmp/study-master-tool.log"
