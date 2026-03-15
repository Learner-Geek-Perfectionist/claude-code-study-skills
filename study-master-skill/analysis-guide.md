# 源码分析方法指南

本文件包含 study-master 的源码分析技术细节，在 Phase 1（源码分析）阶段按需参考。

## 1. LSP 环境检测

**仅 C/C++ 项目需要检测**，其他语言跳过。

检测步骤：
1. 查找 `compile_commands.json`：源码根目录 → 上级目录 → build/ 目录
2. 测试 LSP：`LSP documentSymbol <file> line:1 char:1`
3. 记录结果：✓ LSP 可用 / ✗ LSP 不可用

## 2. 分析方法对照表

根据 LSP 可用性选择分析方法：

| 分析任务 | LSP 可用 | LSP 不可用 |
|---------|---------|-----------|
| 获取符号列表 | `LSP documentSymbol` | Grep 搜索函数定义 |
| 识别核心 API | `LSP findReferences` 统计引用次数 | 基于文件位置和命名推断 |
| 构建模块依赖 | 基于符号的文件位置分组 | Glob/Grep 扫描 include/import |
| 获取函数签名 | `LSP hover <file> line char` | 从头文件/声明处提取 |
| 查找调用关系 | `LSP findReferences` | Grep 搜索函数名 |
| 构建调用树 | `prepareCallHierarchy` + `incomingCalls` + `outgoingCalls` | 手动推断 |

## 3. LSP 深度分析流程

当 LSP 可用时，执行以下深度分析：

1. **热点函数识别**：按 `findReferences` 引用次数排序，找出最核心的函数
2. **模块耦合度分析**：统计跨文件引用，识别高耦合模块
3. **API 稳定性评估**：公共 API 被多少文件调用（引用广度）
4. **调用深度分析**：用 `prepareCallHierarchy` + `incomingCalls` + `outgoingCalls` 构建完整调用树

**输出**：项目架构概览、核心模块列表、热点函数排名

## 4. 函数级深度分析工作流

主对话在 1M 上下文中对每个核心函数执行以下深度分析：

1. **获取签名**：LSP hover / 头文件提取
2. **查找调用关系**：LSP findReferences / Grep
3. **构建调用树**：LSP callHierarchy / 手动推断
4. **阅读源码**：Read 函数完整实现，理解内部逻辑
5. **深度解读**：
   - 函数的设计意图（不只是"做什么"，还有"为什么这样做"）
   - 关键代码段的逻辑解释
   - 错误处理策略和边界条件
   - 与其他模块的交互方式
6. **生成执行路径追踪**：
   - Mermaid sequenceDiagram 展示调用顺序
   - 标注参数值、返回值、状态变化
   - 区分：正常路径、错误处理、边界条件
7. **记录分析结论**：将以上分析结果保留在上下文中，供 Phase 2 直接生成文档时使用

LSP 可用时的标注格式：
- **函数签名**（来自 LSP hover）
- **调用关系**（共 X 次引用，来自 LSP findReferences）
- **调用树深度**：N 层（来自 LSP callHierarchy）

LSP 不可用时的标注格式：
- **函数签名**（从头文件提取）
- **调用关系**（基于 Grep 搜索）

## 5. 可视化类型选择

| 内容类型 | Mermaid 图表 | 示例场景 |
|---------|-------------|---------|
| 模块依赖、调用关系 | `graph TD/LR` | 函数调用链、模块架构 |
| 时序交互 | `sequenceDiagram` | 多模块协作、执行路径追踪 |
| 状态转换 | `stateDiagram-v2` | 对象生命周期、协议状态机 |
| 数据结构 | `classDiagram` | 结构体成员、类层次 |

