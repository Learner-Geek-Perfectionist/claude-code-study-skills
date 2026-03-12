# Study-Master Skill

深度学习开源项目源码、协议规范和语言框架内部机制的 Claude skill。

## 功能特性

- **深度解析**：生成 50-100 页的详细学习文档
- **混合组织**：快速导览 + 模块深度解析
- **多层次展示**：调用关系图 → 伪代码 → 真实代码 → 实现细节
- **教科书风格**：结构化、渐进式、有逻辑关联
- **实时进度**：生成过程中显示当前进度
- **智能查找**：自动定位源码位置

## 推荐目录结构

```
project-root/
├── src/                    # 源码目录
│   └── <module-name>/      # 要学习的源码模块
├── docs/                   # 协议规范文档
│   └── <spec-name>/
└── study/                  # 生成的学习文档（自动创建）
    ├── <topic1>/
    └── <topic2>/
```

**优势**：
- 清晰分离源码、文档、学习材料
- 自动查找源码，无需手动指定路径
- 支持学习多个主题

## 使用方式

### 基本用法（自动查找源码）

```bash
/study-master <topic>
```

skill 会自动在以下位置查找源码：
1. `src/<topic>/` - 精确匹配
2. `src/*<topic>*/` - 模糊匹配
3. `docs/<topic>/` - 协议文档
4. `./<topic>/` - 根目录

### 手动指定源码路径

```bash
/study-master <topic> --source <path>
```

## 示例

### 示例 1：使用推荐目录结构

假设你的项目结构如下：

```
my-project/
├── src/
│   ├── redis/
│   └── nginx/
└── study/          # 自动创建
```

学习 Redis 源码（自动查找）：

```bash
/study-master redis
```

生成的文档位于：`study/redis/`

### 示例 2：手动指定路径

学习外部项目：

```bash
/study-master redis --source /path/to/redis
```

### 示例 3：学习协议规范

```
my-project/
├── docs/
│   └── tcp-ip-specs/
└── study/
```

```bash
/study-master tcp-ip
```

生成的文档位于：`study/tcp-ip/`

## 生成的文档结构

```
<topic>/
├── 00-overview.md          # 快速导览（场景驱动）
├── 01-module-xxx.md        # 模块1深度解析
├── 02-module-yyy.md        # 模块2深度解析
├── ...
├── appendix-references.md  # 参考资料和索引
└── .study-meta.json        # 元数据
```

## 安装

运行安装脚本，将 skill 和 hooks 安装到 Claude：

```bash
./install.sh
```

安装内容：
- Skill 文件：`~/.claude/skills/study-master.md`
- 格式验证 hooks：`~/.claude/hooks/`

安装后即可使用 `/study-master` 命令。

### 检查项

- ❌ `file:///` 绝对路径
- ❌ 链接文本中的反引号
- ❌ ASCII art 字符（应使用 Mermaid）
- ❌ Unicode 数学符号（应使用 LaTeX）
- ❌ 无语言标识的代码块
- ❌ U+FFFD 乱码字符
- ❌ 源码位置格式错误

## 文档特点

### 快速导览章节

- 项目/协议简介
- 核心概念速览
- 典型场景剖析（追踪完整执行流程）
- 架构全景图（Mermaid 图表）
- 学习路线图

### 模块深度解析章节

每个模块包含：

1. 模块概述（职责、边界、交互）
2. 多层次代码展示（调用图 → 伪代码 → 真实代码 → 细节）
3. 数据结构深度解析
4. 关键算法剖析
5. 设计决策分析

## 设计文档

详细的设计和实现文档位于：

- 设计文档：`docs/plans/2026-03-12-study-master-skill-design.md`
- 实现计划：`docs/plans/2026-03-12-study-master-implementation.md`

## License

MIT
