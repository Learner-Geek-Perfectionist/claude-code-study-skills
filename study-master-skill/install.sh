#!/usr/bin/env bash
# Install study-master skill

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_DIR="$CLAUDE_DIR/settings"
SETTINGS_FILE="$SETTINGS_DIR/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Skill name (extracted from SKILL.md frontmatter)
SKILL_NAME=$(grep '^name:' "$SCRIPT_DIR/SKILL.md" | head -1 | sed 's/name: *//')

echo "📦 Installing $SKILL_NAME skill..."
echo ""

# 1. Install skill file
echo "📝 Installing skill file..."
mkdir -p "$SKILLS_DIR"
cp "$SCRIPT_DIR/SKILL.md" "$SKILLS_DIR/${SKILL_NAME}.md"
echo "✅ Installed: $SKILLS_DIR/${SKILL_NAME}.md"
echo ""

# 2. Install hooks (copy all files directly)
if [ -d "$SCRIPT_DIR/hooks" ]; then
    echo "🔧 Installing hooks..."
    mkdir -p "$HOOKS_DIR"

    for file in "$SCRIPT_DIR/hooks"/*; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        cp "$file" "$HOOKS_DIR/$filename"
        chmod +x "$HOOKS_DIR/$filename"
        echo "✅ Installed: $filename"
    done
    echo ""
fi

# 3. Register hooks in settings.json
if [ -f "$HOOKS_DIR/check-study_master.sh" ]; then
    echo "📝 Registering hooks in settings.json..."
    mkdir -p "$SETTINGS_DIR"

    # Initialize settings.json if not exists
    [ ! -f "$SETTINGS_FILE" ] && echo '{}' > "$SETTINGS_FILE"

    # Use Python to safely merge hook configuration
    python3 << 'PYTHON_SCRIPT'
import json
import sys
import os

settings_file = os.path.expanduser("~/.claude/settings/settings.json")
hooks_dir = os.path.expanduser("~/.claude/hooks")

# Read existing settings
with open(settings_file, 'r') as f:
    settings = json.load(f)

# Ensure hooks array exists
if 'hooks' not in settings:
    settings['hooks'] = []

# Hook configuration
hook_config = {
    "name": "study-master-validator",
    "event": "PostToolUse",
    "tool": "Write",
    "command": f"{hooks_dir}/check-study_master.sh"
}

# Check if hook already exists
existing = next((h for h in settings['hooks'] if h.get('name') == 'study-master-validator'), None)

if existing:
    # Update existing hook
    existing.update(hook_config)
    print("✅ Updated existing hook configuration")
else:
    # Add new hook
    settings['hooks'].append(hook_config)
    print("✅ Added new hook configuration")

# Write back
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
PYTHON_SCRIPT

    echo ""
fi

# 4. Success message
echo "🎉 Installation complete!"
echo ""
echo "Installed components:"
echo "  • Skill: $SKILLS_DIR/${SKILL_NAME}.md"
[ -d "$SCRIPT_DIR/hooks" ] && echo "  • Hooks: $HOOKS_DIR/${SKILL_NAME}-*"
echo ""
echo "📖 Recommended project structure:"
echo "  project-root/"
echo "  ├── src/          # Source code"
echo "  ├── docs/         # Documentation"
echo "  └── study/        # Generated study docs (auto-created)"
echo ""
echo "Usage: /${SKILL_NAME} <topic>"

