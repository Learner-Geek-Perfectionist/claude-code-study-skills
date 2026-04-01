#!/usr/bin/env bash
# Validate study-master output for both Claude-style file hooks and Codex Stop hooks.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/validate_study_master.py"
input=$(cat)

# Decode the hook payload once so both Claude and Codex paths reuse the same values.
{
  IFS= read -r -d '' mode || true
  IFS= read -r -d '' file_path || true
  IFS= read -r -d '' cwd || true
  IFS= read -r -d '' stop_hook_active || true
  IFS= read -r -d '' turn_id || true
  IFS= read -r -d '' transcript_path || true
} < <(
  printf '%s' "$input" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    values = ("unknown", "", "", "false", "", "")
else:
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if file_path:
        mode = "claude"
    elif data.get("hook_event_name") == "Stop" or "stop_hook_active" in data or "last_assistant_message" in data:
        mode = "codex-stop"
    else:
        mode = "unknown"

    values = (
        mode,
        file_path,
        data.get("cwd", ""),
        "true" if data.get("stop_hook_active") else "false",
        data.get("turn_id", ""),
        data.get("transcript_path", "") or "",
    )

sys.stdout.write("\0".join(values) + "\0")
'
)

if [[ "$mode" == "claude" ]]; then

  [[ -z "$file_path" || ! -f "$file_path" ]] && exit 0
  [[ ! "$file_path" =~ \.md$ ]] && exit 0
  [[ ! "$file_path" =~ (^|/)study/.+\.md$ ]] && exit 0

  python3 "$VALIDATOR" "$file_path"
  exit 0
fi

if [[ "$mode" != "codex-stop" ]]; then
  exit 0
fi

[[ -z "$cwd" || ! -d "$cwd" ]] && exit 0
cwd=$(
  python3 - "$cwd" <<'PY'
import sys
from pathlib import Path

print(Path(sys.argv[1]).resolve())
PY
)
[[ ! -d "$cwd/study" ]] && exit 0

declare -a study_files=()
study_files_output=$(
  python3 - "$cwd" "$turn_id" "$transcript_path" <<'PY'
import json
import sys
from pathlib import Path

cwd = Path(sys.argv[1]).resolve()
turn_id = sys.argv[2]
transcript_path = sys.argv[3]

if not turn_id or not transcript_path:
    raise SystemExit(0)

transcript = Path(transcript_path)
if not transcript.exists():
    raise SystemExit(0)

seen = set()
candidates = []
non_write_types = {"read", "search", "list_files", "unknown"}

def add_candidate(path_str: str) -> None:
    if not path_str:
        return
    try:
        path = Path(path_str)
        if not path.is_absolute():
            path = (cwd / path).resolve()
        else:
            path = path.resolve()
    except Exception:
        return

    try:
        rel = path.relative_to(cwd)
    except ValueError:
        return

    rel_str = rel.as_posix()
    if not rel_str.startswith("study/") or not rel_str.endswith(".md"):
        return
    if not path.exists():
        return

    normalized = str(path)
    if normalized not in seen:
        seen.add(normalized)
        candidates.append(normalized)

for line in transcript.read_text(encoding="utf-8").splitlines():
    try:
        obj = json.loads(line)
    except Exception:
        continue

    payload = obj.get("payload", {})
    if payload.get("turn_id") != turn_id:
        continue

    if obj.get("type") != "event_msg":
        continue

    event_type = payload.get("type")
    if event_type == "patch_apply_end":
        for path_str in (payload.get("changes") or {}).keys():
            add_candidate(path_str)
        continue

    if event_type == "exec_command_end":
        for parsed in payload.get("parsed_cmd") or []:
            parsed_type = parsed.get("type")
            if parsed_type in non_write_types:
                continue
            add_candidate(parsed.get("path") or "")

for item in sorted(candidates):
    print(item)
PY
)
while IFS= read -r line; do
  [[ -n "$line" ]] && study_files+=("$line")
done <<< "$study_files_output"
[[ ${#study_files[@]} -eq 0 ]] && exit 0

fail_count=0
declare -a failure_summary=()

for file_path in "${study_files[@]}"; do
  err_file=$(mktemp)
  if python3 "$VALIDATOR" "$file_path" 2>"$err_file"; then
    rm -f "$err_file"
    continue
  fi

  fail_count=$((fail_count + 1))
  rel_path=${file_path#"$cwd"/}
  first_issue=$(
    python3 - "$err_file" <<'PY'
import sys
from pathlib import Path

err_path = Path(sys.argv[1])
lines = [line.strip() for line in err_path.read_text(encoding="utf-8").splitlines() if line.strip()]
summary = next((line for line in lines if line.startswith("Line ")), "")
if not summary:
    summary = next((line for line in lines if line.startswith("[") and "issue" in line), "")
if not summary and lines:
    summary = lines[-1]
print(summary)
PY
  )

  failure_summary+=("$rel_path :: $first_issue")
  cat "$err_file" >&2
  rm -f "$err_file"
done

[[ $fail_count -eq 0 ]] && exit 0

summary_text=$(
  printf '%s\n' "${failure_summary[@]}" | python3 -c '
import sys

items = [line.strip() for line in sys.stdin if line.strip()]
limit = 5
shown = items[:limit]
parts = ["- " + item for item in shown]
if len(items) > limit:
    parts.append(f"- ... and {len(items) - limit} more file(s)")
print("\\n".join(parts))
'
)

if [[ "$stop_hook_active" == "true" ]]; then
  python3 - "$summary_text" <<'PY'
import json, sys

summary = sys.argv[1]
payload = {
    "continue": False,
    "stopReason": (
        "study-master validation is still failing after one automatic continuation. "
        "Stop here and inspect the reported files manually."
    ),
    "systemMessage": "Outstanding study-master validation issues:\n" + summary,
}
print(json.dumps(payload, ensure_ascii=False))
PY
  exit 0
fi

python3 - "$summary_text" <<'PY'
import json, sys

summary = sys.argv[1]
payload = {
    "decision": "block",
    "reason": (
        "study-master validation failed for generated study markdown. "
        "Fix the reported files, rerun validation, and only stop when the study output is clean.\n"
        + summary
    ),
}
print(json.dumps(payload, ensure_ascii=False))
PY
