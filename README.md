# Study-Master Skill

一个面向 Claude Code 和 Codex 的 `study-master` Skill，帮助程序员深入学习开源项目源码、协议规范和语言框架内部机制。自动生成**教科书风格**的学习文档，并根据当前 CLI 和模型的实际能力自适应选择文件分析、LSP 和校验流程。

## 特性

- **全源码深度分析** — 在当前上下文预算内尽可能加载核心源码；项目过大时退化为“分批加载 + 摘要保持”
- **LSP 增强** — 自动检测 `compile_commands.json`，利用 LSP 获取精确的符号定义、引用和调用层次
- **教科书风格输出** — 遵循「先整体后局部、先接口后实现、先主流程后边界、先概念后代码」四原则
- **双 CLI 校验** — Claude Code 使用 Write/Edit 后置校验；Codex 使用 Stop Hook 汇总校验
- **性能 Profiling** — 记录工具调用日志，支持生成性能分析报告

## 快速开始

### 安装

```bash
git clone https://github.com/Learner-Geek-Perfectionist/claude-code-study-skills.git
cd claude-code-study-skills/study-master-skill
./install.sh
```

安装脚本会自动完成：
1. 将 Skill 文件安装到 Claude Code 和 Codex 的 Skill 目录
2. 复制并注册 Claude Code 的 Hook
3. 复制并注册 Codex 的 Stop Hook，并启用 `codex_hooks`

### 项目结构要求

在你的目标项目中，至少需要以下目录之一：

```
project-root/
├── source/       # 源码目录（二选一）
├── specs/        # 协议规范文档（二选一）
└── study/        # 生成的学习文档（自动创建）
```

### 使用

在目标项目目录下启动 Claude Code 或 Codex，调用 `study-master` Skill 并提供主题名。Claude Code 可以直接输入：

```
/study-master <topic>
```

例如：

```
/study-master redis
/study-master tcp
/study-master cyclonedds
```

## 生成文档结构

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构全景图、学习路线图 |
| `01~NN-module-xxx.md` | 模块深度解析：概述、API 签名速查、代码展示、数据结构、算法、设计决策、学习检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 生成元数据（主题、源码路径、时间戳、章节列表） |

## 工作流程

```
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

## 组件说明

```
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

## License

MIT
