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

# 1. Install skill directory (includes SKILL.md and supporting files)
echo "📝 Installing skill directory..."
mkdir -p "$SKILLS_DIR"
TARGET_DIR="$SKILLS_DIR/$SKILL_NAME"

# Remove old installation if exists
[ -d "$TARGET_DIR" ] && rm -rf "$TARGET_DIR"
[ -f "$SKILLS_DIR/${SKILL_NAME}.md" ] && rm "$SKILLS_DIR/${SKILL_NAME}.md"

# Copy entire skill directory
mkdir -p "$TARGET_DIR"
cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/"
cp "$SCRIPT_DIR/format-rules.md" "$TARGET_DIR/"
[ -f "$SCRIPT_DIR/README.md" ] && cp "$SCRIPT_DIR/README.md" "$TARGET_DIR/"

echo "✅ Installed: $TARGET_DIR/"
echo "   • SKILL.md"
echo "   • format-rules.md"
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

# Hook configurations (validate on both Write and Edit)
hook_configs = [
    {
        "name": "study-master-validator",
        "event": "PostToolUse",
        "tool": "Write",
        "command": f"{hooks_dir}/check-study_master.sh"
    },
    {
        "name": "study-master-validator-edit",
        "event": "PostToolUse",
        "tool": "Edit",
        "command": f"{hooks_dir}/check-study_master.sh"
    }
]

for hook_config in hook_configs:
    existing = next((h for h in settings['hooks'] if h.get('name') == hook_config['name']), None)
    if existing:
        existing.update(hook_config)
        print(f"✅ Updated hook: {hook_config['name']}")
    else:
        settings['hooks'].append(hook_config)
        print(f"✅ Added hook: {hook_config['name']}")

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
echo "  • Skill directory: $TARGET_DIR/"
echo "    - SKILL.md"
echo "    - format-rules.md"
[ -d "$SCRIPT_DIR/hooks" ] && echo "  • Hooks: $HOOKS_DIR/"
echo ""
echo "📖 Required project structure:"
echo "  project-root/"
echo "  ├── src/          # Source code (required)"
echo "  ├── docs/         # Documentation (required)"
echo "  └── study/        # Generated study docs (auto-created)"
echo ""
echo "Usage: /${SKILL_NAME} <topic>"

