#!/usr/bin/env bash
# Install study-master skill

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
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
[ -f "$SCRIPT_DIR/README.md" ] && cp "$SCRIPT_DIR/README.md" "$TARGET_DIR/"

echo "✅ Installed: $TARGET_DIR/"
echo "   • SKILL.md"
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

# 3. Register hooks in ~/.claude/settings.json
#    Claude Code hooks 格式: hooks.PostToolUse = [{matcher, hooks: [{type, command, timeout}]}]
if [ -f "$HOOKS_DIR/check-study_master.sh" ]; then
    echo "📝 Registering hooks in settings.json..."

    # Initialize settings.json if not exists
    [ ! -f "$SETTINGS_FILE" ] && echo '{}' > "$SETTINGS_FILE"

    # Use Python to safely merge hook configuration
    python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")
hook_cmd = 'bash "$HOME/.claude/hooks/check-study_master.sh"'

with open(settings_file, 'r') as f:
    settings = json.load(f)

# Ensure hooks.PostToolUse structure exists
hooks = settings.setdefault('hooks', {})
post_tool_use = hooks.setdefault('PostToolUse', [])

hook_entry = {"type": "command", "command": hook_cmd, "timeout": 10}

for tool in ["Write", "Edit"]:
    # Find existing matcher for this tool
    matcher = next((m for m in post_tool_use if m.get('matcher') == tool), None)

    if matcher is None:
        # Create new matcher
        post_tool_use.append({"matcher": tool, "hooks": [hook_entry]})
        print(f"✅ Added hook: PostToolUse/{tool}")
    elif not any(h.get('command') == hook_cmd for h in matcher.get('hooks', [])):
        # Append hook to existing matcher
        matcher.setdefault('hooks', []).append(hook_entry)
        print(f"✅ Added hook: PostToolUse/{tool}")
    else:
        print(f"⏭️  Hook already exists: PostToolUse/{tool}")

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
PYTHON_SCRIPT

    echo ""
fi

# 4. Success message
echo "🎉 Installation complete!"
echo ""
echo "Installed components:"
echo "  • Skill directory: $TARGET_DIR/"
echo "    - SKILL.md"
[ -d "$SCRIPT_DIR/hooks" ] && echo "  • Hooks: $HOOKS_DIR/"
echo ""
echo "📖 Required project structure:"
echo "  project-root/"
echo "  ├── source/       # Source code (required)"
echo "  ├── specs/        # Documentation (required)"
echo "  └── study/        # Generated study docs (auto-created)"
echo ""
echo "Usage: /${SKILL_NAME} <topic>"

