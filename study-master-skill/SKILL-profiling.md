---
name: study-master
description: 深入学习开源项目源码、协议规范和语言框架内部机制，生成教科书风格的学习文档
---

# Study-Master Skill（诊断模式）

> ⏱️ **[诊断模式已启用]** 本次运行将在各阶段边界自动记录时间戳到 `study/<topic>/.profiling.log`。这不会影响文档生成质量。请确保在创建 `study/<topic>/` 目录后立即记录第一个检查点。

## 概述

帮助程序员深入学习开源项目源码、协议栈实现（如 TCP/IP、HTTP）、特定编程语言或框架的内部机制。生成深度解析型学习文档，采用教科书风格，文档规模根据主题复杂度动态调整。支持自动检测并使用 LSP 增强代码分析。

## 强制目录结构

- `src/` — 源码目录
- `docs/` — 协议规范文档
- `study/<topic>/` — 学习文档输出目录（自动创建）

**规则**：至少 `src/` 或 `docs/` 之一必须存在。两者都不存在时拒绝执行并提示用户调整目录结构。

## 教科书风格原则

生成的文档必须遵循渐进式知识展开：

1. **先整体后局部**：先展示模块在系统中的位置，再深入细节
2. **先接口后实现**：先讲清楚"做什么"，再讲"怎么做"
3. **先主流程后边界**：先追踪正常执行路径，再分析错误处理
4. **先概念后代码**：先用自然语言解释设计思想，再展示代码

## 工作流程

### Phase 1：源码加载与分析

> ⏱️ **[诊断]** Phase 1 开始，创建 `study/<topic>/` 目录后立即运行：
> ```
> Bash: echo "PHASE|phase-1-analysis|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```

#### 1.1 源码定位与验证

1. 检查 `src/` 或 `docs/` 目录是否存在
2. 按优先级查找：`src/<topic>/` → `src/*<topic>*/` → `docs/<topic>/` → `docs/*<topic>*/` → `./<topic>/`（不区分大小写，支持部分匹配）
3. 找到多个候选时列出让用户选择
4. 输出目录：`study/<topic>/`

#### 1.2 LSP 环境检测

C/C++ 项目自动检测 LSP 可用性，其他语言跳过。

> 📖 详见 [analysis-guide.md](analysis-guide.md) 第 1 节

#### 1.3 主题识别与准备

解析 `<topic>` 参数，判断类型（项目/协议/语言内部机制），确定源码位置，创建 `study/<topic>/`。

#### 1.4 全源码深度分析

利用 1M 上下文窗口，执行全源码深度分析：

1. **源码加载**：Read 项目所有核心源文件到上下文中（1M 上下文可加载约 30000 行代码）
2. **结构分析**：根据 LSP 可用性选择分析方法，识别核心模块、热点函数和模块依赖关系
3. **深度解读**：在拥有全部源码的上下文中完成以下分析：
   - 每个模块的设计意图和职责边界
   - 关键算法和核心函数的逻辑解读（不只是签名，要理解设计动机）
   - 模块间的耦合关系和数据流
   - 关键设计决策和 tradeoff 分析
4. **热点函数深度分析**：对每个核心函数，阅读完整实现，理解内部逻辑、错误处理策略和与其他模块的交互方式

> 📖 分析方法详见 [analysis-guide.md](analysis-guide.md) 第 2-4 节

#### 1.5 确定章节大纲与交叉引用准备

基于深度分析，确定章节划分和学习路径，明确列出所有需要生成的章节。

**必须完成以下准备（结论保留在上下文中，不写文件）：**

1. **计算 `source_path_prefix`**：统计 `study/<topic>/` 相对于项目根的目录层数，每层一个 `../`。例如 `study/redis/` 为 2 层 → `../../`。所有源码路径必须加上此前缀。
2. **预计算「交叉引用锚点映射」表**：根据学习大纲中各章节的预期标题结构，为每个可能被其他章节引用的术语（结构体名、关键函数名）生成 GFM 锚点映射。后续生成每个章节时直接查表使用。
3. **为每个模块准备「分析摘要」**（供 Phase 2.2 并行 agent 使用）：利用 Phase 1.4 的深度分析结论，为每个模块生成精简摘要，包含：
   - 设计意图（该模块为什么存在，解决什么核心问题）
   - 核心函数清单（3-5 个最关键的函数名及其职责，含文件:行号）
   - 关键数据结构（核心结构体及其角色）
   - 与其他模块的关系（调用/被调用关系、数据流方向）
   - 设计决策（1-2 个关键 tradeoff）
   - 关键代码片段（该模块最核心的 2-3 段代码，直接从上下文中提取嵌入）

> ⏱️ **[诊断]** Phase 1 结束（大纲和模块摘要已准备），运行：
> ```
> Bash: echo "PHASE|phase-1-analysis|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

### Phase 2：混合策略生成文档

> ⏱️ **[诊断]** Phase 2 开始，运行：
> ```
> Bash: echo "PHASE|phase-2-generate|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```

**采用"串行奠基 + 并行加速"的混合生成策略。**

```
串行阶段：00-overview.md → 01-xxx.md → 02-xxx.md（主对话直接生成，建立风格基线）
并行阶段：03-xxx.md ~ NN-xxx.md（Agent 工具并行生成，嵌入分析摘要+代码片段）
收尾：appendix-references.md（主对话生成）
```

#### 2.1 串行生成：Overview + 前 2 个模块章节

主对话直接使用 Write 工具依次生成以下章节：

> ⏱️ **[诊断]** 每个串行章节生成前，运行：
> ```
> Bash: echo "PHASE|generate-{章节文件名}|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```
> 每个串行章节生成后，运行：
> ```
> Bash: echo "PHASE|generate-{章节文件名}|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

1. **`00-overview.md`**（快速导览）
2. **`01-xxx.md`**（第 1 个模块章节）
3. **`02-xxx.md`**（第 2 个模块章节）

串行生成的目的：
- 在上下文中建立**写作风格基线**和**交叉引用模式**
- 验证 `source_path_prefix` 和锚点映射的正确性

Overview 生成要求：
- 包含：项目简介、核心概念速览、典型场景剖析（含完整执行路径追踪）、架构全景图、学习路线图

模块章节生成要求：
- 遵循教科书风格原则：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
- 使用多层次代码展示：调用关系图（Mermaid）→ 伪代码 → 真实代码片段 → 实现细节
- 每个章节根据内容复杂度动态调整长度
- 严格遵守 [format-rules.md](format-rules.md) 的所有格式规范
- 源码链接路径前缀统一使用 `source_path_prefix`
- 交叉引用其他章节时，从锚点映射表查找锚点，格式为 `[术语](./文件.md#锚点)`

> 📖 快速导览模板详见 [document-templates.md](document-templates.md) 第 1 节
> 📖 模块章节模板详见 [document-templates.md](document-templates.md) 第 2 节

#### 2.2 并行生成：剩余模块章节

使用 Agent 工具为剩余每个模块章节委派独立 agent，**在一条消息中同时启动所有 agent**。

> ⏱️ **[诊断]** 并行 agent 批次开始——在派发所有 agent 之前，**逐个**运行 start 检查点（每个章节一条）：
> ```
> Bash: echo "PHASE|generate-{章节文件名}|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```
> 所有 agent 返回后，**逐个**运行 end 检查点（每个章节一条）：
> ```
> Bash: echo "PHASE|generate-{章节文件名}|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```
> ⚠️ **重要**：必须为**每一个**并行章节都记录 start 和 end，不能遗漏任何章节。

**核心原则：把分析结论直接喂给 agent，不让 agent 自己从零分析。**

每个 agent 的 prompt 必须包含以下信息（全部直接嵌入 prompt，不依赖外部文件）：

1. 项目全局架构概述（2-3 句话）
2. **该模块的分析摘要**（Phase 1.5 准备的，包含设计意图、核心函数、数据结构、模块关系、设计决策）
3. **该模块的关键代码片段**（Phase 1.5 从源码中提取的 2-3 段核心代码，直接嵌入）
4. `source_path_prefix` 的值
5. 交叉引用锚点映射表（完整表格）
6. 该模块的源码文件路径列表（供 agent 需要更多细节时 Read）
7. 格式规范要点摘要
8. 章节编号、文件名、输出路径

**并行调度规则：**
- 在一条消息中使用多个 Agent 工具调用，同时启动所有剩余章节
- 每个 agent 已有分析摘要和代码片段，仅在需要更多细节时 Read 源文件
- 等待所有 agent 完成后再进入 Phase 2.3

> 📖 格式规范详见 [format-rules.md](format-rules.md)

#### 2.3 生成参考索引

> ⏱️ **[诊断]** 开始生成 appendix，运行：
> ```
> Bash: echo "PHASE|generate-appendix|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```

所有章节完成后，主对话生成 `appendix-references.md`（参考资料索引）。

> ⏱️ **[诊断]** appendix 生成完成，运行：
> ```
> Bash: echo "PHASE|generate-appendix|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

> ⏱️ **[诊断]** Phase 2 结束（所有章节已生成），运行：
> ```
> Bash: echo "PHASE|phase-2-generate|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

### Phase 3：全量格式检查与收尾

> ⏱️ **[诊断]** Phase 3 开始，运行：
> ```
> Bash: echo "PHASE|phase-3-finalize|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```

**进入条件**：所有计划章节的文件已存在于 `study/<topic>/`。

#### 3.1 全量格式检查

> ⏱️ **[诊断]** 格式检查开始，运行：
> ```
> Bash: echo "PHASE|format-check|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```

逐文件 Read 检查每个生成的章节：
- 格式合规性（链接格式、Mermaid 图表、反引号规则、LaTeX 数学符号）
- 无乱码（U+FFFD 等）
- 源码引用路径正确（使用 `source_path_prefix`）
- 交叉引用锚点正确（与预计算的锚点映射一致）
- 发现问题时直接用 Edit 修正

> ⏱️ **[诊断]** 格式检查结束，运行：
> ```
> Bash: echo "PHASE|format-check|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

#### 3.2 整合收尾

> ⏱️ **[诊断]** 整合收尾开始，运行：
> ```
> Bash: echo "PHASE|finalize|start|$(date +%s)" >> study/<topic>/.profiling.log
> ```

1. 创建 `.study-meta.json`（格式见 [document-templates.md](document-templates.md) 第 4 节）
2. 输出最终报告

> 📖 收尾清单详见 [document-templates.md](document-templates.md) 第 5 节

> ⏱️ **[诊断]** 整合收尾结束，运行：
> ```
> Bash: echo "PHASE|finalize|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

> ⏱️ **[诊断]** Phase 3 结束，运行：
> ```
> Bash: echo "PHASE|phase-3-finalize|end|$(date +%s)" >> study/<topic>/.profiling.log
> ```

> ⏱️ **[诊断]** 全部完成！生成诊断报告：
> ```
> Bash: python3 ~/.claude/hooks/generate_profiling_report.py study/<topic>/.profiling.log /tmp/study-master-tool.log
> ```

## 文档结构概要

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构图、学习路线 |
| `01-module-xxx.md` | 模块深度解析：概述、代码展示、数据结构、算法、设计决策、检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 元数据：主题、路径、LSP 状态、章节列表 |

## 质量控制

- 每个章节根据复杂度动态调整长度，确保内容完整
- 生成后逐文件用 Read 检查乱码，发现 U+FFFD 或格式问题立即修正
- 所有源码引用必须有正确的超链接，验证 LSP 数据准确性

> 📖 格式标准详见 [format-rules.md](format-rules.md)，PostToolUse hook 自动验证格式合规
> 📖 输出规则详见 [document-templates.md](document-templates.md) 第 3 节
