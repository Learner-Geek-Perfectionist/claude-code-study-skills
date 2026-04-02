# Agent Study Skills

面向 Claude Code、Codex 等 agent CLI 的学习型 Skill 仓库。当前收录的核心 Skill 是 `study-master`，用于系统化拆解开源项目源码、协议规范和语言框架内部机制，并生成教科书风格的学习文档。

## 仓库定位

`agent-study-skills` 是一个面向多 agent CLI 的 Skill 仓库，目标是沉淀适合深度学习、源码研究与技术拆解的可复用工作流。

当前仓库先以 `study-master` 作为首个收录 Skill，后续如有新的学习型 Skill，再继续在这个仓库中扩展。

## 当前收录 Skills

| Skill | 目录 | 用途 | 状态 |
|------|------|------|------|
| `study-master` | `study-master-skill/` | 深入学习源码、协议规范和框架内部机制，生成结构化学习文档 | 当前主力 |

## 兼容矩阵

| CLI / Agent | Skill 安装 | Hook 模式 | 当前状态 |
|------------|------------|-----------|----------|
| Claude Code | `./study-master-skill/install.sh` | Write/Edit 后置 Hook | 已支持 |
| Codex | `./study-master-skill/install.sh` | Stop Hook + `codex_hooks` | 已支持 |

## 快速开始

### 安装

```bash
git clone https://github.com/Learner-Geek-Perfectionist/agent-study-skills.git
cd agent-study-skills/study-master-skill
./install.sh
```

安装脚本会自动完成：
1. 将 `study-master` 安装到 Claude Code 和 Codex 的 Skill 目录
2. 复制并注册 Claude Code 的 Hook
3. 复制并注册 Codex 的 Stop Hook，并启用 `codex_hooks`

### 项目结构要求

在你的目标项目中，至少需要以下目录之一：

```text
project-root/
├── source/       # 源码目录（二选一）
├── specs/        # 协议规范文档（二选一）
└── study/        # 生成的学习文档（自动创建）
```

## 当前重点 Skill：`study-master`

`study-master` 是当前仓库中负责“深度学习与结构化讲解”的核心 Skill。它帮助程序员在有限上下文预算下尽可能完整地理解项目，并输出适合持续阅读的学习材料。

### 核心特性

- **全源码深度分析**：在当前上下文预算内尽可能加载核心源码；项目过大时退化为“分批加载 + 摘要保持”
- **LSP 增强**：自动检测 `compile_commands.json`，利用 LSP 获取精确的符号定义、引用和调用层次
- **教科书风格输出**：遵循“先整体后局部、先接口后实现、先主流程后边界、先概念后代码”四原则
- **双 CLI 校验**：Claude Code 使用 Write/Edit 后置校验；Codex 使用 Stop Hook 汇总校验
- **性能 Profiling**：记录工具调用日志，支持生成性能分析报告

### 使用

在目标项目目录下启动 Claude Code 或 Codex，调用 `study-master` Skill 并提供主题名。Claude Code 可以直接输入：

```text
/study-master <topic>
```

例如：

```text
/study-master redis
/study-master tcp
/study-master cyclonedds
```

### 生成文档结构

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构全景图、学习路线图 |
| `01~NN-module-xxx.md` | 模块深度解析：概述、API 签名速查、代码展示、数据结构、算法、设计决策、学习检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 生成元数据（主题、源码路径、时间戳、章节列表） |

### 工作流程

```text
Phase 1: 源码加载与分析
  ├─ 源码定位与环境准备
  ├─ LSP 检测（按环境能力执行）
  ├─ 全源码深度分析（上下文预算自适应）
  └─ 确定章节大纲

Phase 2: 串行生成文档
  ├─ 逐章生成（上下文累积）
  └─ 生成参考索引

Phase 3: 收尾
  ├─ 创建 .study-meta.json
  └─ 输出最终报告
```

### 组件说明

```text
study-master-skill/
├── SKILL.md                          # Skill 定义（核心）
├── install.sh                        # 一键安装脚本
└── hooks/
    ├── check-study_master.sh         # Claude/Codex Hook 入口
    └── validate_study_master.py      # 格式校验器
```

### 格式校验器

`validate_study_master.py` 会在 Claude Code 的 Write/Edit 后置 Hook 或 Codex 的 Stop Hook 中运行，检查项包括：

- Unicode 替换字符（U+FFFD）
- Unicode 数学符号（应使用 LaTeX）
- ASCII art / box-drawing 字符（应使用 Mermaid）
- 代码块语言标识
- 源码位置格式
- 绝对路径（应使用相对路径）
- 链接文本中的反引号
- 源码链接文件存在性
- 交叉引用锚点完整性
- API 签名速查节完整性

## 路线图

- 持续打磨 `study-master` 在多 agent CLI 下的一致体验
- 在保持仓库聚焦的前提下，逐步补充新的学习型 Skills
- 继续沉淀适合源码研究、协议学习和框架拆解的通用方法论

## License

MIT
