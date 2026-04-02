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

在方案 2 基础上增加仓库级导航内容，例如当前收录列表、兼容矩阵、后续扩展方向与仓库级快速导览。

优点：

- 品牌表达最完整
- 与 `agent-study-skills` 的仓库级命名最匹配
- README 可以同时承担品牌首页与当前 skill 索引页的角色

缺点：

- 当前仓库只有一个 skill，需要控制仓库级内容的篇幅
- README 重写范围最大，需要避免把未来规划写成空洞口号

## 决策

采用方案 3。

原因：

- 用户明确选择采用仓库索引化表达
- `agent-study-skills` 作为仓库名，本身就更适合用仓库首页的方式来承载
- 即使当前只有一个 `study-master`，也可以通过轻量索引结构提前建立可扩展的 README 骨架
- 继续保留 `study-master` 作为当前首个收录 skill 的独立身份，不影响现有安装与使用路径

## README 重写范围

### 保留内容

- `study-master` 的核心特性说明
- 安装步骤中的 `study-master-skill/` 子目录入口
- 使用方式、工作流程、组件说明、Hook 校验说明

### 重写内容

- 顶部标题改为仓库级标题，例如 `Agent Study Skills`
- 开头介绍改为仓库级描述，强调支持 Claude Code、Codex 等 agent CLI
- 增加仓库级“当前收录”区块，明确当前仅收录 `study-master`
- 增加轻量兼容矩阵，说明当前主要支持的 CLI / Hook 方式 / 安装入口
- 增加仓库级快速导览，让读者先理解仓库定位，再进入具体 skill
- 增加轻量路线图区块，用于表达后续可继续收录更多学习型 skill 的方向
- 安装示例改为新的 clone 路径 `agent-study-skills`
- 局部措辞从“这个 skill”调整为“仓库中的 `study-master` skill”或等价表达

## README 目标结构

重写后的 README 应保持“先仓库、后 skill”的结构，建议按以下顺序组织：

1. 仓库级标题与一句话定位
2. 仓库简介
3. 当前收录 skills 列表
4. 兼容矩阵
5. 快速开始
6. 当前重点 skill：`study-master`
7. `study-master` 的特性、工作流程、生成产物与组件说明
8. 轻量路线图
9. License

## 具体变更

1. 更新 `README.md` 标题与开场文案
2. 更新 `README.md` 中的 clone URL
3. 更新 `README.md` 中的 `cd` 路径
4. 为 README 增加“当前收录 skills”仓库索引区块
5. 为 README 增加轻量兼容矩阵
6. 为 README 增加轻量路线图区块
7. 将 README 组织为仓库级说明 + `study-master` skill 说明
8. 保持 `study-master-skill/` 目录名与 `study-master` skill 名不变

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

### 风险 2：仓库级内容过多，掩盖当前只有一个 skill 的事实

缓解：

- 将“当前收录”放在前面，并明确写出当前只有 `study-master`
- 将路线图保持在轻量级别，只表达方向，不堆砌空泛内容

### 风险 3：用户误以为 skill 名也要变

缓解：

- 在 README 和本设计中明确声明 skill 名与目录名保持不变

### 风险 4：本地 remote 提前修改导致仓库不可用

缓解：

- 本次不直接修改 `origin`
- 只在 GitHub rename 完成后再更新 remote URL

## 验收标准

- README 不再出现 `claude-code-study-skills`
- README 的安装示例使用 `agent-study-skills`
- README 包含仓库级“当前收录 skills”区块
- README 包含轻量兼容矩阵
- README 包含轻量路线图区块
- README 清楚区分仓库品牌与 `study-master` skill 身份
- 仓库内脚本、skill 名称、目录名保持原样
