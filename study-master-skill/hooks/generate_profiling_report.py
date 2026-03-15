#!/usr/bin/env python3
"""
generate_profiling_report.py
解析 study-master profiling 日志，生成 Markdown 格式的性能诊断报告

日志格式:
  PHASE|<name>|start|<timestamp>
  PHASE|<name>|end|<timestamp>
  AGENT|<name>|start|<timestamp>
  AGENT|<name>|end|<timestamp>
  TOOL|<tool_name>|<file_path>|<timestamp>
"""

import os
import sys
from collections import defaultdict


class ProfilingAnalyzer:
    """解析 profiling 日志并生成诊断报告"""

    # final-step 编号 → 中文标签
    FINAL_STEP_LABELS = {
        "final-step-1": "格式验证",
        "final-step-2": "内容审查",
        "final-step-3": "交叉引用注入",
        "final-step-4": "深度补充",
        "final-step-5": "概览更新",
        "final-step-6": "整合",
    }

    def __init__(self, phase_log_path, tool_log_path=None):
        """
        Args:
            phase_log_path: PHASE/AGENT 日志文件路径
            tool_log_path:  TOOL 日志文件路径 (可选)
        """
        self.phases, self.agents = self._parse_phase_log(phase_log_path)
        self.tools = []
        if tool_log_path and os.path.exists(tool_log_path):
            self.tools = self._parse_tool_log(tool_log_path)

    # ------------------------------------------------------------------
    # 解析方法
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_phase_log(path):
        """
        解析 PHASE 和 AGENT 记录，配对 start/end 生成元组列表。

        Returns:
            (phases, agents) 各为 [(name, start, end, duration), ...]
        """
        phase_starts = {}
        agent_starts = {}
        phases = []
        agents = []

        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 4:
                    continue

                record_type = parts[0]
                name = parts[1]
                action = parts[2]
                timestamp = int(parts[3])

                if record_type == "PHASE":
                    if action == "start":
                        phase_starts[name] = timestamp
                    elif action == "end" and name in phase_starts:
                        start = phase_starts.pop(name)
                        duration = timestamp - start
                        phases.append((name, start, timestamp, duration))
                elif record_type == "AGENT":
                    if action == "start":
                        agent_starts[name] = timestamp
                    elif action == "end" and name in agent_starts:
                        start = agent_starts.pop(name)
                        duration = timestamp - start
                        agents.append((name, start, timestamp, duration))

        return phases, agents

    @staticmethod
    def _parse_tool_log(path):
        """
        解析 TOOL 记录。

        Returns:
            [(tool_name, file_path, timestamp), ...]
        """
        tools = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 4 or parts[0] != "TOOL":
                    continue
                tool_name = parts[1]
                file_path = parts[2]
                timestamp = int(parts[3])
                tools.append((tool_name, file_path, timestamp))
        return tools

    # ------------------------------------------------------------------
    # 格式化辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _format_duration(seconds):
        """格式化秒数为易读字符串: 'Xm YYs' 或 'Xs'"""
        if seconds >= 60:
            m = seconds // 60
            s = seconds % 60
            return f"{m}m {s:02d}s"
        return f"{seconds}s"

    @staticmethod
    def _severity(seconds):
        """根据耗时返回严重度标记"""
        if seconds >= 180:
            return "\U0001f534"  # 🔴
        elif seconds >= 60:
            return "\U0001f7e1"  # 🟡
        else:
            return "\U0001f7e2"  # 🟢

    # ------------------------------------------------------------------
    # 报告生成
    # ------------------------------------------------------------------

    def generate_report(self):
        """生成完整 Markdown 诊断报告，包含 5 个 section"""
        sections = [
            self._section_overview(),
            self._section_phase_ranking(),
            self._section_tool_stats(),
            self._section_parallel_analysis(),
            self._section_bottleneck_diagnosis(),
        ]
        header = "# Study-Master 性能诊断报告\n"
        return header + "\n".join(sections)

    def _section_overview(self):
        """Section 1: 总耗时概览"""
        lines = ["\n## 1. 总耗时概览\n"]

        # 计算总耗时：取所有 phase 的最大 end - 最小 start
        if self.phases:
            all_starts = [p[1] for p in self.phases]
            all_ends = [p[2] for p in self.phases]
            total_seconds = max(all_ends) - min(all_starts)
        else:
            total_seconds = 0

        # 顶层 phase 数量 (不含 final-step-N 子阶段)
        top_phases = [p for p in self.phases if not p[0].startswith("final-step-")]
        phase_count = len(top_phases)
        agent_count = len(self.agents)
        tool_count = len(self.tools)

        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 总耗时 | **{self._format_duration(total_seconds)}** |")
        lines.append(f"| 阶段数 | {phase_count} |")
        lines.append(f"| Subagent 数 | {agent_count} |")
        lines.append(f"| 工具调用数 | {tool_count} |")
        lines.append("")
        return "\n".join(lines)

    def _section_phase_ranking(self):
        """Section 2: 阶段耗时排行"""
        lines = ["\n## 2. 阶段耗时排行\n"]

        # 顶层阶段 (不含 final-step-N)
        top_phases = [p for p in self.phases if not p[0].startswith("final-step-")]

        if not top_phases:
            lines.append("_无阶段数据_\n")
            return "\n".join(lines)

        # 总时间用于计算百分比
        total = sum(p[3] for p in top_phases)

        # 按耗时降序排列
        sorted_phases = sorted(top_phases, key=lambda p: p[3], reverse=True)

        lines.append("| # | 阶段 | 耗时 | 占比 | 严重度 |")
        lines.append("|---|------|------|------|--------|")
        for i, (name, _start, _end, dur) in enumerate(sorted_phases, 1):
            pct = (dur / total * 100) if total > 0 else 0
            sev = self._severity(dur)
            lines.append(
                f"| {i} | {name} | {self._format_duration(dur)} | {pct:.1f}% | {sev} |"
            )
        lines.append("")

        # final-step 子表
        final_steps = [p for p in self.phases if p[0].startswith("final-step-")]
        if final_steps:
            lines.append("### Final 阶段明细\n")
            final_steps_sorted = sorted(final_steps, key=lambda p: p[1])  # 按时间顺序
            lines.append("| 步骤 | 标签 | 耗时 | 严重度 |")
            lines.append("|------|------|------|--------|")
            for name, _start, _end, dur in final_steps_sorted:
                label = self.FINAL_STEP_LABELS.get(name, name)
                sev = self._severity(dur)
                lines.append(f"| {name} | {label} | {self._format_duration(dur)} | {sev} |")
            lines.append("")

        return "\n".join(lines)

    def _section_tool_stats(self):
        """Section 3: 工具调用统计"""
        lines = ["\n## 3. 工具调用统计\n"]

        if not self.tools:
            lines.append("_无工具调用数据_\n")
            return "\n".join(lines)

        # 按工具类型统计
        tool_counts = defaultdict(int)
        for tool_name, _path, _ts in self.tools:
            tool_counts[tool_name] += 1

        lines.append("### 按工具类型\n")
        lines.append("| 工具 | 调用次数 |")
        lines.append("|------|---------|")
        for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {tool} | {count} |")
        lines.append("")

        # 重复读取检测
        read_files = defaultdict(int)
        for tool_name, path, _ts in self.tools:
            if tool_name == "Read":
                read_files[path] += 1

        duplicates = {path: count for path, count in read_files.items() if count > 1}
        if duplicates:
            lines.append("### 重复读取检测\n")
            lines.append(
                "以下文件被多次 Read，可考虑缓存或合并读取：\n"
            )
            lines.append("| 文件 | 读取次数 |")
            lines.append("|------|---------|")
            for path, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| `{path}` | {count} |")
            lines.append("")

        return "\n".join(lines)

    def _section_parallel_analysis(self):
        """Section 4: Subagent 并行度分析"""
        lines = ["\n## 4. Subagent 并行度分析\n"]

        if not self.agents:
            lines.append("_无 subagent 数据_\n")
            return "\n".join(lines)

        # 分类：overview (串行) vs chapter agents (并行)
        overview_agents = [a for a in self.agents if a[0] == "overview"]
        chapter_agents = [a for a in self.agents if a[0] != "overview"]

        # Overview agent（串行执行）
        if overview_agents:
            lines.append("### Overview Agent（串行）\n")
            for name, _start, _end, dur in overview_agents:
                lines.append(f"- **{name}**: {self._format_duration(dur)}")
            lines.append("")

        # Chapter agents（并行执行）
        if chapter_agents:
            lines.append("### Chapter Agents（并行）\n")

            durations = [a[3] for a in chapter_agents]
            wall_clock = max(durations)       # 实际耗时 = 最长 agent
            total_compute = sum(durations)     # 总计算时间 = 所有 agent 之和
            min_dur = min(durations)
            parallel_efficiency = (wall_clock / total_compute * 100) if total_compute > 0 else 0
            long_tail_ratio = (wall_clock / min_dur) if min_dur > 0 else 0

            lines.append("| Agent | 耗时 |")
            lines.append("|-------|------|")
            for name, _start, _end, dur in sorted(chapter_agents, key=lambda a: a[3], reverse=True):
                lines.append(f"| {name} | {self._format_duration(dur)} |")
            lines.append("")

            lines.append("| 指标 | 值 |")
            lines.append("|------|-----|")
            lines.append(f"| Wall clock（实际耗时） | {self._format_duration(wall_clock)} |")
            lines.append(f"| Total compute（总计算时间） | {self._format_duration(total_compute)} |")
            lines.append(f"| 并行效率 | {parallel_efficiency:.1f}% |")
            lines.append(f"| Long-tail ratio (max/min) | {long_tail_ratio:.2f}x |")
            lines.append("")

            # 解读
            if parallel_efficiency < 40:
                lines.append("> 并行效率良好，多个 agent 有效并行执行。\n")
            else:
                lines.append("> 并行效率偏低，可能存在长尾 agent 拖慢整体进度。\n")

        return "\n".join(lines)

    def _section_bottleneck_diagnosis(self):
        """Section 5: 瓶颈诊断结论"""
        lines = ["\n## 5. 瓶颈诊断结论\n"]

        threshold = 120  # 超过 120s 标记为瓶颈

        # 找出所有超过阈值的顶层阶段
        top_phases = [p for p in self.phases if not p[0].startswith("final-step-")]
        bottlenecks = [p for p in top_phases if p[3] > threshold]
        bottlenecks.sort(key=lambda p: p[3], reverse=True)

        if not bottlenecks:
            lines.append("未检测到明显瓶颈（所有阶段 ≤ 120s）。\n")
            return "\n".join(lines)

        lines.append(
            f"检测到 **{len(bottlenecks)}** 个瓶颈阶段（耗时 > {threshold}s）：\n"
        )

        for name, _start, _end, dur in bottlenecks:
            sev = self._severity(dur)
            lines.append(f"### {sev} {name} — {self._format_duration(dur)}\n")

            # 针对不同阶段给出优化建议
            if "analysis" in name:
                lines.append("- **原因**: 源码深度分析阶段，文件数量或复杂度较高")
                lines.append("- **优化方向**: 考虑增量分析、缓存 AST 解析结果、或限制分析深度")
            elif "serialize" in name:
                lines.append("- **原因**: 分析结果序列化/写入耗时")
                lines.append("- **优化方向**: 减少中间序列化步骤、使用更高效的格式")
            elif "overview" in name:
                lines.append("- **原因**: 概览生成需要综合所有模块信息")
                lines.append("- **优化方向**: 提前准备摘要数据，减少概览 agent 的上下文量")
            elif "chapter" in name or "6N" in name:
                lines.append("- **原因**: 章节并行生成阶段")
                lines.append("- **优化方向**: 检查长尾 agent，优化最慢模块的提示词或拆分粒度")
            elif "final" in name:
                lines.append("- **原因**: 最终审查与整合阶段，包含多个串行步骤")
                lines.append("- **优化方向**: 审视各 final-step 是否可合并或并行化")
            else:
                lines.append("- **优化方向**: 进一步细分此阶段的子步骤以定位具体瓶颈")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # CLI 入口
    # ------------------------------------------------------------------

    @staticmethod
    def main():
        """CLI entry point: argv[1]=phase_log, argv[2]=tool_log (optional)"""
        if len(sys.argv) < 2:
            print("Usage: generate_profiling_report.py <phase_log> [tool_log]")
            print("  phase_log: PHASE/AGENT 日志文件路径")
            print("  tool_log:  TOOL 日志文件路径 (默认 /tmp/study-master-tool.log)")
            sys.exit(1)

        phase_log = sys.argv[1]
        tool_log = sys.argv[2] if len(sys.argv) > 2 else "/tmp/study-master-tool.log"

        if not os.path.exists(phase_log):
            print(f"Error: phase log not found: {phase_log}")
            sys.exit(1)

        analyzer = ProfilingAnalyzer(phase_log, tool_log)
        report = analyzer.generate_report()

        # 写入报告到与 phase_log 同目录
        report_dir = os.path.dirname(os.path.abspath(phase_log))
        report_path = os.path.join(report_dir, ".profiling-report.md")

        with open(report_path, "w") as f:
            f.write(report)

        print(f"报告已生成: {report_path}")
        print(f"总行数: {len(report.splitlines())}")


if __name__ == "__main__":
    ProfilingAnalyzer.main()
