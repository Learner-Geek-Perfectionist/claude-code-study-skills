#!/usr/bin/env bash
# PostToolUse hook: validate study-master generated files
# Exits 2 (blocking) if critical errors found

set -euo pipefail

input=$(cat)

file_path=$(printf '%s' "$input" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
")

# Only check markdown files in study/ directory
[[ -z "$file_path" || ! -f "$file_path" ]] && exit 0
[[ ! "$file_path" =~ \.md$ ]] && exit 0
[[ ! "$file_path" =~ study/.+\.md$ ]] && exit 0

# Call Python validator
python3 "$(dirname "$0")/validate_study_master.py" "$file_path"
