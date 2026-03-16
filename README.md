# learning-skills

Claude Code 自定义 Skill 集合。

## study-master

深入学习开源项目源码、协议规范和语言框架内部机制，生成教科书风格的学习文档。

### 功能特点

- **全串行生成**：利用 1M 上下文窗口，主对话串行生成所有章节，每章拥有完整的源码 + 前序章节上下文
- **LSP 增强分析**：C/C++ 项目自动检测并使用 LSP（documentSymbol、findReferences、callHierarchy）
- **教科书风格**：先整体后局部、先接口后实现、先主流程后边界、先概念后代码
- **丰富的交叉引用**：章节间知识网络、源码超链接、Mermaid 图表、独立 SVG 内存布局图
- **格式验证 Hook**：PostToolUse hook 自动检测 ASCII art、Unicode 数学符号、失效锚点等格式问题

### 文件结构

```
study-master-skill/
├── SKILL.md              # 主 Skill 文件（自给自足，无需子文件依赖）
├── format-rules.md       # 格式规范参考
├── install.sh            # 安装脚本
└── hooks/
    ├── check-study_master.sh       # PostToolUse hook 入口
    └── validate_study_master.py    # 格式验证器
```

### 安装

```bash
cd study-master-skill
bash install.sh
```

### 使用

```
/study-master <topic>
```

要求项目目录包含 `source/`（源码）或 `specs/`（协议规范）目录。

### 生成的文档结构

```
study/<topic>/
├── 00-overview.md           # 总览：背景、核心概念、典型场景、架构图、学习路线
├── 01-module-xxx.md         # 模块深度解析（6 节结构）
├── ...
├── NN-module-xxx.md
├── appendix-references.md   # 参考资料索引
├── *.svg                    # 内存布局图（独立 SVG 文件）
└── .study-meta.json         # 元数据
```
