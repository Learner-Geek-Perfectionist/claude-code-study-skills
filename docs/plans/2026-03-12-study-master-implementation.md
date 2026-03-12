# Study-Master Skill 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建 study-master skill 和 format-validator hook，用于深度学习开源项目源码和协议规范

**Architecture:** 流程驱动型 skill，通过 8 个阶段任务生成教科书风格的学习文档。包含独立的格式检查 hook 确保输出质量。

**Tech Stack:** Markdown, Mermaid, Shell Script, Claude Skills Framework

---

## Task 1: 创建 skill 目录结构

**Files:**
- Create: `~/.claude/skills/study-master/SKILL.md`

**Step 1: 创建 skill 目录**

```bash
mkdir -p ~/.claude/skills/study-master
```

**Step 2: 创建 SKILL.md 基础框架**

创建文件 `~/.claude/skills/study-master/SKILL.md`，包含 frontmatter 和基本结构。

**Step 3: 验证文件创建**

```bash
ls -la ~/.claude/skills/study-master/
cat ~/.claude/skills/study-master/SKILL.md | head -20
```

Expected: 文件存在且包含正确的 frontmatter

**Step 4: Commit**

```bash
cd ~/.claude/skills
git add study-master/SKILL.md
git commit -m "feat: create study-master skill framework"
```

## Task 2: 实现 SKILL.md 核心内容

**Files:**
- Modify: `~/.claude/skills/study-master/SKILL.md`

**Step 1: 添加参数解析和主题识别逻辑**

在 SKILL.md 中添加参数解析部分，包括：
- 解析 `<topic>` 和可选的 `--source <path>`
- 主题类型识别逻辑

**Step 2: 添加 8 阶段任务定义**

添加完整的工作流程说明：
- 阶段 1：主题识别与准备
- 阶段 2：项目结构分析
- 阶段 3：生成学习大纲
- 阶段 4：生成快速导览
- 阶段 5-N：逐模块深度解析
- 最后阶段：整合与收尾

**Step 3: 添加文档生成规范引用**

引用 `~/.claude/skills/_shared/format-rules.md`

**Step 4: 验证 skill 内容**

```bash
cat ~/.claude/skills/study-master/SKILL.md
```

Expected: 包含完整的流程定义和规范引用

**Step 5: Commit**

```bash
cd ~/.claude/skills
git add study-master/SKILL.md
git commit -m "feat: implement study-master core workflow"
```

## Task 3: 创建 format-validator hook

**Files:**
- Create: `~/.claude/hooks/format-validator.sh`

**Step 1: 创建 hooks 目录**

```bash
mkdir -p ~/.claude/hooks
```

**Step 2: 创建 format-validator.sh 脚本**

创建 shell 脚本，包含以下检查功能：
- 检测 `file:///` 绝对路径
- 检测链接文本中的反引号
- 检测 ASCII art 字符
- 检测 Unicode 数学符号
- 检测无语言标识的代码块
- 检测 U+FFFD 乱码字符

**Step 3: 添加执行权限**

```bash
chmod +x ~/.claude/hooks/format-validator.sh
```

**Step 4: 测试 hook**

创建测试文件并运行 hook：

```bash
echo "test file:///" > /tmp/test.md
~/.claude/hooks/format-validator.sh /tmp/test.md
```

Expected: 检测到 `file:///` 违规

**Step 5: Commit**

```bash
cd ~/.claude
git add hooks/format-validator.sh
git commit -m "feat: add format-validator hook"
```

## Task 4: 测试 study-master skill

**Files:**
- Create: `test-study-master.sh`

**Step 1: 创建简单测试脚本**

在当前目录创建测试脚本，测试 skill 的基本功能。

**Step 2: 运行测试**

```bash
bash test-study-master.sh
```

Expected: skill 能正确识别主题并创建目录结构

**Step 3: 验证生成的文档**

检查生成的文档是否符合格式规范：

```bash
~/.claude/hooks/format-validator.sh <topic>/
```

Expected: 格式检查通过或输出具体违规项

**Step 4: Commit 测试脚本**

```bash
git add test-study-master.sh
git commit -m "test: add study-master skill test"
```

## Task 5: 更新项目文档

**Files:**
- Create: `README.md`

**Step 1: 创建 README.md**

包含以下内容：
- 项目简介
- study-master skill 使用说明
- format-validator hook 使用说明
- 示例

**Step 2: 验证文档**

```bash
cat README.md
```

Expected: 文档清晰完整

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add project README"
```

---

## 执行说明

1. 按顺序执行每个 Task
2. 每个 Step 完成后验证结果
3. 遇到问题立即停止并修复
4. 所有任务完成后运行完整测试

