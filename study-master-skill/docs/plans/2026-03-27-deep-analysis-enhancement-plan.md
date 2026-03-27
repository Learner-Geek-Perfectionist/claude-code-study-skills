# Study-Master 深度分析增强 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 study-master skill 的模块章节从 7 节结构重构为 9 节结构，增加命名消歧、逐行精讲、三层字段分析等深度分析能力。

**Architecture:** 仅修改 `study-master-skill/SKILL.md` 一个文件，涉及 4 个区域的编辑：Phase 1.4 大纲准备、模块章节结构定义、Mermaid 图要求、文档结构概要表。

**Tech Stack:** Markdown (skill definition)

---

### Task 1: 更新 Phase 1.4 — 增加"识别易混淆函数组"准备步骤

**Files:**
- Modify: `study-master-skill/SKILL.md:66-73`

**Step 1: 编辑 Phase 1.4**

在现有的第 2 点之后增加第 3 点。将：

```markdown
1. **计算 `source_path_prefix`**：统计 `study/<topic>/` 相对于项目根的目录层数，每层一个 `../`。例如 `study/redis/` 为 2 层 → `../../`。
2. **确定章节大纲和各章节的主要标题结构**：明确各章节会包含哪些核心结构体/函数的定义标题，以便串行生成时自然地内嵌前向和后向交叉引用。
```

替换为：

```markdown
1. **计算 `source_path_prefix`**：统计 `study/<topic>/` 相对于项目根的目录层数，每层一个 `../`。例如 `study/redis/` 为 2 层 → `../../`。
2. **确定章节大纲和各章节的主要标题结构**：明确各章节会包含哪些核心结构体/函数的定义标题，以便串行生成时自然地内嵌前向和后向交叉引用。
3. **识别易混淆函数组**：扫描各模块的函数列表，按"前缀 + 模块名 + 操作"拆解命名，标记名称相似但用途不同的函数组（如 `ddsi_rmsg_xxx` vs `ddsi_rdata_xxx` 委托对），为 Section 2 的命名对比表做准备。
```

**Step 2: 验证修改**

Run: `grep -n "识别易混淆函数组" study-master-skill/SKILL.md`
Expected: 找到新增的第 3 点

**Step 3: Commit**

```bash
git add -f study-master-skill/SKILL.md
git commit -m "feat(study-master): add confusable function identification to Phase 1.4"
```

---

### Task 2: 重构模块章节结构 — 从 7 节替换为 9 节

**Files:**
- Modify: `study-master-skill/SKILL.md:98-106`

**Step 1: 替换模块章节结构定义**

将原始的 7 节结构（第 98-106 行）：

```markdown
**模块章节（01~NN-module-xxx.md）结构（7 节必须齐全）：**

1. **模块概述**：模块职责、在系统中的位置
2. **API 签名速查**：该模块所有函数的完整 C 签名（代码块），每个函数一行注释说明用途。包括公开 API 和文档中分析到的内部函数，不可省略。
3. **多层次代码展示**：调用关系图（Mermaid）→ 伪代码 → 真实代码片段 → 实现细节
4. **数据结构深度解析**：结构定义、字段含义、生命周期
5. **关键算法剖析**：算法思想、时间复杂度、边界处理
6. **设计决策分析**：为什么这样设计、权衡考虑、替代方案
7. **学习检查点**：📝 本章小结（3-5 个要点）+ 🤔 思考题（2-3 个引导性问题）
```

替换为以下完整的 9 节结构定义（8 节编号 + 调用关系图移入 Section 3，合计 9 个逻辑节）：

````markdown
**模块章节（01~NN-module-xxx.md）结构（8 节必须齐全）：**

1. **模块概述**：模块职责、在系统中的位置

2. **命名体系与易混淆函数对比**：本节分两个部分。

   **2.1 命名规律拆解**：将本模块所有函数名拆解为"前缀 + 模块名 + 操作"的组成部分，用表格展示命名规律。格式：

   | 前缀 | 模块/对象 | 操作 | 含义 |
   |------|----------|------|------|
   | `ddsi_` | `rmsg_` | `addbias` | 为 rmsg 的 refcount 增加一个 RDATA_BIAS |
   | `ddsi_` | `rdata_` | `addbias` | 委托层：转调 rmsg_addbias，附加 debug 断言 |

   末尾给出命名规律总结（1-3 条），例如："`ddsi_rdata_xxx` 是 `ddsi_rmsg_xxx` 的委托包装层，增加了 rdata 级别的断言检查"。

   **2.2 易混淆函数对比表**：列出本模块中名称相似、容易混淆的函数组，每组一张对比表。格式：

   | 对比维度 | 函数 A | 函数 B |
   |---------|--------|--------|
   | 操作对象 | ... | ... |
   | 调用者 | ... | ... |
   | 调用阶段 | ... | ... |
   | 附加逻辑 | ... | ... |
   | **一句话区分** | ... | ... |

   每张表最后一行必须是 **"一句话区分"** ，用最简洁的语言说清两者的本质差异。

3. **API Signatures**：该模块所有函数的完整签名（代码块）。开头附带调用关系图（Mermaid），展示函数之间的调用层次。每个函数包含两行注释：第一行说明用途，第二行以 `场景：` 开头说明何时/谁调用此函数。格式：

   ```c
   static void ddsi_rmsg_addbias (struct ddsi_rmsg *rmsg);
     // 为 rmsg 的 refcount 增加一个 RDATA_BIAS 偏置
     // 场景：defrag 模块决定保留某个 rdata 时，由接收线程在 uncommitted 阶段调用
   ```

   包括公开 API 和文档中分析到的内部函数，不可省略。

4. **数据结构深度解析**：每个结构体的分析包含以下子部分。

   **4.a 结构体存在的理由**：在展示结构定义之前，先用引用块回答"为什么需要这个结构体"，说明如果没有它系统会面临什么问题。

   **4.b 结构定义**：展示完整的 struct 定义源码（遵守真实代码忠实性规则）。

   **4.c 字段三层分析表**：每个字段一行，三列分析。格式：

   | 字段 | 设计动机（为什么需要） | 反事实（如果去掉会怎样） | 替代方案（还能怎么做） |
   |------|----------------------|------------------------|----------------------|
   | `field_name` | 需要它因为... | 如果去掉会导致... | 也可以用...，但代价是... |

   **4.d 生命周期状态图**：使用 Mermaid stateDiagram-v2 展示结构体从创建到销毁的完整状态流转。

5. **函数逐行精讲**：本模块所有函数都按以下统一格式做深度分析。

   **5.a 场景卡片**（每个函数开头必须有）：

   > **函数：`function_name`**
   > - **调用时机**：何时触发
   > - **典型调用者**：哪个函数/模块调用它
   > - **前置条件**：调用前必须满足的状态
   > - **目的**：一句话说明这个函数要解决什么问题

   **5.b 逐行注释式精讲**：展示函数完整源码（通过 Read 读取，遵守真实代码忠实性规则），每一行代码后面紧跟一行中文注释行，以 `// →` 开头。格式：

   ```c
   static void example_func (struct example *obj, int param)
   // → 函数签名：接收对象指针和参数
   {
   // → 函数体开始
     assert (param >= 0);
     // → 断言：param 不能为负，负值意味着上游逻辑有 bug
     obj->field = param;
     // → 将参数存入对象字段，后续 xxx 函数会读取此值
   }
   // → 函数体结束
   ```

   **逐行注释规则：**
   - 每一行源码（空行除外）后面必须有 `// →` 注释行
   - 注释不仅要说"这行做了什么"，还要说"为什么这样做"或"如果不这样做会怎样"
   - assert / trace / debug 宏也必须注释，解释它们在防御什么错误场景
   - 函数最后一个 `}` 后附带一行总结性注释，说明"如果执行到这里意味着什么"

6. **关键算法剖析**：算法思想、时间复杂度、边界处理
7. **设计决策分析**：为什么这样设计、权衡考虑、替代方案
8. **学习检查点**：📝 本章小结（3-5 个要点）+ 🤔 思考题（2-3 个引导性问题）
````

**Step 2: 验证修改**

Run: `grep -c "命名体系\|逐行精讲\|三层分析\|场景卡片" study-master-skill/SKILL.md`
Expected: 至少 4 个匹配

**Step 3: Commit**

```bash
git add -f study-master-skill/SKILL.md
git commit -m "feat(study-master): restructure module chapters from 7 to 9 sections

Add Section 2 (naming disambiguation) and Section 5 (line-by-line
function analysis). Enhance Section 3 (API Signatures with scene
descriptions) and Section 4 (three-layer field analysis)."
```

---

### Task 3: 更新 Mermaid 图表要求

**Files:**
- Modify: `study-master-skill/SKILL.md:112`

**Step 1: 更新 Mermaid 要求**

将：

```markdown
- **Mermaid 图表**：每个模块章节至少 2 个 Mermaid 图（如调用关系图 + 时序图/状态图），帮助读者从不同角度理解模块。
```

替换为：

```markdown
- **Mermaid 图表**：每个模块章节至少 3 个 Mermaid 图：Section 3 的调用关系图（必须）、Section 4 的生命周期状态图（每个结构体一个）、以及至少 1 个辅助图（时序图/流程图等）。Section 5（函数逐行精讲）不要求 Mermaid 图，逐行注释本身即为最细粒度的展示。
```

**Step 2: 验证修改**

Run: `grep -n "至少 3 个 Mermaid" study-master-skill/SKILL.md`
Expected: 找到更新后的行

**Step 3: Commit**

```bash
git add -f study-master-skill/SKILL.md
git commit -m "feat(study-master): update Mermaid diagram requirements for 9-section structure"
```

---

### Task 4: 更新文档结构概要表

**Files:**
- Modify: `study-master-skill/SKILL.md:185-192`

**Step 1: 替换概要表**

将：

```markdown
## 文档结构概要

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构图、学习路线 |
| `01-module-xxx.md` | 模块深度解析：概述、代码展示、数据结构、算法、设计决策、检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 元数据 |
```

替换为：

```markdown
## 文档结构概要

| 文件 | 内容 |
|------|------|
| `00-overview.md` | 快速导览：项目简介、核心概念、典型场景、架构图、学习路线 |
| `01-module-xxx.md` | 模块深度解析（8 节）：概述、命名消歧、API 签名（含场景）、数据结构（三层字段分析）、函数逐行精讲（场景卡片 + 逐行注释）、算法、设计决策、检查点 |
| `appendix-references.md` | 参考资料索引 |
| `.study-meta.json` | 元数据 |
```

**Step 2: 验证修改**

Run: `grep "命名消歧\|逐行精讲" study-master-skill/SKILL.md`
Expected: 在概要表中找到匹配

**Step 3: Commit**

```bash
git add -f study-master-skill/SKILL.md
git commit -m "feat(study-master): update document structure overview table"
```

---

### Task 5: 最终验证

**Step 1: 通读完整 SKILL.md 检查一致性**

Run: `cat study-master-skill/SKILL.md`

检查项：
- [ ] Phase 1.4 包含"识别易混淆函数组"步骤
- [ ] 模块章节结构为"8 节必须齐全"
- [ ] Section 2 有命名拆解表 + 对比表格式
- [ ] Section 3 有两行注释格式（用途 + 场景）
- [ ] Section 4 有 4.a/4.b/4.c/4.d 子部分
- [ ] Section 5 有场景卡片 + 逐行注释规则
- [ ] Mermaid 要求更新为"至少 3 个"
- [ ] 文档结构概要表反映 8 节内容
- [ ] 无格式错误（未闭合代码块、表格对齐等）

**Step 2: 如有问题，修复并提交**

```bash
git add -f study-master-skill/SKILL.md
git commit -m "fix(study-master): fix consistency issues in SKILL.md"
```
