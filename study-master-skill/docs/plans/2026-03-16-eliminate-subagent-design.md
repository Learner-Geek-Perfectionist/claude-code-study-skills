# 消除 Subagent 架构 — 主对话直出设计

## 背景

### 性能基线（Lua 5.5 测试用例）

- **总耗时**：41m15s（目标 < 20m）
- **源码规模**：63 文件，5943 行
- **输出规模**：9 章节 + overview + appendix，共 ~8000 行 markdown

### 瓶颈分析

| 阶段 | 耗时 | 占比 | 问题 |
|------|------|------|------|
| Stage 6N 章节生成 | 18m56s | 45.9% | 9 个 agent 实际串行执行，无并行收益 |
| Final 质量审查 | 9m03s | 21.9% | 6 步串行审查，其中交叉引用注入 4m37s |
| Stage 4 序列化 | 7m07s | 17.3% | 写 700 行富分析报告，纯粹为 subagent 服务 |
| Stage 5 Overview | 4m30s | 10.9% | 单独 agent 有启动开销 |

### 根因

当前架构基于"并行 subagent"假设设计，但实测显示 agent 是串行执行的。subagent 架构引入了 ~11 分钟的无效开销（序列化 + agent 启动 + 审查修补），却没有换来并行加速。

## 设计决策

**消除 subagent，主对话在 1M 上下文中直接完成所有工作。**

理由：
1. agent 串行执行，并行架构前提不成立
2. 序列化分析报告（Stage 4）纯粹为 subagent 服务，是最大浪费
3. 主对话拥有完整源码上下文，生成质量至少不低于 subagent
4. 同一对话生成所有章节，交叉引用天然一致，不需要事后注入

## 新架构：三阶段工作流

```
旧：Stage 0-2 → Stage 3 → Stage 4 序列化 → Stage 5 agent → Stage 6N 9×agent → Final 6步
新：Phase 1 准备+分析 → Phase 2 直接生成 → Phase 3 轻量收尾
```

### Phase 1：源码加载与分析（~2 min）

| 子阶段 | 内容 | 变化 |
|--------|------|------|
| 1.1 源码定位与验证 | 检查 src/docs 存在，定位 topic 源码 | 不变 |
| 1.2 LSP 环境检测 | C/C++ 项目检测 LSP | 不变 |
| 1.3 全源码深度分析 | Read 全部源文件，结构分析，热点函数 | 不变 |
| 1.4 确定章节大纲 | 章节划分、source_path_prefix、交叉引用锚点映射 | **简化**：不再写 .analysis-context.md，结论留在上下文中 |

关键变化：
- 删除 .analysis-context.md 的强制生成（原 Stage 4 耗时 7m07s）
- 交叉引用锚点映射表保留在上下文中供 Phase 2 使用
- 可选：在 Phase 3 收尾时生成精简版摘要（~100 行，供用户参考）

### Phase 2：主对话直接生成（~12-14 min）

**生成顺序：串行，从概览到模块章节**

```
00-overview.md → 01-xxx.md → 02-xxx.md → ... → NN-xxx.md → appendix-references.md
```

#### Phase 2.1：生成 Overview

- 主对话直接 Write 完整的 00-overview.md
- 内容要求不变：项目简介、核心概念、典型场景、架构全景图、学习路线图
- 模板参考 document-templates.md 第 1 节

#### Phase 2.2：逐章生成模块章节

对每个章节：
1. 在上下文中回顾该模块相关源码（Phase 1 已加载，无需再次 Read）
2. 按 document-templates.md 第 2 节模板，一次 Write 完整章节
3. 生成时直接查阅上下文中的锚点映射表，当场写入正确的交叉引用链接

每章预估 ~80s（当前 subagent ~126s，去掉读文件和启动开销后）。

#### Phase 2.3：生成 appendix-references.md

最后生成参考索引。

#### 交叉引用策略

交叉引用在生成时直接注入（而非事后补），因为主对话上下文中已有：
- 前面章节的所有标题和锚点
- 后续章节的预计算锚点映射（Phase 1.4）

这消除了原 Final step-3 的 4m37s 开销。

### Phase 3：轻量收尾（~3.5 min）

#### Phase 3.1：全量格式检查（~2 min）

逐文件 Read 所有生成的章节，检查：
- 链接格式（相对路径、锚点完整性）
- Mermaid 图表（节点数、标题长度）
- 反引号规则（链接文本 vs 纯文本）
- LaTeX 数学符号（无 Unicode 数学符号）
- 源码路径正确性（source_path_prefix）
- 乱码（U+FFFD）

发现问题直接 Edit 修正。

#### Phase 3.2：整合收尾（~90s）

- 创建 `.study-meta.json`
- 输出最终完成报告
- （可选）生成精简版 `.analysis-context.md` 摘要

### 被删除的步骤

| 原步骤 | 耗时 | 删除理由 |
|--------|------|---------|
| Stage 4 序列化富分析报告 | 7m07s | 分析留在上下文中，不需要序列化 |
| Stage 5 Overview agent | 4m30s | 主对话直接生成 |
| Stage 6N Subagent 委派 | 18m56s | 主对话直接生成 |
| Final step-2 内容审查 | 1m43s | 主对话生成时已保持一致性 |
| Final step-3 交叉引用注入 | 4m37s | Phase 2 生成时已内嵌 |
| Final step-4 深度补充 | 0s | 主对话直接引用源码，深度已足够 |
| Final step-5 概览更新 | 0s | 主对话先生成概览 |

## 时间预估

| 阶段 | 当前耗时 | 优化后预估 | 节省 |
|------|---------|-----------|------|
| Phase 1 (原 Stage 0-3 + 4 大纲部分) | 8m46s | ~2m | -6m46s |
| Phase 2 (原 Stage 5 + 6N) | 23m26s | ~14m | -9m26s |
| Phase 3 (原 Final) | 9m03s | ~3.5m | -5m33s |
| **总计** | **41m15s** | **~19.5m** | **-21m45s** |

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| SKILL.md | 重写 | 6 阶段 → 3 阶段，删除 subagent prompt 模板 |
| document-templates.md | 精简 | 删除第 6 节（富分析报告模板），修改第 3 节 |
| analysis-guide.md | 微调 | 删除第 6 节（序列化指南） |
| format-rules.md | 不变 | 格式规范与架构无关 |
| README.md | 更新 | 架构描述、演进表、Mermaid 图 |
| SKILL-profiling.md | 同步重写 | profiling 版与新 SKILL.md 同步 |

不需要改动：hooks/、install 脚本。无新增或删除文件。

## 风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| 上下文压力（~6000 行源码 + ~7000 行输出） | 低 | 1M 上下文远超 13000 行需求 |
| 后半段章节质量下降 | 低 | Phase 3.1 全量格式检查兜底 |
| 单点失败（中途出错需重来） | 中 | PostToolUse hook 在 Write 时即时验证，尽早发现问题 |

## 质量保障

文档质量维持当前水平的措施：
1. 教科书风格原则不变（先整体后局部、先接口后实现、先主流程后边界、先概念后代码）
2. format-rules.md 所有规范不变
3. document-templates.md 的章节模板不变
4. PostToolUse hook 自动验证不变
5. Phase 3.1 全量格式检查兜底
