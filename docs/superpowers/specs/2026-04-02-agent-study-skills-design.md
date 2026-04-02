# Agent Study Skills 仓库品牌化重写设计

## 背景

当前仓库实际已经同时支持 Claude Code 和 Codex，但仓库名与 README 中的对外表述仍带有 `claude-code-study-skills` 的单平台色彩。这会造成仓库品牌与实际能力不一致，也会让后续扩展到更多 agent CLI 时显得受限。

本次调整只修改“仓库品牌层”：

- 仓库目标名称改为 `agent-study-skills`
- 保留 `study-master-skill/` 目录名不变
- 保留 `study-master` skill 名称不变

## 目标

- 让仓库品牌从单一 CLI 导向改为多 agent CLI 中性命名
- 让 README 的仓库级信息与新仓库名保持一致
- 为后续收录更多学习型 skill 预留扩展空间

## 非目标

- 不修改 `study-master` skill 的名称
- 不重命名 `study-master-skill/` 目录
- 不修改安装脚本中的 skill 安装目标名
- 不调整 Hook 行为或校验逻辑
- 不在本次变更中修改本地 `git remote`

## 方案对比

### 方案 1：轻品牌化

只改 README 标题、仓库介绍和 clone 示例。

优点：

- 改动最小
- 风险最低

缺点：

- 仓库名变了，但 README 结构仍像单一 skill 说明页
- 不利于未来扩展多个 skill

### 方案 2：中度品牌化

将 README 拆成“仓库层 + 当前 skill 层”两层叙事。仓库层介绍 `agent-study-skills` 的定位，skill 层继续介绍当前收录的 `study-master`。

优点：

- 与新仓库名一致
- 不影响现有 skill 包名和安装逻辑
- 为未来加入更多 skill 留出自然扩展位

缺点：

- 需要系统性重写 README 主体文案

### 方案 3：重品牌 + 仓库索引化

在方案 2 基础上增加仓库级路线图、兼容矩阵、收录列表等内容。

优点：

- 品牌表达最完整

缺点：

- 当前仓库只有一个 skill，信息密度会失衡
- 超出当前需求

## 决策

采用方案 2。

原因：

- 既能体现 `agent-study-skills` 的仓库级定位，又不会过度设计
- 保持 `study-master` 作为当前首个收录 skill 的独立身份
- 文档结构能平滑容纳未来新增 skill

## README 重写范围

### 保留内容

- `study-master` 的核心特性说明
- 安装步骤中的 `study-master-skill/` 子目录入口
- 使用方式、工作流程、组件说明、Hook 校验说明

### 重写内容

- 顶部标题改为仓库级标题，例如 `Agent Study Skills`
- 开头介绍改为仓库级描述，强调支持 Claude Code、Codex 等 agent CLI
- 增加“当前收录”或“仓库定位”区块，明确当前仅收录 `study-master`
- 安装示例改为新的 clone 路径 `agent-study-skills`
- 局部措辞从“这个 skill”调整为“仓库中的 `study-master` skill”或等价表达

## 具体变更

1. 更新 `README.md` 标题与开场文案
2. 更新 `README.md` 中的 clone URL
3. 更新 `README.md` 中的 `cd` 路径
4. 将 README 组织为仓库级说明 + `study-master` skill 说明
5. 保持 `study-master-skill/` 目录名与 `study-master` skill 名不变

## 外部手动步骤

以下步骤不在本仓库代码改动内完成，但需要在实际发布时执行：

1. 在 GitHub 上将仓库重命名为 `agent-study-skills`
2. GitHub rename 完成后，更新本地远端：

```bash
git remote set-url origin git@github.com:Learner-Geek-Perfectionist/agent-study-skills.git
```

## 风险与缓解

### 风险 1：README 品牌层与 skill 层混淆

缓解：

- 使用明确的小节划分仓库定位与当前 skill
- 在安装和使用部分持续强调 `study-master` 是当前收录的 skill

### 风险 2：用户误以为 skill 名也要变

缓解：

- 在 README 和本设计中明确声明 skill 名与目录名保持不变

### 风险 3：本地 remote 提前修改导致仓库不可用

缓解：

- 本次不直接修改 `origin`
- 只在 GitHub rename 完成后再更新 remote URL

## 验收标准

- README 不再出现 `claude-code-study-skills`
- README 的安装示例使用 `agent-study-skills`
- README 清楚区分仓库品牌与 `study-master` skill 身份
- 仓库内脚本、skill 名称、目录名保持原样
