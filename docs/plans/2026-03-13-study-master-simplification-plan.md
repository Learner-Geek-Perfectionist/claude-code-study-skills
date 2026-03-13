# Study-Master 模块化精简 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 SKILL.md 从 333 行精简至 ~100-120 行，通过模块化拆分减少初始上下文占用，同时保持 Markdown 生成质量不变。

**Architecture:** 将当前单一的 SKILL.md 拆分为核心文件（工作流骨架）+ 2 个按需加载的参考文件（analysis-guide.md、document-templates.md），加上已有的 format-rules.md。格式质量由 hook 自动保障。

**Tech Stack:** Markdown 技能文件、Bash 安装脚本、Python 验证脚本

---

### Task 1: 创建 analysis-guide.md

**Files:**
- Create: `study-master-skill/analysis-guide.md`

**Step 1: 从当前 SKILL.md 提取 LSP 和分析方法内容**

阅读 `study-master-skill/SKILL.md`，提取以下内容：
- 阶段 1（L88-95）：LSP 环境检测
- 阶段 3（L107-124）：项目结构分析方法表 + LSP 深度分析
- 阶段 6-N（L158-188）：函数级分析工作流（LSP/Grep 双路径）
- 可视化类型选择指南（L262-271）

**Step 2: 编写 analysis-guide.md**

将提取的内容整合去重，写入新文件。关键要求：
- 合并 Phase 3 和 Phase 6-N 的 LSP 双路径为**统一的方法对照表**
- LSP 环境检测：查找 compile_commands.json 的位置列表、LSP 测试命令、状态记录
- 函数级分析：统一为"LSP 可用时用 X，否则用 Y"的条件格式
- 可视化选择：保持表格形式
- 目标：~60-70 行

```markdown
# 源码分析方法指南

本文件包含 study-master 的源码分析技术细节，在工作流阶段 1/3/6-N 中按需 Read。

## 1. LSP 环境检测

**仅 C/C++ 项目需要检测**，其他语言跳过。

检测步骤：
1. 查找 `compile_commands.json`：源码根目录 → 上级目录 → build/ 目录
2. 测试 LSP：`LSP documentSymbol <file> line:1 char:1`
3. 记录结果：✓ LSP 可用 / ✗ LSP 不可用

## 2. 分析方法对照表

根据 LSP 可用性选择分析方法：

| 分析任务 | LSP 可用 | LSP 不可用 |
|---------|---------|-----------|
| 获取符号列表 | `LSP documentSymbol` | Grep 搜索函数定义 |
| 识别核心 API | `LSP findReferences` 统计引用次数 | 基于文件位置和命名推断 |
| 构建模块依赖 | 基于符号的文件位置分组 | Glob/Grep 扫描 include/import |
| 获取函数签名 | `LSP hover <file> line char` | 从头文件/声明处提取 |
| 查找调用关系 | `LSP findReferences` | Grep 搜索函数名 |
| 构建调用树 | `prepareCallHierarchy` + `incomingCalls` + `outgoingCalls` | 手动推断 |

## 3. LSP 深度分析流程

当 LSP 可用时，执行以下深度分析：

1. **热点函数识别**：按 `findReferences` 引用次数排序，找出最核心的函数
2. **模块耦合度分析**：统计跨文件引用，识别高耦合模块
3. **API 稳定性评估**：公共 API 被多少文件调用（引用广度）
4. **调用深度分析**：用 `prepareCallHierarchy` + `incomingCalls` + `outgoingCalls` 构建完整调用树

## 4. 函数级分析工作流

对每个核心函数，按以下步骤分析：

1. **获取签名**：LSP hover / 头文件提取
2. **查找调用关系**：LSP findReferences / Grep
3. **构建调用树**：LSP callHierarchy / 手动推断
4. **生成执行路径追踪**：
   - Mermaid sequenceDiagram 展示调用顺序
   - 标注参数值、返回值、状态变化
   - 区分：正常路径、错误处理、边界条件
5. **生成文档**，标注数据来源（LSP hover / Grep / 头文件）

## 5. 可视化类型选择

| 内容类型 | Mermaid 图表 | 示例场景 |
|---------|-------------|---------|
| 模块依赖、调用关系 | `graph TD/LR` | 函数调用链、模块架构 |
| 时序交互 | `sequenceDiagram` | 多模块协作、执行路径追踪 |
| 状态转换 | `stateDiagram-v2` | 对象生命周期、协议状态机 |
| 数据结构 | `classDiagram` | 结构体成员、类层次 |
```

**Step 3: 验证文件**

Run: `wc -l study-master-skill/analysis-guide.md`
Expected: 60-70 行

检查要点：
- 所有 LSP 分析方法都已包含
- 双路径合并为统一对照表，无重复
- 可视化选择指南完整

**Step 4: Commit**

```bash
git add study-master-skill/analysis-guide.md
git commit -m "feat: create analysis-guide.md for study-master modular split"
```

---

### Task 2: 创建 document-templates.md

**Files:**
- Create: `study-master-skill/document-templates.md`

**Step 1: 从当前 SKILL.md 提取文档模板内容**

阅读 `study-master-skill/SKILL.md`，提取以下内容：
- 快速导览章节结构（L215-221）
- 模块深度解析章节结构（L223-240）
- 分段输出规则（L283-306）
- 元数据格式（L310-332）
- 收尾步骤（L192-209）中的具体格式

**Step 2: 编写 document-templates.md**

```markdown
# 文档生成模板

本文件包含 study-master 的文档模板和操作规则，在工作流阶段 4/5/6-N 和收尾阶段按需 Read。

## 1. 快速导览章节（00-overview.md）

必须包含以下 5 个部分：

1. **项目/协议简介**：背景、目标、核心特性
2. **核心概念速览**：关键术语、设计理念
3. **典型场景剖析**：选择 1-2 个典型场景，追踪完整执行路径（调用栈、数据流、时序图、状态转换）
4. **架构全景图**：Mermaid 图展示系统整体结构
5. **学习路线图**：建议学习顺序，导航后续章节

## 2. 模块深度解析章节（01-module-xxx.md）

每个模块文档包含以下 6 个部分：

1. **模块概述**：模块职责、在系统中的位置、对外接口
2. **多层次代码展示**：
   - 调用关系图（Mermaid）→ 伪代码 → 真实代码片段 → 实现细节
3. **数据结构深度解析**：结构定义、字段含义、生命周期
4. **关键算法剖析**：算法思想、时间复杂度、边界处理
5. **设计决策分析**：为什么这样设计、权衡考虑、替代方案
6. **学习检查点**：
   - 📝 本章小结（3-5 个要点）
   - 🤔 思考题（2-3 个引导性问题）

## 3. 分段输出规则

**必须分段写入文件，避免一次输出过长内容**：

- 初始文件创建：使用 Write 工具，内容 ≤ 50 行
- 后续追加：使用 `cat >>` 命令，每次 ≤ 80 行
- 大章节：分 3-5 次追加完成

## 4. 元数据格式（.study-meta.json）

必须包含以下字段：

- `topic`：学习主题名
- `source_path`：源码路径
- `generated_at`：生成时间戳
- `lsp_enabled`：是否使用了 LSP
- `lsp_status`："已使用" / "不可用" / "未检测到"
- `lsp_calls`：各 LSP 操作调用次数（documentSymbol, hover, findReferences, outgoingCalls, total）
- `symbols_analyzed`：分析的符号数
- `functions_analyzed`：分析的函数名列表
- `chapters`：章节列表

## 5. 收尾清单

完成所有章节后，执行以下收尾：

1. 生成 `appendix-references.md`（参考资料索引）
2. 创建 `.study-meta.json`（格式见上方）
3. 更新 README.md，标记所有章节为"已完成"
4. 输出最终报告：位置、章节数、LSP 使用状态
```

**Step 3: 验证文件**

Run: `wc -l study-master-skill/document-templates.md`
Expected: 50-60 行

检查要点：
- 快速导览 5 个部分完整
- 模块解析 6 个部分完整
- 分段规则清晰简洁（对比原 SKILL.md 25 行 → 5 行）
- 元数据字段完整

**Step 4: Commit**

```bash
git add study-master-skill/document-templates.md
git commit -m "feat: create document-templates.md for study-master modular split"
```

---

### Task 3: 重写精简版 SKILL.md

**Files:**
- Modify: `study-master-skill/SKILL.md`（全量重写）

**Step 1: 阅读当前 SKILL.md 和两个新参考文件**

确认所有需要保留在 SKILL.md 中的核心内容：
- Frontmatter + 概述
- 目录结构规则（无 Mermaid 图）
- 教科书风格 4 原则
- 工作流程骨架（每阶段 3-5 行 + 参考文件引用）
- 文档结构概要
- 质量控制核心规则

**Step 2: 编写精简版 SKILL.md**

关键原则：
- 每个工作流阶段只保留"做什么"，不保留"怎么做的细节"
- 用 `📖 详见 [analysis-guide.md](analysis-guide.md)` 引用参考文件
- 不复述 format-rules.md 中的任何规则
- 目标 ~100-120 行

```markdown
---
name: study-master
description: 深入学习开源项目源码、协议规范和语言框架内部机制，生成教科书风格的学习文档
---

# Study-Master Skill

## 概述

帮助程序员深入学习开源项目源码、协议栈实现、编程语言/框架内部机制，生成深度解析型教科书风格学习文档。

文档规模根据主题复杂度动态调整，确保内容完整覆盖所有核心概念和关键实现。

## 强制目录结构

- 所有源码必须位于 `src/` 目录下
- 所有协议/规范文档必须位于 `docs/` 目录下
- 学习文档统一输出到 `study/<topic>/`
- 如果 `src/` 和 `docs/` 都不存在，拒绝执行并提示用户

## 教科书风格原则

生成的文档必须遵循渐进式知识展开：

1. **先整体后局部**：先展示模块在系统中的位置，再深入细节
2. **先接口后实现**：先讲清楚"做什么"，再讲"怎么做"
3. **先主流程后边界**：先追踪正常执行路径，再分析错误处理
4. **先概念后代码**：先用自然语言解释设计思想，再展示代码

## 工作流程

### 阶段 0：源码定位与验证

1. 验证 `src/` 或 `docs/` 目录存在
2. 按优先级查找：`src/<topic>/` → `src/*<topic>*/` → `docs/<topic>/` → `docs/*<topic>*/`
3. 多个候选时列出让用户选择
4. 创建输出目录 `study/<topic>/`

### 阶段 1：LSP 环境检测

C/C++ 项目自动检测 LSP 可用性，其他语言跳过。

📖 检测方法详见 [analysis-guide.md](analysis-guide.md) 第 1 节

### 阶段 2：主题识别与准备

解析 `<topic>` 参数，判断类型（项目/协议/语言内部机制），确定源码位置。

### 阶段 3：项目结构分析

扫描目录结构、关键文件，识别主要模块和依赖关系，生成架构概览和热点函数排名。

📖 分析方法详见 [analysis-guide.md](analysis-guide.md) 第 2-3 节

### 阶段 4：生成学习大纲

基于分析结果，确定章节划分，明确列出**所有**需要生成的章节。

📖 章节模板详见 [document-templates.md](document-templates.md)

### 阶段 5：生成快速导览

编写 `00-overview.md`，必须包含典型场景的完整执行路径追踪。

📖 导览模板详见 [document-templates.md](document-templates.md) 第 1 节
📖 格式规范详见 [format-rules.md](format-rules.md)

### 阶段 6-N：逐模块深度解析

**必须逐个生成所有计划的章节，不能中途停止。**

对每个核心函数进行分析，根据 LSP 可用性选择对应方法，生成文档并标注数据来源。

📖 函数分析流程详见 [analysis-guide.md](analysis-guide.md) 第 4 节
📖 模块章节模板详见 [document-templates.md](document-templates.md) 第 2 节

### 最后阶段：整合与收尾

**进入条件**：已生成所有计划章节，核心概念/关键函数/典型场景都已覆盖。

📖 收尾清单详见 [document-templates.md](document-templates.md) 第 5 节

## 文档结构概要

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：简介、概念速览、典型场景剖析、架构全景图、学习路线图 |
| `01-module-xxx.md` | 模块深度解析：概述、多层次代码展示、数据结构、算法、设计决策、学习检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 生成元数据 |

## 质量控制

- 每个章节根据复杂度动态调整长度，确保内容完整
- 生成后逐文件用 Read 检查乱码（U+FFFD）
- 确保所有源码引用都有正确的超链接
- 📖 格式规范由 [format-rules.md](format-rules.md) 定义，PostToolUse hook 自动验证
- 📖 分段输出规则详见 [document-templates.md](document-templates.md) 第 3 节
```

**Step 3: 验证精简结果**

Run: `wc -l study-master-skill/SKILL.md`
Expected: 100-120 行

对照检查：
- ✅ Frontmatter 和概述完整
- ✅ 目录结构规则完整（无 Mermaid 图）
- ✅ 教科书风格 4 原则完整
- ✅ 所有工作流阶段都有覆盖
- ✅ 每个需要详细方法的阶段都有参考文件引用
- ✅ 文档结构概要完整
- ✅ 质量控制核心规则完整
- ✅ 不包含 format-rules.md 中已有的格式细节
- ✅ 不包含 LSP 分析方法的技术细节
- ✅ 不包含分段输出规则的示例

**Step 4: Commit**

```bash
git add study-master-skill/SKILL.md
git commit -m "refactor: simplify SKILL.md with modular references (~60% reduction)"
```

---

### Task 4: 更新 install.sh

**Files:**
- Modify: `study-master-skill/install.sh`

**Step 1: 阅读当前 install.sh**

确认当前复制文件的逻辑（L30-31）。

**Step 2: 添加新文件到安装列表**

在 `cp "$SCRIPT_DIR/format-rules.md" "$TARGET_DIR/"` 之后添加两行：

```bash
cp "$SCRIPT_DIR/analysis-guide.md" "$TARGET_DIR/"
cp "$SCRIPT_DIR/document-templates.md" "$TARGET_DIR/"
```

更新成功消息中的文件列表（L35-36 之后）：

```bash
echo "   • analysis-guide.md"
echo "   • document-templates.md"
```

同样更新底部的安装组件列表（L114 附近）：

```bash
echo "    - analysis-guide.md"
echo "    - document-templates.md"
```

**Step 3: 验证安装脚本语法**

Run: `bash -n study-master-skill/install.sh`
Expected: 无输出（语法正确）

**Step 4: Commit**

```bash
git add study-master-skill/install.sh
git commit -m "feat: add new reference files to install.sh"
```

---

### Task 5: 更新 README.md

**Files:**
- Modify: `study-master-skill/README.md`

**Step 1: 阅读当前 README.md**

确认需要更新的部分。

**Step 2: 更新文件结构描述**

将 README 中的安装内容部分更新为反映新的文件结构：

```markdown
安装内容：
- Skill 文件：`~/.claude/skills/study-master/`
  - SKILL.md（核心工作流）
  - format-rules.md（格式规范）
  - analysis-guide.md（源码分析方法）
  - document-templates.md（文档模板）
- 格式验证 hooks：`~/.claude/hooks/`
```

**Step 3: Commit**

```bash
git add study-master-skill/README.md
git commit -m "docs: update README for modular file structure"
```

---

### Task 6: 端到端验证

**Files:**
- Read: 所有修改过的文件

**Step 1: 验证文件行数**

```bash
wc -l study-master-skill/SKILL.md study-master-skill/analysis-guide.md study-master-skill/document-templates.md study-master-skill/format-rules.md
```

Expected:
- SKILL.md: ~100-120 行
- analysis-guide.md: ~60-70 行
- document-templates.md: ~50-60 行
- format-rules.md: ~100 行（不变）

**Step 2: 验证内容完整性——无信息丢失**

逐一检查原 SKILL.md 中的每个关键概念是否在新的文件体系中有对应：

- [ ] LSP 环境检测 → analysis-guide.md 第 1 节
- [ ] 分析方法对照表 → analysis-guide.md 第 2 节
- [ ] LSP 深度分析 → analysis-guide.md 第 3 节
- [ ] 函数级分析 → analysis-guide.md 第 4 节
- [ ] 可视化类型选择 → analysis-guide.md 第 5 节
- [ ] 快速导览模板 → document-templates.md 第 1 节
- [ ] 模块解析模板 → document-templates.md 第 2 节
- [ ] 分段输出规则 → document-templates.md 第 3 节
- [ ] 元数据格式 → document-templates.md 第 4 节
- [ ] 收尾清单 → document-templates.md 第 5 节
- [ ] 格式规范 → format-rules.md（不变）
- [ ] 教科书原则 → SKILL.md（保留）
- [ ] 目录结构 → SKILL.md（保留）
- [ ] 工作流程 → SKILL.md（精简版）

**Step 3: 验证参考文件链接**

检查 SKILL.md 中所有 `📖 详见` 链接指向的文件和章节是否存在。

**Step 4: 验证 hook 兼容性**

确认 validate_study_master.py 不需要修改——它只检查 `study/` 目录下的 `.md` 文件，与 skill 文件结构无关。

**Step 5: 最终 Commit（如有修正）**

```bash
git add -A study-master-skill/
git commit -m "fix: address issues found in end-to-end verification"
```
