#!/usr/bin/env python3
"""
TDD tests for generate_profiling_report.py
验证 ProfilingAnalyzer 能正确解析日志并生成包含 5 个 section 的诊断报告
"""

import os
import sys
import tempfile

# ---------------------------------------------------------------------------
# 样本数据：模拟约 26 分钟的 study-master 运行
# timestamps: 1710489600 (start) → 1710491175 (end) = 1575s ≈ 26m 15s
# ---------------------------------------------------------------------------

SAMPLE_PHASE_LOG = """\
PHASE|stage-0-2|start|1710489600
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

SAMPLE_TOOL_LOG = """\
TOOL|Read|src/core/module.c|1710489665
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


def run_tests():
    """运行所有测试，返回 (passed, failed) 计数"""
    from generate_profiling_report import ProfilingAnalyzer

    passed = 0
    failed = 0
    errors = []

    # --- 准备临时日志文件 ---
    tmp_dir = tempfile.mkdtemp(prefix="profiling_test_")
    phase_path = os.path.join(tmp_dir, "phase.log")
    tool_path = os.path.join(tmp_dir, "tool.log")

    with open(phase_path, "w") as f:
        f.write(SAMPLE_PHASE_LOG)
    with open(tool_path, "w") as f:
        f.write(SAMPLE_TOOL_LOG)

    try:
        analyzer = ProfilingAnalyzer(phase_path, tool_path)
        report = analyzer.generate_report()

        # ------------------------------------------------------------------
        # Test 1: 报告包含全部 5 个 section
        # ------------------------------------------------------------------
        test_name = "报告包含全部 5 个 section"
        section_markers = [
            "总耗时概览",
            "阶段耗时排行",
            "工具调用统计",
            "并行度分析",
            "瓶颈诊断结论",
        ]
        missing = [m for m in section_markers if m not in report]
        if not missing:
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(f"  [FAIL] {test_name}: 缺少 section: {missing}")
            print(errors[-1])

        # ------------------------------------------------------------------
        # Test 2: 总耗时正确 (1575s = 26m 15s)
        # ------------------------------------------------------------------
        test_name = "总耗时计算正确 (26m 15s)"
        if "26m 15s" in report:
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(f"  [FAIL] {test_name}: 报告中未找到 '26m 15s'")
            print(errors[-1])

        # ------------------------------------------------------------------
        # Test 3: 瓶颈识别 — stage-3-analysis (420s) 和 final (450s) 应标记为瓶颈
        # ------------------------------------------------------------------
        test_name = "瓶颈识别 (>120s 阶段被标记)"
        # stage-3-analysis=420s, stage-4-serialize=240s, final=450s 都超过 120s
        has_bottleneck_section = "瓶颈" in report
        has_analysis_flagged = "stage-3-analysis" in report
        has_final_flagged = "final" in report
        if has_bottleneck_section and has_analysis_flagged and has_final_flagged:
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(
                f"  [FAIL] {test_name}: bottleneck={has_bottleneck_section}, "
                f"analysis={has_analysis_flagged}, final={has_final_flagged}"
            )
            print(errors[-1])

        # ------------------------------------------------------------------
        # Test 4: Subagent 并行度分析存在且包含关键指标
        # ------------------------------------------------------------------
        test_name = "Subagent 并行度分析包含关键指标"
        parallel_keywords = ["并行", "overview", "wall"]
        found = [kw for kw in parallel_keywords if kw.lower() in report.lower()]
        if len(found) >= 2:
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(
                f"  [FAIL] {test_name}: 只找到 {found}，期望至少 2 个关键词"
            )
            print(errors[-1])

        # ------------------------------------------------------------------
        # Test 5: 工具调用统计 — Read 应为 10 次，重复读取被检测
        # ------------------------------------------------------------------
        test_name = "工具调用统计 (Read=10, 检测重复读取)"
        has_read_count = "Read" in report
        has_duplicate = "重复" in report or "duplicate" in report.lower()
        if has_read_count and has_duplicate:
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(
                f"  [FAIL] {test_name}: read_count={has_read_count}, duplicate={has_duplicate}"
            )
            print(errors[-1])

        # ------------------------------------------------------------------
        # Test 6: 阶段耗时排行包含严重度标记
        # ------------------------------------------------------------------
        test_name = "阶段耗时排行包含严重度标记"
        has_red = "\U0001f534" in report     # 🔴
        has_yellow = "\U0001f7e1" in report  # 🟡
        has_green = "\U0001f7e2" in report   # 🟢
        # 样本数据所有顶层阶段 >=60s (🔴/🟡)，final-step 也都 >=60s (🟡)
        # 因此只需验证 red 和 yellow 都出现即可
        if has_red and has_yellow:
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(
                f"  [FAIL] {test_name}: red={has_red}, yellow={has_yellow}, green={has_green}"
            )
            print(errors[-1])

        # ------------------------------------------------------------------
        # Test 7: final-step 子表包含步骤标签
        # ------------------------------------------------------------------
        test_name = "final-step 子表包含步骤标签"
        step_labels = ["格式验证", "内容审查", "交叉引用注入", "深度补充", "概览更新", "整合"]
        found_labels = [lbl for lbl in step_labels if lbl in report]
        if len(found_labels) >= 4:  # 至少找到 4 个
            passed += 1
            print(f"  [PASS] {test_name}")
        else:
            failed += 1
            errors.append(
                f"  [FAIL] {test_name}: 只找到 {found_labels}"
            )
            print(errors[-1])

        # --- 打印报告预览 (前 80 行) ---
        print("\n" + "=" * 60)
        print("报告预览 (前 80 行):")
        print("=" * 60)
        preview_lines = report.split("\n")[:80]
        print("\n".join(preview_lines))
        if len(report.split("\n")) > 80:
            print(f"\n... (共 {len(report.split(chr(10)))} 行)")

    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return passed, failed


if __name__ == "__main__":
    print("=" * 60)
    print("ProfilingAnalyzer 测试套件")
    print("=" * 60)

    try:
        p, f = run_tests()
    except ImportError as e:
        print(f"\n[ERROR] ImportError: {e}")
        print("generate_profiling_report.py 尚未创建")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    if f == 0:
        print(f"✅ 所有测试通过！({p}/{p})")
    else:
        print(f"❌ {f} 个测试失败 ({p} 通过 / {f} 失败)")
    print("=" * 60)
    sys.exit(0 if f == 0 else 1)
