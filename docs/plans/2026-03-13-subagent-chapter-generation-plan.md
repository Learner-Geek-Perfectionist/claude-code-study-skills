# Study-Master Subagent 分章生成 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 改造 study-master skill，将章节生成从单线程串行改为 subagent 并行委派，解决长文档生成时 context 溢出触发 auto-compact 的问题。

**Architecture:** 阶段 0-4（分析+大纲）保持在主对话执行。阶段 4 末尾新增序列化步骤，将分析结果写入 `.analysis-context.md`。阶段 5 和 6-N 改为委派 Agent subagent 生成各章节。收尾阶段新增跨章节格式验证。

**Tech Stack:** Claude Code Agent tool（subagent），Markdown skill 文件

---

### Task 1: 在 analysis-guide.md 新增第 6 节"序列化分析结果"

**Files:**
- Modify: `study-master-skill/analysis-guide.md:68` (文件末尾追加)

**Step 1: 追加第 6 节内容**

在 `analysis-guide.md` 末尾追加以下内容：

```markdown
## 6. 序列化分析结果

阶段 4 完成大纲后，必须将分析结果写入 `study/<topic>/.analysis-context.md`，供 subagent 读取。

### 序列化步骤

1. **收集项目概况**：项目名称、类型、源码根路径、LSP 状态
2. **构建路径映射表**：每个模块对应的源码文件路径列表
3. **提取模块摘要**：每个模块的核心函数（函数名、文件:行号、一句话职责）、关键数据结构、模块间依赖
4. **写入文件**：使用 Write 工具生成 `.analysis-context.md`

### 控制体积原则

- 每个模块摘要 ≤ 30 行
- **只存指针不存原文**：记录文件路径+行号，不复制源码内容
- 格式规范只写关键摘要，指向完整文件让 subagent 自行 Read

### .analysis-context.md 模板

见 [document-templates.md](document-templates.md) 第 6 节。
```

**Step 2: 验证文件完整性**

Read `study-master-skill/analysis-guide.md` 确认：
- 第 6 节已正确追加
- 原有内容（第 1-5 节）未被修改
- 无乱码

**Step 3: Commit**

```bash
git add study-master-skill/analysis-guide.md
git commit -m "feat(study-master): add analysis result serialization guide (section 6)"
```

---

### Task 2: 在 document-templates.md 新增第 6 节"Analysis Context 模板"

**Files:**
- Modify: `study-master-skill/document-templates.md:65` (文件末尾追加)

**Step 1: 追加第 6 节内容**

在 `document-templates.md` 末尾追加以下内容：

````markdown
## 6. Analysis Context 模板（.analysis-context.md）

此文件由主对话在阶段 4 生成，供 subagent 读取。使用 Write 工具一次写入。

```markdown
# Analysis Context for {topic}

## 项目概况

- **项目名称**：{name}
- **类型**：{源码项目 / 协议规范 / 语言内部机制}
- **源码根路径**：{source_root}
- **LSP 状态**：{已使用 / 不可用 / 未检测到}

## 源码路径映射

| 模块 | 文件路径 |
|------|----------|
| {模块名} | {path1}, {path2}, ... |

## 学习大纲

| 章节 | 标题 | 对应模块 | 内容要点 |
|------|------|----------|----------|
| 00 | 快速导览 | 全局 | {3-5 个 bullet} |
| 01 | {标题} | {模块名} | {3-5 个 bullet} |

## 模块分析摘要

### {模块名}

**核心函数：**

| 函数名 | 位置 | 职责 |
|--------|------|------|
| {func} | {file:line} | {一句话描述} |

**关键数据结构：** {struct1}, {struct2}

**依赖关系：** 调用 → {模块A, 模块B}；被调用 ← {模块C}

**热点函数 Top 5：** {按引用次数排序}

（每个模块重复上述格式，每模块 ≤ 30 行）

## 格式规范摘要

> 完整规范请 Read {skill_path}/format-rules.md

- 源码位置：`> 📍 源码：[文件名:起始行-结束行](相对路径#L起始行)`
- 图表：必须用 Mermaid，禁止 ASCII art，节点 ≤ 20，同层 ≤ 6
- 链接文本不加反引号；无链接标识符必须加反引号
- 数学符号用 LaTeX，禁止 Unicode 数学符号
- 代码块必须指定语言标识
```
````

**Step 2: 验证文件完整性**

Read `study-master-skill/document-templates.md` 确认：
- 第 6 节已正确追加
- 原有内容（第 1-5 节）未被修改
- Markdown 嵌套代码块格式正确

**Step 3: Commit**

```bash
git add study-master-skill/document-templates.md
git commit -m "feat(study-master): add analysis context template (section 6)"
```

---

### Task 3: 改造 SKILL.md 阶段 4——新增序列化步骤

**Files:**
- Modify: `study-master-skill/SKILL.md:55-59`

**Step 1: 修改阶段 4 内容**

将 SKILL.md 中阶段 4 从：

```markdown
### 阶段 4：生成学习大纲

基于分析结果确定章节划分，识别核心模块和学习路径，生成文档目录结构。明确列出所有需要生成的章节。

> 📖 章节模板详见 [document-templates.md](document-templates.md)
```

替换为：

```markdown
### 阶段 4：生成学习大纲与序列化

基于分析结果确定章节划分，识别核心模块和学习路径，生成文档目录结构。明确列出所有需要生成的章节。

完成大纲后，将分析结果序列化写入 `study/<topic>/.analysis-context.md`，供后续 subagent 读取。

> 📖 章节模板详见 [document-templates.md](document-templates.md)
> 📖 Analysis Context 模板详见 [document-templates.md](document-templates.md) 第 6 节
> 📖 序列化指南详见 [analysis-guide.md](analysis-guide.md) 第 6 节
```

**Step 2: 验证修改**

Read `study-master-skill/SKILL.md` 确认阶段 4 已更新且不影响其他阶段。

**Step 3: Commit**

```bash
git add study-master-skill/SKILL.md
git commit -m "feat(study-master): add serialization step to phase 4"
```

---

### Task 4: 改造 SKILL.md 阶段 5——委派 subagent 生成 overview

**Files:**
- Modify: `study-master-skill/SKILL.md:61-66`

**Step 1: 替换阶段 5 内容**

将 SKILL.md 中阶段 5 从：

```markdown
### 阶段 5：生成快速导览

编写 `00-overview.md`，包含项目简介、核心概念速览、典型场景剖析（含完整执行路径追踪）、架构全景图、学习路线图。

> 📖 详见 [document-templates.md](document-templates.md) 第 1 节
> 📖 格式规范详见 [format-rules.md](format-rules.md)
```

替换为：

```markdown
### 阶段 5：委派生成快速导览

使用 Agent 工具委派一个 subagent 生成 `00-overview.md`。此章节必须先于模块章节完成（后续章节可能引用）。

**Subagent prompt 构造：**

```
你是 study-master 文档生成器。你的任务是为「{topic}」生成快速导览章节。

准备步骤：
1. Read {study_path}/.analysis-context.md — 获取项目分析上下文
2. Read {skill_path}/format-rules.md — 获取完整格式规范
3. Read {skill_path}/document-templates.md 第 1 节 — 获取快速导览模板

生成要求：
- 包含：项目简介、核心概念速览、典型场景剖析（含完整执行路径追踪）、架构全景图、学习路线图
- 遵循教科书风格原则：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
- 严格遵守 format-rules.md 的所有格式规范
- 使用分段写入：Write 创建文件（≤50 行）+ cat >> 追加（每次 ≤80 行）
- 生成完成后用 Read 验证无乱码和格式问题
- 输出到：{study_path}/00-overview.md
```

等待 subagent 完成后再进入阶段 6-N。

> 📖 快速导览模板详见 [document-templates.md](document-templates.md) 第 1 节
> 📖 格式规范详见 [format-rules.md](format-rules.md)
```

**Step 2: 验证修改**

Read `study-master-skill/SKILL.md` 确认阶段 5 已更新。

**Step 3: Commit**

```bash
git add study-master-skill/SKILL.md
git commit -m "feat(study-master): delegate overview generation to subagent (phase 5)"
```

---

### Task 5: 改造 SKILL.md 阶段 6-N——并行 subagent 生成模块章节

**Files:**
- Modify: `study-master-skill/SKILL.md:68-74`

**Step 1: 替换阶段 6-N 内容**

将 SKILL.md 中阶段 6-N 从：

```markdown
### 阶段 6-N：逐模块深度解析

**必须逐个生成所有章节，不能中途停止。** 每个章节根据内容复杂度动态调整长度，确保完整覆盖所有核心函数、关键数据结构和典型使用场景。对每个核心函数，根据 LSP 可用性选择分析路径并标注数据来源。

> 📖 函数级分析工作流详见 [analysis-guide.md](analysis-guide.md) 第 4 节
> 📖 模块章节模板详见 [document-templates.md](document-templates.md) 第 2 节
> 📖 格式规范详见 [format-rules.md](format-rules.md)
```

替换为：

```markdown
### 阶段 6-N：并行委派模块章节生成

**必须生成所有计划的章节，不能遗漏。** 使用 Agent 工具为每个模块章节委派独立的 subagent，所有模块章节**并行生成**。

**对每个模块章节构造 subagent prompt：**

```
你是 study-master 文档生成器。你的任务是为「{topic}」生成第 {N} 章：{章节标题}。

准备步骤：
1. Read {study_path}/.analysis-context.md — 获取项目分析上下文
2. Read {skill_path}/format-rules.md — 获取完整格式规范
3. Read {skill_path}/document-templates.md 第 2 节 — 获取模块深度解析模板
4. Read {skill_path}/analysis-guide.md 第 4 节 — 获取函数级分析工作流

你需要分析的模块：{模块名}
源码文件：{文件路径列表}（从 .analysis-context.md 的路径映射表获取）

生成要求：
- 遵循教科书风格原则：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
- 每个章节根据内容复杂度动态调整长度，确保完整覆盖所有核心函数、关键数据结构和典型使用场景
- 对每个核心函数，分析源码并标注数据来源（LSP/Grep）
- 严格遵守 format-rules.md 的所有格式规范
- 使用分段写入：Write 创建文件（≤50 行）+ cat >> 追加（每次 ≤80 行）
- 生成完成后用 Read 验证无乱码和格式问题
- 输出到：{study_path}/{filename}.md
```

**并行调度规则：**
- 在一条消息中使用多个 Agent 工具调用，同时启动所有模块章节的 subagent
- 每个 subagent 独立运行，互不依赖
- 等待所有 subagent 完成后再进入收尾阶段

> 📖 函数级分析工作流详见 [analysis-guide.md](analysis-guide.md) 第 4 节
> 📖 模块章节模板详见 [document-templates.md](document-templates.md) 第 2 节
> 📖 格式规范详见 [format-rules.md](format-rules.md)
```

**Step 2: 验证修改**

Read `study-master-skill/SKILL.md` 确认阶段 6-N 已更新。

**Step 3: Commit**

```bash
git add study-master-skill/SKILL.md
git commit -m "feat(study-master): parallelize module chapter generation with subagents (phase 6-N)"
```

---

### Task 6: 改造 SKILL.md 收尾阶段——新增跨章节格式验证

**Files:**
- Modify: `study-master-skill/SKILL.md:76-82`

**Step 1: 替换收尾阶段内容**

将 SKILL.md 中最后阶段从：

```markdown
### 最后阶段：整合与收尾

**进入条件**（全部满足）：已生成所有计划的章节、核心概念和关键函数都已覆盖、每个章节已通过 Read 检查无乱码。

执行：生成 `appendix-references.md`、创建 `.study-meta.json`、更新 README.md、输出最终报告。

> 📖 详见 [document-templates.md](document-templates.md) 第 5 节
```

替换为：

```markdown
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
```

**Step 2: 验证修改**

Read `study-master-skill/SKILL.md` 确认收尾阶段已更新。

**Step 3: Commit**

```bash
git add study-master-skill/SKILL.md
git commit -m "feat(study-master): add cross-chapter validation to finalization phase"
```

---

### Task 7: 更新 SKILL.md 文档结构概要表——新增 .analysis-context.md

**Files:**
- Modify: `study-master-skill/SKILL.md:84-91`

**Step 1: 更新文档结构表**

将文档结构概要表从：

```markdown
| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构图、学习路线 |
| `01-module-xxx.md` | 模块深度解析：概述、代码展示、数据结构、算法、设计决策、检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 元数据：主题、路径、LSP 状态、章节列表 |
```

替换为：

```markdown
| 文件 | 内容 |
|------|------|
| `.analysis-context.md` | 分析上下文：项目概况、路径映射、大纲、模块摘要（阶段 4 生成，供 subagent 读取） |
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构图、学习路线 |
| `01-module-xxx.md` | 模块深度解析：概述、代码展示、数据结构、算法、设计决策、检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 元数据：主题、路径、LSP 状态、章节列表 |
```

**Step 2: 验证修改**

Read `study-master-skill/SKILL.md` 确认表格已更新。

**Step 3: Commit**

```bash
git add study-master-skill/SKILL.md
git commit -m "feat(study-master): add .analysis-context.md to document structure table"
```

---

### Task 8: 重新安装 skill 并做最终验证

**Files:**
- Run: `study-master-skill/install.sh`
- Verify: `~/.claude/skills/study-master/` 下所有文件已更新

**Step 1: 运行安装脚本**

```bash
bash study-master-skill/install.sh
```

Expected: 安装成功消息，所有 4 个文件已复制。

**Step 2: 验证安装后文件一致**

```bash
diff study-master-skill/SKILL.md ~/.claude/skills/study-master/SKILL.md
diff study-master-skill/document-templates.md ~/.claude/skills/study-master/document-templates.md
diff study-master-skill/analysis-guide.md ~/.claude/skills/study-master/analysis-guide.md
```

Expected: 所有 diff 无输出（文件完全一致）。

**Step 3: Commit（如有 untracked changes from install）**

如果 install.sh 修改了 settings.json 等文件，酌情 commit：

```bash
git status
# 如有变更则 commit
```
