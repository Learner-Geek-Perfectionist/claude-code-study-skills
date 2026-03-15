#!/usr/bin/env bash
# PostToolUse hook: 记录所有工具调用到 profiling 日志
# 写入固定位置 /tmp/study-master-tool.log，避免 hook 需要知道 study/<topic> 路径

set -euo pipefail

LOG_FILE="/tmp/study-master-tool.log"

input=$(cat)

# 提取工具名和文件路径
tool_name=$(printf '%s' "$input" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_name', 'unknown'))
")

file_path=$(printf '%s' "$input" | python3 -c "
import sys, json
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
# 不同工具的路径字段不同
path = inp.get('file_path', '') or inp.get('path', '') or inp.get('command', '[:30]')
print(str(path)[:200])
")

# 只记录与源码分析/文档生成相关的操作
# 跳过明显无关的路径（如 skill 文件本身的加载）
if [[ "$file_path" =~ (study/|src/|docs/|\.analysis-context|\.profiling) ]] || \
   [[ "$tool_name" == "Agent" ]] || \
   [[ "$tool_name" == "LSP" ]]; then
    echo "TOOL|${tool_name}|${file_path}|$(date +%s)" >> "$LOG_FILE"
fi

exit 0
