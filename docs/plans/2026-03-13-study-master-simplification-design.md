# Study-Master Skill 模块化精简设计

**日期**：2026-03-13
**目标**：在不降低 Markdown 生成质量的前提下，消除 SKILL.md 的冗余，通过模块化拆分减少初始上下文占用

## 1. 问题分析

### 1.1 当前状态

| 文件 | 行数 | 加载时机 |
|------|------|---------|
| SKILL.md | 333 行 | Skill 触发时全量加载 |
| format-rules.md | 100 行 | 需手动 Read |

### 1.2 已识别的冗余

| 冗余类型 | 位置 | 行数 | 说明 |
|---------|------|------|------|
| 格式规范重复 | SKILL.md L244-257 | ~15 | 与 format-rules.md 高度重叠，hook 已自动执行 |
| LSP 双路径重复 | SKILL.md L109-124 + L158-188 | ~50 | Phase 3 和 Phase 6-N 各写一遍 |
| 分段输出规则 | SKILL.md L283-306 | ~25 | 过度详细的示例 |
| 目录结构 Mermaid 图 | SKILL.md L25-40 | ~16 | 与文字规则重复 |
| 元数据 JSON 模板 | SKILL.md L314-332 | ~20 | 可简化 |
| 文档结构与流程重叠 | SKILL.md L213-240 | ~28 | 两处描述相同信息 |

冗余总计约 154 行（占 46%）。

## 2. 设计方案：模块化拆分

### 2.1 文件结构

```
study-master-skill/
├── SKILL.md                  ~100-120 行  ← Skill 加载（减少 ~60%）
├── format-rules.md           ~100 行      ← 按需 Read（无变化）
├── analysis-guide.md (新)    ~60-70 行    ← 阶段 1/3/6 时 Read
├── document-templates.md (新) ~50-60 行   ← 阶段 4/5 时 Read
├── hooks/
│   ├── check-study_master.sh
│   └── validate_study_master.py
├── install.sh
└── README.md
```

### 2.2 各文件职责

**SKILL.md（核心，~100-120 行）**：工作流骨架 + 核心规则
- Frontmatter + 概述（~10行）
- 目录结构规则：src/ docs/ study/ 三行规则，去掉 Mermaid 图（~8行）
- 教科书风格原则：4 条渐进式展开原则（~6行）
- 工作流程：每阶段 3-5 行，标注需 Read 的参考文件（~50行）
- 文档结构概要：章节名 + 核心要素（~12行）
- 质量控制：核心检查项 + 引用 format-rules.md（~6行）

**analysis-guide.md（新建，~60-70 行）**：源码分析技术细节
1. LSP 环境检测（~10行）：查找 compile_commands.json、测试响应、记录状态
2. 项目结构分析方法表（~15行）：统一的 LSP/传统工具对照表
3. LSP 深度分析流程（~15行）：热点函数、耦合度、调用树
4. 函数级分析工作流（~15行）：签名→调用→调用树→执行路径
5. 可视化类型选择（~8行）：graph/sequenceDiagram/stateDiagram/classDiagram

**document-templates.md（新建，~50-60 行）**：文档模板和操作规则
1. 快速导览章节模板（~12行）：00-overview.md 的 5 个必含部分
2. 模块深度解析模板（~15行）：6 个标准部分的要求
3. 分段输出规则（~8行）：Write ≤ 50行，cat >> ≤ 80行
4. 元数据格式（~10行）：.study-meta.json 关键字段
5. 收尾清单（~5行）：appendix、README、最终报告

**format-rules.md（无变化，100 行）**：格式规范，由 hook 自动执行

### 2.3 SKILL.md 内容设计

#### 保留的内容

| 部分 | 精简后行数 | 保留理由 |
|------|-----------|---------|
| Frontmatter + 概述 | ~10 | 必须：定义触发和用途 |
| 目录结构规则 | ~8 | 必须：强制约定，去掉重复的 Mermaid 图 |
| 教科书风格原则 | ~6 | 关键：直接影响生成质量 |
| 工作流程骨架 | ~50 | 骨架：每阶段精简为核心步骤 + 参考文件引用 |
| 文档结构概要 | ~12 | 保留章节名和核心要素 |
| 质量控制 | ~6 | 精简为核心规则 |

#### 删除/移出的内容

| 内容 | 去向 | 原因 |
|------|------|------|
| 文档生成规范格式细节 | 已在 format-rules.md | 纯重复，hook 自动执行 |
| LSP 检测方法 | → analysis-guide.md | 技术细节 |
| LSP/传统分析双路径表 | → analysis-guide.md | 合并两处重复 |
| 函数级分析工作流 | → analysis-guide.md | 详细方法论 |
| 可视化类型选择指南 | → analysis-guide.md | 参考信息 |
| 分段输出规则+示例 | → document-templates.md | 操作细节 |
| 元数据 JSON 完整模板 | → document-templates.md | 模板格式 |
| 快速导览详细模板 | → document-templates.md | 模板细节 |
| 模块解析详细模板 | → document-templates.md | 模板细节 |
| Mermaid 目录结构图 | 删除 | 与文字规则完全重复 |

### 2.4 按需加载策略

工作流中每个阶段明确标注需要 Read 的文件：

| 阶段 | 需要 Read 的文件 |
|------|----------------|
| 阶段 0（源码定位） | 无 |
| 阶段 1（LSP 检测） | analysis-guide.md |
| 阶段 2（主题识别） | 无 |
| 阶段 3（结构分析） | analysis-guide.md（如阶段1未读） |
| 阶段 4（生成大纲） | document-templates.md |
| 阶段 5（生成导览） | document-templates.md（如阶段4未读）, format-rules.md |
| 阶段 6-N（模块解析） | analysis-guide.md（如需回顾分析方法）|
| 最后阶段（收尾） | document-templates.md（元数据格式）|

## 3. install.sh 更新

install.sh 需要更新以复制新增的两个文件：
- 添加 `analysis-guide.md` 到安装列表
- 添加 `document-templates.md` 到安装列表

## 4. 不变的部分

- format-rules.md：内容不变
- hooks/：check-study_master.sh 和 validate_study_master.py 不变
- README.md：需要小幅更新以反映新的文件结构

## 5. 预期效果

- Skill 加载时的上下文占用从 ~333 行降至 ~100-120 行（减少 ~60%）
- 全部内容（含参考文件）的总行数从 ~433 行降至 ~330 行（去重后也有减少）
- 格式质量由 format-rules.md + hook 保障，不受精简影响
- 分析方法和文档模板按需加载，不浪费上下文空间
