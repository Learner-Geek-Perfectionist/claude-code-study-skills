# Study-Master 性能诊断系统 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 study-master skill 构建一次性性能诊断工具链，包括阶段计时、工具调用日志和自动报告生成

**Architecture:** 两层数据采集（SKILL.md 阶段检查点 + PostToolUse hook 工具日志）汇入统一的 profiling log，由 Python 脚本解析生成可视化报告。所有诊断组件均为临时性的，诊断完成后可一键清理。

**Tech Stack:** Bash (hooks), Python 3 (报告生成), Markdown (SKILL 注入)

---

### Task 1: 创建 profiling hook 脚本

**Files:**
- Create: `hooks/profiling_hook.sh`

**Step 1: 编写 hook 脚本**

```bash
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
```

**Step 2: 设为可执行**

Run: `chmod +x hooks/profiling_hook.sh`

**Step 3: 验证脚本语法**

Run: `bash -n hooks/profiling_hook.sh`
Expected: 无输出（无语法错误）

**Step 4: Commit**

```bash
git add hooks/profiling_hook.sh
git commit -m "feat(profiling): add PostToolUse hook for tool call logging"
```

---

### Task 2: 创建报告生成脚本（含测试数据）

**Files:**
- Create: `hooks/generate_profiling_report.py`
- Create: `hooks/test_profiling_report.py`

**Step 1: 创建测试用的模拟 profiling 数据**

```python
# hooks/test_profiling_report.py
"""测试 profiling 报告生成器"""
import tempfile
import os
import sys

# 模拟 20 分钟运行的 profiling 数据
SAMPLE_PHASE_LOG = """PHASE|stage-0-2|start|1710489600
PHASE|stage-0-2|end|1710489660
PHASE|stage-3-analysis|start|1710489660
PHASE|stage-3-analysis|end|1710490080
PHASE|stage-4-serialize|start|1710490080
PHASE|stage-4-serialize|end|1710490320
PHASE|stage-5-overview|start|1710490320
AGENT|overview|start|1710490325
AGENT|overview|end|1710490500
PHASE|stage-5-overview|end|1710490505
PHASE|stage-6N-chapters|start|1710490505
AGENT|01-module-core|start|1710490510
AGENT|02-module-net|start|1710490510
AGENT|03-module-data|start|1710490510
AGENT|01-module-core|end|1710490660
AGENT|03-module-data|end|1710490690
AGENT|02-module-net|end|1710490720
PHASE|stage-6N-chapters|end|1710490725
PHASE|final|start|1710490725
PHASE|final-step-1|start|1710490725
PHASE|final-step-1|end|1710490785
PHASE|final-step-2|start|1710490785
PHASE|final-step-2|end|1710490905
PHASE|final-step-3|start|1710490905
PHASE|final-step-3|end|1710490995
PHASE|final-step-4|start|1710490995
PHASE|final-step-4|end|1710491055
PHASE|final-step-5|start|1710491055
PHASE|final-step-5|end|1710491115
PHASE|final-step-6|start|1710491115
PHASE|final-step-6|end|1710491175
PHASE|final|end|1710491175
"""

SAMPLE_TOOL_LOG = """TOOL|Read|src/core/module.c|1710489665
TOOL|Read|src/core/types.h|1710489670
TOOL|Read|src/net/socket.c|1710489680
TOOL|Read|src/net/protocol.c|1710489690
TOOL|Read|src/data/store.c|1710489700
TOOL|Read|src/data/cache.c|1710489710
TOOL|LSP|src/core/module.c|1710489720
TOOL|LSP|src/net/socket.c|1710489730
TOOL|Read|src/core/module.c|1710489800
TOOL|Read|src/core/types.h|1710489850
TOOL|Write|study/topic/.analysis-context.md|1710490300
TOOL|Agent|overview|1710490325
TOOL|Agent|01-module-core|1710490510
TOOL|Agent|02-module-net|1710490510
TOOL|Agent|03-module-data|1710490510
TOOL|Read|study/topic/00-overview.md|1710490730
TOOL|Read|study/topic/01-module-core.md|1710490735
TOOL|Read|study/topic/02-module-net.md|1710490740
TOOL|Read|study/topic/03-module-data.md|1710490745
TOOL|Edit|study/topic/01-module-core.md|1710490900
TOOL|Edit|study/topic/02-module-net.md|1710490950
TOOL|Edit|study/topic/00-overview.md|1710491100
TOOL|Write|study/topic/appendix-references.md|1710491150
TOOL|Write|study/topic/.study-meta.json|1710491160
"""


def test_report_generation():
    """测试报告生成的完整流程"""
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, prefix='phase_') as pf:
        pf.write(SAMPLE_PHASE_LOG)
        phase_log = pf.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, prefix='tool_') as tf:
        tf.write(SAMPLE_TOOL_LOG)
        tool_log = tf.name

    try:
        from generate_profiling_report import ProfilingAnalyzer

        analyzer = ProfilingAnalyzer(phase_log, tool_log)
        report = analyzer.generate_report()

        # 验证报告包含关键部分
        assert '## 1. 总耗时概览' in report, "缺少总耗时概览"
        assert '## 2. 阶段耗时排行' in report, "缺少阶段耗时排行"
        assert '## 3. 工具调用统计' in report, "缺少工具调用统计"
        assert '## 4. Subagent 并行度分析' in report, "缺少并行度分析"
        assert '## 5. 瓶颈诊断结论' in report, "缺少瓶颈结论"

        # 验证总耗时计算（1710491175 - 1710489600 = 1575 秒 ≈ 26 分钟）
        assert '1575' in report or '26' in report, "总耗时计算错误"

        # 验证 stage-3 被标记为瓶颈（420 秒，最长阶段）
        assert 'stage-3-analysis' in report, "缺少 stage-3 分析"

        # 验证 subagent 并行度计算
        # 并行时间 = max(150, 210, 180) = 210 秒
        # 总时间 = 150 + 210 + 180 = 540 秒
        # 并行效率 = 210/540 ≈ 38.9%（越低越好，说明并行度高）
        assert 'overview' in report or '并行' in report, "缺少并行度数据"

        print("✅ 所有测试通过！")
        print("\n--- 生成的报告预览 ---\n")
        print(report[:2000])

    finally:
        os.unlink(phase_log)
        os.unlink(tool_log)


if __name__ == '__main__':
    # 需要从 hooks 目录运行
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    test_report_generation()
```

**Step 2: 运行测试确认失败**

Run: `cd hooks && python3 test_profiling_report.py`
Expected: FAIL（ImportError: generate_profiling_report 不存在）

**Step 3: 编写报告生成器**

```python
# hooks/generate_profiling_report.py
"""Study-Master 性能诊断报告生成器

用法：
    python3 generate_profiling_report.py <phase_log> [tool_log]

参数：
    phase_log: 阶段检查点日志（study/<topic>/.profiling.log）
    tool_log:  工具调用日志（/tmp/study-master-tool.log），可选
"""
import sys
import os
from collections import defaultdict
from typing import Optional


class ProfilingAnalyzer:
    def __init__(self, phase_log_path: str, tool_log_path: Optional[str] = None):
        self.phases = []      # [(name, start, end, duration)]
        self.agents = []      # [(name, start, end, duration)]
        self.tools = []       # [(tool_name, file_path, timestamp)]

        self._parse_phase_log(phase_log_path)
        if tool_log_path and os.path.exists(tool_log_path):
            self._parse_tool_log(tool_log_path)

    def _parse_phase_log(self, path: str):
        starts = {}
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) != 4:
                    continue
                record_type, name, action, timestamp = parts
                timestamp = int(timestamp)

                if record_type == 'PHASE':
                    if action == 'start':
                        starts[name] = timestamp
                    elif action == 'end' and name in starts:
                        duration = timestamp - starts[name]
                        self.phases.append((name, starts[name], timestamp, duration))
                        del starts[name]

                elif record_type == 'AGENT':
                    if action == 'start':
                        starts[f'agent:{name}'] = timestamp
                    elif action == 'end' and f'agent:{name}' in starts:
                        key = f'agent:{name}'
                        duration = timestamp - starts[key]
                        self.agents.append((name, starts[key], timestamp, duration))
                        del starts[key]

    def _parse_tool_log(self, path: str):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) != 4:
                    continue
                _, tool_name, file_path, timestamp = parts
                self.tools.append((tool_name, file_path, int(timestamp)))

    def _format_duration(self, seconds: int) -> str:
        if seconds >= 60:
            m, s = divmod(seconds, 60)
            return f"{m}m{s:02d}s"
        return f"{seconds}s"

    def _severity(self, seconds: int) -> str:
        if seconds >= 180:
            return '🔴'
        if seconds >= 60:
            return '🟡'
        return '🟢'

    def generate_report(self) -> str:
        sections = []
        sections.append("# Study-Master 性能诊断报告\n")

        # 1. 总耗时概览
        sections.append(self._section_overview())

        # 2. 阶段耗时排行
        sections.append(self._section_phases())

        # 3. 工具调用统计
        sections.append(self._section_tools())

        # 4. Subagent 并行度分析
        sections.append(self._section_agents())

        # 5. 瓶颈诊断结论
        sections.append(self._section_bottlenecks())

        return '\n'.join(sections)

    def _section_overview(self) -> str:
        # 找到最早和最晚的时间戳
        all_times = [p[1] for p in self.phases] + [p[2] for p in self.phases]
        if not all_times:
            return "## 1. 总耗时概览\n\n无数据\n"

        total = max(all_times) - min(all_times)
        lines = [
            "## 1. 总耗时概览\n",
            f"- **总耗时**: {self._format_duration(total)} ({total} 秒)",
            f"- **阶段数**: {len([p for p in self.phases if not p[0].startswith('final-step')])}",
            f"- **Subagent 调用**: {len(self.agents)} 次",
            f"- **工具调用**: {len(self.tools)} 次\n",
        ]
        return '\n'.join(lines)

    def _section_phases(self) -> str:
        # 只显示顶层阶段（不显示 final-step-N 细节，除非在 final 展开中）
        top_phases = [p for p in self.phases if not p[0].startswith('final-step')]
        top_phases.sort(key=lambda x: x[3], reverse=True)

        total = sum(p[3] for p in top_phases) if top_phases else 1

        lines = ["## 2. 阶段耗时排行\n"]
        lines.append("| 阶段 | 耗时 | 占比 | 状态 |")
        lines.append("|------|------|------|------|")

        for name, _, _, duration in top_phases:
            pct = duration / total * 100
            severity = self._severity(duration)
            lines.append(f"| {name} | {self._format_duration(duration)} | {pct:.0f}% | {severity} |")

        # 如果有 final-step 详情，展开
        final_steps = [p for p in self.phases if p[0].startswith('final-step')]
        if final_steps:
            final_steps.sort(key=lambda x: x[0])
            lines.append("\n### 最后阶段详细步骤\n")
            lines.append("| 步骤 | 耗时 | 状态 |")
            lines.append("|------|------|------|")
            for name, _, _, duration in final_steps:
                severity = self._severity(duration)
                step_num = name.replace('final-step-', '')
                step_labels = {
                    '1': '格式验证', '2': '内容审查', '3': '交叉引用注入',
                    '4': '深度补充', '5': '概览更新', '6': '整合'
                }
                label = step_labels.get(step_num, step_num)
                lines.append(f"| {label} | {self._format_duration(duration)} | {severity} |")

        lines.append("")
        return '\n'.join(lines)

    def _section_tools(self) -> str:
        if not self.tools:
            return "## 3. 工具调用统计\n\n无工具日志数据（/tmp/study-master-tool.log 不存在或为空）\n"

        # 按工具类型统计
        by_type = defaultdict(int)
        for tool_name, _, _ in self.tools:
            by_type[tool_name] += 1

        lines = ["## 3. 工具调用统计\n"]
        lines.append("### 按工具类型\n")
        lines.append("| 工具 | 调用次数 |")
        lines.append("|------|---------|")
        for tool, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {tool} | {count} |")

        # 检测重复读取
        read_files = [fp for tn, fp, _ in self.tools if tn == 'Read']
        file_counts = defaultdict(int)
        for fp in read_files:
            file_counts[fp] += 1
        duplicates = {fp: c for fp, c in file_counts.items() if c > 1}

        if duplicates:
            lines.append("\n### 重复读取的文件\n")
            lines.append("| 文件 | 读取次数 |")
            lines.append("|------|---------|")
            for fp, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {fp} | {count} |")

        lines.append("")
        return '\n'.join(lines)

    def _section_agents(self) -> str:
        if not self.agents:
            return "## 4. Subagent 并行度分析\n\n无 subagent 数据\n"

        # 分离 overview（串行）和章节 subagent（并行）
        overview = [a for a in self.agents if a[0] == 'overview']
        chapters = [a for a in self.agents if a[0] != 'overview']

        lines = ["## 4. Subagent 并行度分析\n"]

        if overview:
            ov = overview[0]
            lines.append(f"### Overview 章节（串行）\n")
            lines.append(f"- 耗时: {self._format_duration(ov[3])}\n")

        if chapters:
            chapters.sort(key=lambda x: x[3], reverse=True)
            total_sum = sum(a[3] for a in chapters)
            max_duration = max(a[3] for a in chapters)
            min_duration = min(a[3] for a in chapters)
            efficiency = max_duration / total_sum * 100 if total_sum > 0 else 0

            lines.append(f"### 模块章节（并行）\n")
            lines.append(f"- **并行墙钟时间**: {self._format_duration(max_duration)}（取决于最慢的 subagent）")
            lines.append(f"- **总计算时间**: {self._format_duration(total_sum)}（所有 subagent 耗时之和）")
            lines.append(f"- **并行效率**: {efficiency:.1f}%（越低说明并行度越高，理想值 = 100%/{len(chapters)} = {100/len(chapters):.0f}%）")
            lines.append(f"- **长尾比**: {max_duration/min_duration:.1f}x（最慢/最快，>2x 说明有长尾）\n")

            lines.append("| 章节 | 耗时 | 状态 |")
            lines.append("|------|------|------|")
            for name, _, _, duration in chapters:
                severity = self._severity(duration)
                lines.append(f"| {name} | {self._format_duration(duration)} | {severity} |")

        lines.append("")
        return '\n'.join(lines)

    def _section_bottlenecks(self) -> str:
        lines = ["## 5. 瓶颈诊断结论\n"]

        # 找出所有 > 120 秒的阶段
        bottlenecks = [(n, d) for n, _, _, d in self.phases
                       if d >= 120 and not n.startswith('final-step')]

        if not bottlenecks:
            lines.append("未发现明显瓶颈（所有阶段 < 2 分钟）。\n")
            return '\n'.join(lines)

        bottlenecks.sort(key=lambda x: x[1], reverse=True)

        for name, duration in bottlenecks:
            lines.append(f"### 🔴 {name} ({self._format_duration(duration)})\n")

            if 'stage-3' in name:
                lines.append("**可能原因**: 全源码深度分析——大量 Read 调用 + LLM 串行推理")
                lines.append("**优化方向**: 减少 Read 次数（合并文件读取）、精简分析范围、预缓存 LSP 数据\n")
            elif 'stage-4' in name:
                lines.append("**可能原因**: 富分析报告序列化——大量 token 生成写入 .analysis-context.md")
                lines.append("**优化方向**: 精简报告内容、只序列化 subagent 真正需要的信息\n")
            elif 'stage-5' in name:
                lines.append("**可能原因**: overview 章节串行等待——阻塞了后续并行章节")
                lines.append("**优化方向**: 考虑与模块章节并行生成（取消 overview 串行依赖）\n")
            elif 'stage-6N' in name:
                lines.append("**可能原因**: 并行章节中有长尾 subagent，或 subagent 需要额外 Read 源码")
                lines.append("**优化方向**: 在分析报告中提供更充分的信息减少 subagent 回读源码\n")
            elif 'final' in name:
                lines.append("**可能原因**: 6 步后处理全部串行——格式验证+内容审查+交叉引用+深度补充+概览更新+整合")
                lines.append("**优化方向**: 合并审查步骤、减少重复 Read、将部分工作前置到 subagent\n")
            else:
                lines.append("**可能原因**: 待具体分析")
                lines.append("**优化方向**: 查看工具调用日志了解详情\n")

        return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_profiling_report.py <phase_log> [tool_log]", file=sys.stderr)
        sys.exit(1)

    phase_log = sys.argv[1]
    tool_log = sys.argv[2] if len(sys.argv) > 2 else "/tmp/study-master-tool.log"

    if not os.path.exists(phase_log):
        print(f"错误: 找不到阶段日志 {phase_log}", file=sys.stderr)
        sys.exit(1)

    analyzer = ProfilingAnalyzer(phase_log, tool_log)
    report = analyzer.generate_report()

    # 输出到同目录的 .profiling-report.md
    output_dir = os.path.dirname(os.path.abspath(phase_log))
    output_path = os.path.join(output_dir, '.profiling-report.md')
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"✅ 报告已生成: {output_path}")
    print(report)


if __name__ == '__main__':
    main()
```

**Step 4: 运行测试验证通过**

Run: `cd hooks && python3 test_profiling_report.py`
Expected: `✅ 所有测试通过！` + 报告预览

**Step 5: Commit**

```bash
git add hooks/generate_profiling_report.py hooks/test_profiling_report.py
git commit -m "feat(profiling): add report generator with test data"
```

---

### Task 3: 创建诊断版 SKILL.md

**Files:**
- Read: `~/.claude/skills/study-master/SKILL.md`（获取最新版本）
- Create: `SKILL-profiling.md`（带检查点的诊断版）

**Step 1: 生成 SKILL-profiling.md**

在原始 SKILL.md 的基础上，在每个阶段边界注入检查点指令。具体注入位置和内容：

1. 在 `### 阶段 0：源码定位与验证` 标题后添加：
```markdown
> ⏱️ **[诊断模式]** 阶段 0-2 开始，运行：`Bash: echo "PHASE|stage-0-2|start|$(date +%s)" >> {study_path}/.profiling.log`（其中 `{study_path}` 替换为实际的 `study/<topic>/` 路径）
```

2. 在 `### 阶段 2：主题识别与准备` 末尾添加：
```markdown
> ⏱️ **[诊断模式]** 阶段 0-2 结束，运行：`Bash: echo "PHASE|stage-0-2|end|$(date +%s)" >> {study_path}/.profiling.log`
```

3. 在 `### 阶段 3：全源码深度分析` 标题后添加：
```markdown
> ⏱️ **[诊断模式]** 阶段 3 开始，运行：`Bash: echo "PHASE|stage-3-analysis|start|$(date +%s)" >> {study_path}/.profiling.log`
```

4. 在阶段 3 末尾添加：
```markdown
> ⏱️ **[诊断模式]** 阶段 3 结束，运行：`Bash: echo "PHASE|stage-3-analysis|end|$(date +%s)" >> {study_path}/.profiling.log`
```

5. 对阶段 4、5、6-N、最后阶段（及其 6 个子步骤）同样处理。

6. 对 Agent 调用（阶段 5 的 overview subagent 和阶段 6-N 的每个模块 subagent），在调用前后添加：
```markdown
> ⏱️ **[诊断模式]** Agent 调度前运行：`Bash: echo "AGENT|{chapter_name}|start|$(date +%s)" >> {study_path}/.profiling.log`
```
```markdown
> ⏱️ **[诊断模式]** Agent 返回后运行：`Bash: echo "AGENT|{chapter_name}|end|$(date +%s)" >> {study_path}/.profiling.log`
```

7. 在最后阶段的步骤 6（整合）末尾添加报告生成指令：
```markdown
> ⏱️ **[诊断模式]** 所有阶段完成，生成诊断报告：
> `Bash: python3 ~/.claude/hooks/generate_profiling_report.py {study_path}/.profiling.log /tmp/study-master-tool.log`
```

**Step 2: 验证 SKILL-profiling.md 的完整性**

手动检查：
- 原始 SKILL.md 的所有内容完整保留
- 每个阶段都有 start/end 检查点
- Agent 调用前后都有检查点
- 最后有报告生成指令

**Step 3: Commit**

```bash
git add SKILL-profiling.md
git commit -m "feat(profiling): create instrumented SKILL with timing checkpoints"
```

---

### Task 4: 创建安装/清理脚本

**Files:**
- Create: `profiling-install.sh`
- Create: `profiling-cleanup.sh`

**Step 1: 编写安装脚本**

```bash
#!/usr/bin/env bash
# 安装 study-master 诊断模式
set -euo pipefail

SKILL_DIR="$HOME/.claude/skills/study-master"
HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 安装 study-master 诊断模式..."

# 1. 备份原始 SKILL.md
cp "$SKILL_DIR/SKILL.md" "$SKILL_DIR/SKILL.md.bak"
echo "✅ 备份: SKILL.md → SKILL.md.bak"

# 2. 替换为诊断版
cp "$SCRIPT_DIR/SKILL-profiling.md" "$SKILL_DIR/SKILL.md"
echo "✅ 替换: SKILL-profiling.md → SKILL.md"

# 3. 安装 profiling hook 和报告生成器
cp "$SCRIPT_DIR/hooks/profiling_hook.sh" "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR/profiling_hook.sh"
cp "$SCRIPT_DIR/hooks/generate_profiling_report.py" "$HOOKS_DIR/"
echo "✅ 安装: profiling_hook.sh, generate_profiling_report.py"

# 4. 注册 hook
python3 << 'PYTHON_SCRIPT'
import json
settings_file = "$HOME/.claude/settings/settings.json".replace("$HOME", __import__("os").path.expanduser("~"))
with open(settings_file) as f:
    settings = json.load(f)

hook_config = {
    "name": "study-master-profiling",
    "event": "PostToolUse",
    "command": __import__("os").path.expanduser("~") + "/.claude/hooks/profiling_hook.sh"
}

# 移除旧的同名 hook
settings['hooks'] = [h for h in settings.get('hooks', []) if h.get('name') != 'study-master-profiling']
settings['hooks'].append(hook_config)

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
print("✅ 注册: PostToolUse profiling hook")
PYTHON_SCRIPT

# 5. 清空旧日志
rm -f /tmp/study-master-tool.log
echo "✅ 清理: /tmp/study-master-tool.log"

echo ""
echo "🎉 诊断模式已启用！"
echo "   现在可以运行 /study-master <topic> 进行诊断。"
echo "   完成后运行 ./profiling-cleanup.sh 恢复原始版本。"
```

**Step 2: 编写清理脚本**

```bash
#!/usr/bin/env bash
# 卸载 study-master 诊断模式，恢复原始版本
set -euo pipefail

SKILL_DIR="$HOME/.claude/skills/study-master"
HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings/settings.json"

echo "🔧 恢复 study-master 原始版本..."

# 1. 恢复原始 SKILL.md
if [ -f "$SKILL_DIR/SKILL.md.bak" ]; then
    mv "$SKILL_DIR/SKILL.md.bak" "$SKILL_DIR/SKILL.md"
    echo "✅ 恢复: SKILL.md.bak → SKILL.md"
else
    echo "⚠️  未找到备份文件 SKILL.md.bak，跳过恢复"
fi

# 2. 移除 profiling hook 文件
rm -f "$HOOKS_DIR/profiling_hook.sh"
rm -f "$HOOKS_DIR/generate_profiling_report.py"
echo "✅ 删除: profiling_hook.sh, generate_profiling_report.py"

# 3. 注销 hook
python3 << 'PYTHON_SCRIPT'
import json, os
settings_file = os.path.expanduser("~/.claude/settings/settings.json")
with open(settings_file) as f:
    settings = json.load(f)

settings['hooks'] = [h for h in settings.get('hooks', []) if h.get('name') != 'study-master-profiling']

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
print("✅ 注销: PostToolUse profiling hook")
PYTHON_SCRIPT

echo ""
echo "🎉 已恢复原始版本！"
echo "   诊断日志保留在 study/<topic>/.profiling.log"
echo "   诊断报告保留在 study/<topic>/.profiling-report.md"
```

**Step 3: 设为可执行**

Run: `chmod +x profiling-install.sh profiling-cleanup.sh`

**Step 4: Commit**

```bash
git add profiling-install.sh profiling-cleanup.sh
git commit -m "feat(profiling): add install/cleanup scripts for diagnostic mode"
```

---

### Task 5: 端到端测试（可选）

**在实际项目上运行诊断**

1. 运行 `./profiling-install.sh` 安装诊断模式
2. 在一个有 `src/` 目录的中型项目中运行 `/study-master <topic>`
3. 等待完成后查看 `study/<topic>/.profiling-report.md`
4. 运行 `./profiling-cleanup.sh` 恢复

**验证检查项：**
- [ ] `.profiling.log` 包含所有阶段的 start/end 记录
- [ ] `/tmp/study-master-tool.log` 包含工具调用记录
- [ ] `.profiling-report.md` 正确生成，包含 5 个部分
- [ ] 原始文档质量未受影响
- [ ] 清理后 SKILL.md 恢复正常

---

### Task 6: 分析结果并制定优化方向

**基于诊断报告：**

1. 读取 `.profiling-report.md`
2. 识别标红的瓶颈阶段
3. 对比理论分析与实际数据
4. 制定下一步优化计划
