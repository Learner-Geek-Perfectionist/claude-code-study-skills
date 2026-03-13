---
name: study-master
description: 深入学习开源项目源码、协议规范和语言框架内部机制，生成教科书风格的学习文档
---

# Study-Master Skill

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

### 阶段 0：源码定位与验证

1. 检查 `src/` 或 `docs/` 目录是否存在
2. 如果用户指定了 `--source` 参数，直接使用该路径
3. 否则按优先级查找：`src/<topic>/` → `src/*<topic>*/` → `docs/<topic>/` → `docs/*<topic>*/` → `./<topic>/`（不区分大小写，支持部分匹配）
4. 找到多个候选时列出让用户选择
5. 输出目录：`study/<topic>/`

### 阶段 1：LSP 环境检测

C/C++ 项目自动检测 LSP 可用性，其他语言跳过。

> 📖 详见 [analysis-guide.md](analysis-guide.md) 第 1 节

### 阶段 2：主题识别与准备

解析 `<topic>` 参数，判断类型（项目/协议/语言内部机制），确定源码位置，创建 `study/<topic>/`。

### 阶段 3：项目结构分析

根据 LSP 可用性选择分析方法，识别核心模块、热点函数和模块依赖关系。

> 📖 详见 [analysis-guide.md](analysis-guide.md) 第 2-3 节

### 阶段 4：生成学习大纲与序列化

基于分析结果确定章节划分，识别核心模块和学习路径，生成文档目录结构。明确列出所有需要生成的章节。

完成大纲后，将分析结果序列化写入 `study/<topic>/.analysis-context.md`，供后续 subagent 读取。

> 📖 章节模板详见 [document-templates.md](document-templates.md)
> 📖 Analysis Context 模板详见 [document-templates.md](document-templates.md) 第 6 节
> 📖 序列化指南详见 [analysis-guide.md](analysis-guide.md) 第 6 节

### 阶段 5：委派生成快速导览

使用 Agent 工具委派一个 subagent 生成 `00-overview.md`。此章节必须先于模块章节完成（后续章节可能引用）。

**Subagent prompt 构造：**

> 你是 study-master 文档生成器。你的任务是为「{topic}」生成快速导览章节。
>
> 准备步骤：
> 1. Read {study_path}/.analysis-context.md — 获取项目分析上下文
> 2. Read {skill_path}/format-rules.md — 获取完整格式规范
> 3. Read {skill_path}/document-templates.md 第 1 节 — 获取快速导览模板
>
> 生成要求：
> - 包含：项目简介、核心概念速览、典型场景剖析（含完整执行路径追踪）、架构全景图、学习路线图
> - 遵循教科书风格原则：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
> - 严格遵守 format-rules.md 的所有格式规范
> - 使用分段写入：Write 创建文件（≤50 行）+ cat >> 追加（每次 ≤80 行）
> - 生成完成后用 Read 验证无乱码和格式问题
> - 输出到：{study_path}/00-overview.md

等待 subagent 完成后再进入阶段 6-N。

> 📖 快速导览模板详见 [document-templates.md](document-templates.md) 第 1 节
> 📖 格式规范详见 [format-rules.md](format-rules.md)

### 阶段 6-N：并行委派模块章节生成

**必须生成所有计划的章节，不能遗漏。** 使用 Agent 工具为每个模块章节委派独立的 subagent，所有模块章节**并行生成**。

**对每个模块章节构造 subagent prompt：**

> 你是 study-master 文档生成器。你的任务是为「{topic}」生成第 {N} 章：{章节标题}。
>
> 准备步骤：
> 1. Read {study_path}/.analysis-context.md — 获取项目分析上下文
> 2. Read {skill_path}/format-rules.md — 获取完整格式规范
> 3. Read {skill_path}/document-templates.md 第 2 节 — 获取模块深度解析模板
> 4. Read {skill_path}/analysis-guide.md 第 4 节 — 获取函数级分析工作流
>
> 你需要分析的模块：{模块名}
> 源码文件：{文件路径列表}（从 .analysis-context.md 的路径映射表获取）
>
> 生成要求：
> - 遵循教科书风格原则：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
> - 每个章节根据内容复杂度动态调整长度，确保完整覆盖所有核心函数、关键数据结构和典型使用场景
> - 对每个核心函数，分析源码并标注数据来源（LSP/Grep）
> - 严格遵守 format-rules.md 的所有格式规范
> - 使用分段写入：Write 创建文件（≤50 行）+ cat >> 追加（每次 ≤80 行）
> - 生成完成后用 Read 验证无乱码和格式问题
> - 输出到：{study_path}/{filename}.md

**并行调度规则：**
- 在一条消息中使用多个 Agent 工具调用，同时启动所有模块章节的 subagent
- 每个 subagent 独立运行，互不依赖
- 等待所有 subagent 完成后再进入收尾阶段

> 📖 函数级分析工作流详见 [analysis-guide.md](analysis-guide.md) 第 4 节
> 📖 模块章节模板详见 [document-templates.md](document-templates.md) 第 2 节
> 📖 格式规范详见 [format-rules.md](format-rules.md)

### 最后阶段：验证、整合与收尾

**进入条件**（全部满足）：所有 subagent 已完成、所有计划章节的文件已存在于 `study/<topic>/`。

**步骤 1：跨章节格式验证**

逐文件 Read 检查每个 subagent 生成的章节：
- 格式合规性（链接格式、Mermaid 图表、反引号规则、LaTeX 数学符号）
- 无乱码（U+FFFD 等）
- 源码引用路径正确
- 发现问题时直接修正，不需要重新委派 subagent

**步骤 2：整合**

执行：生成 `appendix-references.md`、创建 `.study-meta.json`、更新 README.md、输出最终报告。

> 📖 详见 [document-templates.md](document-templates.md) 第 5 节

## 文档结构概要

| 文件 | 内容 |
|------|------|
| `.analysis-context.md` | 分析上下文：项目概况、路径映射、大纲、模块摘要（阶段 4 生成，供 subagent 读取） |
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构图、学习路线 |
| `01-module-xxx.md` | 模块深度解析：概述、代码展示、数据结构、算法、设计决策、检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 元数据：主题、路径、LSP 状态、章节列表 |

## 质量控制

- 每个章节根据复杂度动态调整长度，确保内容完整
- 生成后逐文件用 Read 检查乱码，发现 U+FFFD 或格式问题立即修正
- 所有源码引用必须有正确的超链接，验证 LSP 数据准确性

> 📖 格式标准详见 [format-rules.md](format-rules.md)，PostToolUse hook 自动验证格式合规
> 📖 分段输出规则详见 [document-templates.md](document-templates.md) 第 3 节
