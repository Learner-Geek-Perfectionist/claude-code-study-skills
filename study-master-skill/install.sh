#!/usr/bin/env bash
# Install study-master skill for both Claude Code and Codex.

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
CLAUDE_SKILLS_DIR="$CLAUDE_DIR/skills"
CLAUDE_HOOKS_DIR="$CLAUDE_DIR/hooks"
CLAUDE_SETTINGS_FILE="$CLAUDE_DIR/settings.json"

CODEX_DIR="$HOME/.codex"
CODEX_SKILLS_DIR="$HOME/.agents/skills"
CODEX_HOOKS_FILE="$CODEX_DIR/hooks.json"
CODEX_CONFIG_FILE="$CODEX_DIR/config.toml"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Skill name (extracted from SKILL.md frontmatter)
SKILL_NAME=$(grep '^name:' "$SCRIPT_DIR/SKILL.md" | head -1 | sed 's/name: *//')
CLAUDE_TARGET_DIR="$CLAUDE_SKILLS_DIR/$SKILL_NAME"
CODEX_TARGET_DIR="$CODEX_SKILLS_DIR/$SKILL_NAME"
LEGACY_SKILL_NAME="study_master"

echo "📦 Installing $SKILL_NAME skill..."
echo ""

remove_path_if_exists() {
    local path="$1"
    [ ! -e "$path" ] && return 0
    rm -rf "$path"
    echo "🧹 Removed legacy path: $path"
}

copy_optional_files() {
    local target_dir="$1"
    cp "$SCRIPT_DIR/SKILL.md" "$target_dir/"
    if [ -f "$SCRIPT_DIR/README.md" ]; then
        cp "$SCRIPT_DIR/README.md" "$target_dir/"
    fi
}

cleanup_legacy_skill_installs() {
    echo "🧹 Cleaning legacy skill installs..."
    mkdir -p "$CLAUDE_SKILLS_DIR" "$CODEX_SKILLS_DIR"

    remove_path_if_exists "$CLAUDE_SKILLS_DIR/$LEGACY_SKILL_NAME"
    remove_path_if_exists "$CLAUDE_SKILLS_DIR/${LEGACY_SKILL_NAME}.md"
    remove_path_if_exists "$CLAUDE_SKILLS_DIR/${SKILL_NAME}.md"
    remove_path_if_exists "$CODEX_SKILLS_DIR/$LEGACY_SKILL_NAME"
    remove_path_if_exists "$CODEX_SKILLS_DIR/${LEGACY_SKILL_NAME}.md"
    remove_path_if_exists "$CODEX_SKILLS_DIR/${SKILL_NAME}.md"

    echo ""
}

install_claude_skill() {
    echo "📝 Installing Claude Code skill..."
    mkdir -p "$CLAUDE_SKILLS_DIR"

    [ -d "$CLAUDE_TARGET_DIR" ] && rm -rf "$CLAUDE_TARGET_DIR"
    [ -f "$CLAUDE_SKILLS_DIR/${SKILL_NAME}.md" ] && rm "$CLAUDE_SKILLS_DIR/${SKILL_NAME}.md"

    mkdir -p "$CLAUDE_TARGET_DIR"
    copy_optional_files "$CLAUDE_TARGET_DIR"

    echo "✅ Installed: $CLAUDE_TARGET_DIR/"
    echo "   • SKILL.md"
    echo ""
}

install_claude_hooks() {
    [ ! -d "$SCRIPT_DIR/hooks" ] && return 0

    echo "🔧 Installing Claude Code hooks..."
    mkdir -p "$CLAUDE_HOOKS_DIR"

    for filename in generate_profiling_report.py profiling_hook.sh test_profiling_report.py; do
        remove_path_if_exists "$CLAUDE_HOOKS_DIR/$filename"
    done

    for file in "$SCRIPT_DIR/hooks"/*; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        cp "$file" "$CLAUDE_HOOKS_DIR/$filename"
        chmod +x "$CLAUDE_HOOKS_DIR/$filename"
        echo "✅ Installed: $CLAUDE_HOOKS_DIR/$filename"
    done
    echo ""
}

register_claude_hooks() {
    [ ! -f "$CLAUDE_HOOKS_DIR/check-study_master.sh" ] && return 0

    echo "📝 Registering Claude Code hooks in settings.json..."

    [ ! -f "$CLAUDE_SETTINGS_FILE" ] && echo '{}' > "$CLAUDE_SETTINGS_FILE"

    python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")
hook_cmd = 'bash "$HOME/.claude/hooks/check-study_master.sh"'
hook_timeout = 30
desired_matcher = "Write|Edit"

try:
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)
except Exception:
    settings = {}

hooks = settings.setdefault('hooks', {})
post_tool_use = hooks.setdefault('PostToolUse', [])

hook_entry = {"type": "command", "command": hook_cmd, "timeout": hook_timeout}
normalized_matchers = []

for matcher in list(post_tool_use):
    matcher_hooks = matcher.get('hooks') or []
    kept_hooks = [hook for hook in matcher_hooks if hook.get('command') != hook_cmd]
    if len(kept_hooks) != len(matcher_hooks):
        normalized_matchers.append(matcher.get('matcher', '<unknown>'))
        if kept_hooks:
            matcher['hooks'] = kept_hooks
        else:
            post_tool_use.remove(matcher)

matcher = next((m for m in post_tool_use if m.get('matcher') == desired_matcher), None)
if matcher is None:
    matcher = {"matcher": desired_matcher, "hooks": []}
    post_tool_use.append(matcher)

existing_hook = next((h for h in matcher.get('hooks', []) if h.get('command') == hook_cmd), None)
if existing_hook is None:
    matcher.setdefault('hooks', []).append(dict(hook_entry))
    action = "✅ Added hook"
else:
    action = "⏭️  Hook already exists"
    for key, value in hook_entry.items():
        if existing_hook.get(key) != value:
            existing_hook[key] = value
            action = "🔄 Updated hook settings"

if normalized_matchers:
    names = ", ".join(dict.fromkeys(normalized_matchers))
    print(f"🧹 Normalized hook registrations: {names}")
print(f"{action}: PostToolUse/{desired_matcher}")

with open(settings_file, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
PYTHON_SCRIPT

    echo ""
}

install_codex_skill() {
    echo "📝 Installing Codex skill..."
    mkdir -p "$CODEX_SKILLS_DIR"

    [ -d "$CODEX_TARGET_DIR" ] && rm -rf "$CODEX_TARGET_DIR"
    mkdir -p "$CODEX_TARGET_DIR"
    copy_optional_files "$CODEX_TARGET_DIR"

    if [ -d "$SCRIPT_DIR/hooks" ]; then
        mkdir -p "$CODEX_TARGET_DIR/hooks"
        for file in "$SCRIPT_DIR/hooks"/*; do
            [ -f "$file" ] || continue
            filename=$(basename "$file")
            cp "$file" "$CODEX_TARGET_DIR/hooks/$filename"
            chmod +x "$CODEX_TARGET_DIR/hooks/$filename"
            echo "✅ Installed: $CODEX_TARGET_DIR/hooks/$filename"
        done
    fi

    echo "✅ Installed: $CODEX_TARGET_DIR/"
    echo "   • SKILL.md"
    [ -d "$CODEX_TARGET_DIR/hooks" ] && echo "   • hooks/"
    echo ""
}

register_codex_hook() {
    [ ! -f "$CODEX_TARGET_DIR/hooks/check-study_master.sh" ] && return 0

    echo "📝 Registering Codex Stop hook..."
    mkdir -p "$CODEX_DIR"
    [ ! -f "$CODEX_HOOKS_FILE" ] && echo '{}' > "$CODEX_HOOKS_FILE"

    python3 << 'PYTHON_SCRIPT'
import json
import os

hooks_file = os.path.expanduser("~/.codex/hooks.json")
hook_cmd = os.path.expanduser("~/.agents/skills/study-master/hooks/check-study_master.sh")
hook_entry = {
    "type": "command",
    "command": f"/bin/bash {hook_cmd}",
    "timeout": 30,
}

try:
    with open(hooks_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    data = {}

hooks = data.setdefault("hooks", {})
stop_hooks = hooks.setdefault("Stop", [])

existing_hook = None
for group in stop_hooks:
    for hook in group.get("hooks", []):
        if hook.get("command") == hook_entry["command"]:
            existing_hook = hook
            break
    if existing_hook is not None:
        break

if existing_hook is not None:
    updated = False
    for key, value in hook_entry.items():
        if existing_hook.get(key) != value:
            existing_hook[key] = value
            updated = True
    if updated:
        print("🔄 Updated Codex Stop hook settings")
    else:
        print("⏭️  Codex Stop hook already exists")
else:
    stop_hooks.append({"hooks": [dict(hook_entry)]})
    print("✅ Added Codex Stop hook")

with open(hooks_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYTHON_SCRIPT

    echo ""
}

enable_codex_hooks_feature() {
    echo "📝 Enabling Codex hook feature..."

    python3 << 'PYTHON_SCRIPT'
import os
from pathlib import Path

config_path = Path(os.path.expanduser("~/.codex/config.toml"))
config_path.parent.mkdir(parents=True, exist_ok=True)

if not config_path.exists():
    config_path.write_text("[features]\ncodex_hooks = true\n", encoding="utf-8")
    print("✅ Created ~/.codex/config.toml with features.codex_hooks = true")
    raise SystemExit(0)

lines = config_path.read_text(encoding="utf-8").splitlines()
out = []
in_features = False
features_seen = False
feature_written = False

for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        if in_features and not feature_written:
            out.append("codex_hooks = true")
            feature_written = True
        in_features = stripped == "[features]"
        features_seen = features_seen or in_features
        out.append(line)
        continue

    if in_features and stripped.startswith("codex_hooks"):
        out.append("codex_hooks = true")
        feature_written = True
        continue

    out.append(line)

if features_seen and in_features and not feature_written:
    out.append("codex_hooks = true")
    feature_written = True

if not features_seen:
    if out and out[-1] != "":
        out.append("")
    out.append("[features]")
    out.append("codex_hooks = true")
    feature_written = True

config_path.write_text("\n".join(out) + "\n", encoding="utf-8")
print("✅ Ensured features.codex_hooks = true in ~/.codex/config.toml")
PYTHON_SCRIPT

    echo ""
}

install_claude_skill
install_claude_hooks
register_claude_hooks

cleanup_legacy_skill_installs
install_codex_skill
register_codex_hook
enable_codex_hooks_feature

echo "🎉 Installation complete!"
echo ""
echo "Installed components:"
echo "  • Claude skill: $CLAUDE_TARGET_DIR/"
[ -d "$SCRIPT_DIR/hooks" ] && echo "  • Claude hooks: $CLAUDE_HOOKS_DIR/"
echo "  • Codex skill: $CODEX_TARGET_DIR/"
[ -d "$SCRIPT_DIR/hooks" ] && echo "  • Codex hook config: $CODEX_HOOKS_FILE"
[ -f "$CODEX_CONFIG_FILE" ] && echo "  • Codex config: $CODEX_CONFIG_FILE"
echo ""
echo "📖 Required project structure:"
echo "  project-root/"
echo "  ├── source/       # Source code (one of source/specs is required)"
echo "  ├── specs/        # Documentation (one of source/specs is required)"
echo "  └── study/        # Generated study docs (auto-created)"
echo ""
echo "Usage:"
echo "  Claude Code: /${SKILL_NAME} <topic>"
echo "  Codex: invoke the ${SKILL_NAME} skill with a topic such as 'redis' or 'tcp'"
