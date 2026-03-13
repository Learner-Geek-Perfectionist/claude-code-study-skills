# Study-Master Subagent 分章生成设计

## 问题

study-master 在生成中大型项目（6-10 个模块）的学习文档时，阶段 5-N 的逐章节串行生成导致 context 持续膨胀，在 4-6 个章节后触发 Opus 4.6 的 auto-compact。虽然目前质量下降不明显，但 compact 后丢失前期分析上下文存在质量风险。

## 约束

- 不降低文档质量（教科书风格、格式规范不变）
- 兼容现有的 format-rules.md 和 PostToolUse hook 验证

## 方案：Subagent 分章生成

### 核心思路

将"分析"和"生成"解耦。主对话完成源码分析和大纲规划后，将分析结果序列化为中间产物文件，然后将每个章节的生成任务委派给独立的 Agent subagent。每个 subagent 拥有独立的 context 窗口，从根本上避免 context 积累。

### 架构变化

```
主对话: 阶段 0-4（分析 + 大纲 + 序列化）
  │
  ├─ 写入: study/<topic>/.analysis-context.md
  │
  ├→ Agent #1（串行）: 生成 00-overview.md
  │
  ├→ Agent #2（并行）: 生成 01-module-xxx.md
  ├→ Agent #3（并行）: 生成 02-module-yyy.md
  ├→ Agent #N（并行）: ...
  │
  └─ 主对话: 收尾（逐文件验证 + appendix + meta）
```

### 中间产物：`.analysis-context.md`

连接主对话和 subagent 的桥梁。包含 subagent 生成高质量章节所需的上下文，但通过"只存指针不存原文"控制体积。

结构：

```markdown
# Analysis Context for <topic>

## 项目概况
- 项目名称、类型（源码/协议/语言机制）
- 源码根路径
- 源码路径映射表（模块名 → 文件路径列表）
- LSP 可用性状态

## 学习大纲
- 完整章节列表（编号、标题、对应模块）
- 每章内容要点（3-5 bullet）
- 章节间依赖关系

## 模块分析摘要
### 模块 X
- 核心函数列表（函数名、文件:行号、一句话职责）
- 关键数据结构列表
- 模块间依赖（调用谁、被谁调用）
- 热点函数排名（引用次数 Top 5）

## 格式规范引用
> 完整规范请 Read <skill-path>/format-rules.md
> 以下为关键摘要（源码位置格式、Mermaid 规则、反引号规则）
```

设计原则：
- 每个模块摘要 ≤ 30 行
- 只存文件路径+行号指针，不存源码原文
- 格式规范写摘要，指向完整文件让 subagent 自己 Read

### Subagent 调度策略

**第一波（串行）**：生成 00-overview.md
- 原因：overview 包含全局架构图和学习路线，后续章节可能引用

**第二波（并行）**：所有模块章节
- 每个 subagent 独立生成一个章节
- 互不依赖，可完全并行

**第三波（主对话串行）**：收尾
- 逐文件 Read 检查格式合规
- 生成 appendix-references.md、.study-meta.json、更新 README.md

### Subagent Prompt 模板

```
你是 study-master 文档生成器。你的任务是为「{topic}」生成第 {N} 章：{章节标题}。

准备步骤：
1. Read {study_path}/.analysis-context.md — 获取项目分析上下文
2. Read {skill_path}/format-rules.md — 获取完整格式规范
3. Read {skill_path}/document-templates.md — 获取章节模板（overview 用第 1 节，模块用第 2 节）

你需要分析的模块：{模块名}
源码文件：{文件路径列表}

生成要求：
- 遵循教科书风格原则：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
- 严格遵守 format-rules.md 的所有格式规范
- 使用分段写入：Write 创建文件（≤50 行）+ cat >> 追加（每次 ≤80 行）
- 生成完成后用 Read 验证无乱码和格式问题
- 输出到：{study_path}/{filename}.md
```

### 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `SKILL.md` | 阶段 4 新增序列化步骤；阶段 5/6-N 改为 subagent 委派；收尾新增格式验证 |
| `document-templates.md` | 新增第 6 节：Analysis Context 模板 |
| `analysis-guide.md` | 新增第 6 节：序列化分析结果指南 |

不需要修改：
- `format-rules.md` — 格式规范不变，subagent 直接引用
- Hook 文件 — 验证逻辑不变

### 质量保证

1. Subagent 内：生成后 Read 自检格式
2. 主对话：所有 subagent 完成后逐文件 Read 验证
3. PostToolUse hook：自动验证每次写入的格式合规性（已有机制，无需修改）
4. 跨章节一致性：通过共享的 .analysis-context.md 保证术语、结构、引用一致
