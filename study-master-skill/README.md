# Study-Master Skill

一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 自定义 Skill，帮助程序员深入学习开源项目源码、协议规范和语言框架内部机制。自动生成**教科书风格**的学习文档，充分利用 Claude 的 1M 上下文窗口进行全源码深度分析。

## 特性

- **全源码深度分析** — 将整个项目源码加载到 1M 上下文窗口中，生成真正理解代码的学习文档
- **LSP 增强** — 自动检测 `compile_commands.json`，利用 LSP 获取精确的符号定义、引用和调用层次
- **教科书风格输出** — 遵循「先整体后局部、先接口后实现、先主流程后边界、先概念后代码」四原则
- **格式自动校验** — PostToolUse Hook 实时校验生成文档的链接、图表、代码块等格式规范
- **性能 Profiling** — 记录工具调用日志，支持生成性能分析报告

## 快速开始

### 安装

```bash
git clone https://github.com/Learner-Geek-Perfectionist/claude-code-study-skills.git
cd claude-code-study-skills/study-master-skill
./install.sh
```

安装脚本会自动完成：
1. 将 Skill 文件复制到 `~/.claude/skills/study-master/`
2. 将 Hook 脚本复制到 `~/.claude/hooks/`
3. 在 `~/.claude/settings/settings.json` 中注册格式校验 Hook

### 项目结构要求

在你的目标项目中，至少需要以下目录之一：

```
project-root/
├── source/       # 源码目录
├── specs/        # 协议规范文档
└── study/        # 生成的学习文档（自动创建）
```

### 使用

在目标项目目录下启动 Claude Code，输入：

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
  ├─ LSP 检测（C/C++ 项目）
  ├─ 全源码深度分析（1M 上下文）
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
├── hooks/
│   ├── check-study_master.sh         # PostToolUse Hook 入口
│   ├── validate_study_master.py      # 格式校验器
│   ├── profiling_hook.sh             # 工具调用日志记录
│   └── generate_profiling_report.py  # 性能分析报告生成
└── docs/plans/                       # 设计文档与迭代计划
```

### 格式校验器

`validate_study_master.py` 在每次 Write/Edit 操作后自动运行，检查项包括：

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
