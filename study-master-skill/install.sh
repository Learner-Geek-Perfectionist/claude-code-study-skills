#!/usr/bin/env bash
# Install study-master skill

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"
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

# 3. Success message
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

