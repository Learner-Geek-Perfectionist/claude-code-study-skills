# Study-Master 性能诊断系统设计

**日期：** 2026-03-15
**状态：** 已批准
**目标：** 在不影响文档质量的前提下，为 study-master skill 建立一次性性能诊断机制，精确定位各阶段耗时瓶颈，为后续优化提供数据支撑

## 背景

Study-master 当前执行一次中型项目（5000-15000 行代码）需约 20 分钟。用户反馈速度不够快且担心质量。需要精确数据来判断瓶颈所在，而不是凭理论猜测。

### 理论瓶颈分析（待诊断数据验证）

| 可能瓶颈 | 推测原因 | 严重度 |
|---------|---------|--------|
| 阶段 3（全源码深度分析） | 主 dialog 串行推理，大量 Read + LLM 分析 | 高 |
| 阶段 4（富分析报告序列化） | 大量 token 生成写入 .analysis-context.md | 高 |
| 阶段 5（overview 串行等待） | 阻塞并行章节，subagent 要 Read 大文件 | 中 |
| 最后阶段（6步后处理） | 串行 Read 所有章节 + 多次 Edit | 中-高 |
| 重复 I/O | .analysis-context.md 被每个 subagent 重复 Read | 低-中 |

## 方案选择

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（选定）** | 诊断先行：注入 profiling 后跑一次，基于数据优化 | 精确诊断，不会误判 | 需要跑一次带诊断的 skill |
| B | 理论分析直接优化 | 快 | 实际瓶颈可能与理论不同 |
| C | 只加时间戳不加日志 | 轻量 | 信息不够详细 |

## 诊断架构

### 两层数据采集

```
层 1：阶段级检查点                  层 2：工具级日志
(SKILL.md 注入)                   (PostToolUse hook)
     │                                  │
     ▼                                  ▼
┌─────────────────────────────────────────────┐
│         study/<topic>/.profiling.log        │
│  PHASE|stage-3|start|1710489600            │
│  TOOL|Read|src/module.c|1710489601         │
│  TOOL|Read|src/core.h|1710489602           │
│  PHASE|stage-3|end|1710489900              │
│  ...                                        │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│    generate_profiling_report.py 解析        │
│    → .profiling-report.md                   │
└─────────────────────────────────────────────┘
```

### 层 1：阶段级检查点

在 SKILL.md 的每个阶段边界注入 `date +%s` 检查点。

**检查点位置：**

| ID | 位置 | 记录内容 |
|----|------|---------|
| P0 | 阶段 0 开始 | `PHASE\|stage-0-2\|start` |
| P1 | 阶段 2 结束 | `PHASE\|stage-0-2\|end` |
| P2 | 阶段 3 开始 | `PHASE\|stage-3-analysis\|start` |
| P3 | 阶段 3 结束 | `PHASE\|stage-3-analysis\|end` |
| P4 | 阶段 4 开始 | `PHASE\|stage-4-serialize\|start` |
| P5 | 阶段 4 结束 | `PHASE\|stage-4-serialize\|end` |
| P6 | 阶段 5 开始 | `PHASE\|stage-5-overview\|start` |
| P6a | Agent 调用前 | `AGENT\|overview\|start` |
| P6b | Agent 返回后 | `AGENT\|overview\|end` |
| P7 | 阶段 5 结束 | `PHASE\|stage-5-overview\|end` |
| P8 | 阶段 6-N 开始 | `PHASE\|stage-6N-chapters\|start` |
| P8a-n | 每个 Agent 前 | `AGENT\|{chapter}\|start` |
| P8b-n | 每个 Agent 后 | `AGENT\|{chapter}\|end` |
| P9 | 阶段 6-N 结束 | `PHASE\|stage-6N-chapters\|end` |
| P10 | 最后阶段开始 | `PHASE\|final\|start` |
| P10a-f | 每个步骤(1-6)前后 | `PHASE\|final-step-{N}\|start/end` |
| P11 | 最后阶段结束 | `PHASE\|final\|end` |

**注入格式：** 在 SKILL.md 对应阶段描述的开头添加 blockquote 指令：

```markdown
> ⏱️ **[诊断模式]** 此阶段开始前运行：
> `Bash: echo "PHASE|stage-3-analysis|start|$(date +%s)" >> {study_path}/.profiling.log`
```

### 层 2：工具级日志（PostToolUse Hook）

创建 `hooks/profiling_hook.sh`，在每次工具调用后记录。

**触发条件：** 只在路径包含 `study/` 或 `src/` 时记录（避免无关噪声）。

**记录格式：**
```
TOOL|<tool_name>|<file_path>|<timestamp>
```

**Hook 配置（临时注册到 settings.json）：**
```json
{
  "name": "study-master-profiling",
  "event": "PostToolUse",
  "command": "~/.claude/hooks/profiling_hook.sh"
}
```

### 层 3：报告生成

创建 `hooks/generate_profiling_report.py`，解析 `.profiling.log` 生成 `.profiling-report.md`。

**报告内容：**

1. **总耗时概览**
   - 总时间、各阶段百分比

2. **阶段耗时排行**
   ```
   阶段                    耗时      占比    状态
   stage-3-analysis       420s     35%     🔴 瓶颈
   final                  300s     25%     🔴 瓶颈
   stage-4-serialize      180s     15%     🟡 关注
   stage-5-overview       120s     10%     🟢 正常
   stage-6N-chapters      120s     10%     🟢 正常
   stage-0-2               60s      5%     🟢 正常
   ```

3. **工具调用统计**
   - 按工具类型：Read N 次, Write N 次, Agent N 次, Edit N 次
   - 按阶段分布：哪个阶段调用最多工具

4. **Subagent 并行度分析**
   - 各 subagent 独立耗时
   - 并行效率 = max(单个subagent耗时) / sum(所有subagent耗时)
   - 识别"长尾" subagent（某个章节生成特别慢）

5. **瓶颈诊断结论**
   - 自动标注 > 2 分钟的阶段为"瓶颈"
   - 给出初步优化建议方向

## 实现文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `SKILL-profiling.md` | 新建（临时） | 带检查点的诊断版 SKILL.md |
| `hooks/profiling_hook.sh` | 新建（临时） | PostToolUse 工具调用日志 |
| `hooks/generate_profiling_report.py` | 新建（临时） | 报告生成脚本 |

## 使用流程

1. **安装诊断版本**：用 `SKILL-profiling.md` 临时替换 `SKILL.md`，注册 profiling hook
2. **运行 skill**：`/study-master <topic>`，正常执行
3. **生成报告**：skill 完成后运行 `python3 hooks/generate_profiling_report.py study/<topic>/.profiling.log`
4. **分析报告**：查看 `.profiling-report.md`，识别瓶颈
5. **清理**：恢复原始 `SKILL.md`，删除 profiling hook，保留报告供参考

## 诊断后的预期产出

基于诊断数据，我们将能够：
- 精确知道每个阶段的实际耗时（而非猜测）
- 判断串行阶段（3/4/最后阶段）是否真的是主要瓶颈
- 量化 subagent 并行效率
- 为后续的针对性优化提供数据依据
