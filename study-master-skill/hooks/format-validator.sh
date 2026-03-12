#!/bin/bash

# Format Validator Hook
# 检查 Markdown 文档是否符合 format-rules.md 规范

set -e

TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "用法: $0 <文件或目录>"
    exit 1
fi

VIOLATIONS=0

# 检查单个文件
check_file() {
    local file="$1"
    local line_num=0

    echo "检查文件: $file"

    while IFS= read -r line; do
        ((line_num++))

        # 1. 检测 file:/// 绝对路径
        if echo "$line" | grep -q "file:///"; then
            echo "  ❌ 行 $line_num: 发现 file:/// 绝对路径"
            ((VIOLATIONS++))
        fi

        # 2. 检测链接文本中的反引号
        if echo "$line" | grep -qE '\[`[^`]+`\]\('; then
            echo "  ❌ 行 $line_num: 链接文本中包含反引号"
            ((VIOLATIONS++))
        fi

        # 3. 检测 ASCII art 字符
        if echo "$line" | grep -qE '[┌┐└┘├┤│─┬┴┼]'; then
            echo "  ❌ 行 $line_num: 发现 ASCII art 字符，应使用 Mermaid"
            ((VIOLATIONS++))
        fi

        # 4. 检测 Unicode 数学符号
        if echo "$line" | grep -qE '[²³⁰¹⁴⁵⁶⁷⁸⁹×÷≥≤≠≈]'; then
            echo "  ❌ 行 $line_num: 发现 Unicode 数学符号，应使用 LaTeX 格式"
            ((VIOLATIONS++))
        fi

        # 5. 检测 U+FFFD 乱码字符
        if echo "$line" | grep -qP '\xEF\xBF\xBD'; then
            echo "  ❌ 行 $line_num: 发现乱码字符 U+FFFD"
            ((VIOLATIONS++))
        fi
    done < "$file"

    # 6. 检测无语言标识的代码块
    if grep -qE '^```$' "$file"; then
        echo "  ❌ 发现无语言标识的代码块"
        ((VIOLATIONS++))
    fi
}

# 主逻辑
if [ -f "$TARGET" ]; then
    # 单个文件
    check_file "$TARGET"
elif [ -d "$TARGET" ]; then
    # 目录：遍历所有 .md 文件
    find "$TARGET" -name "*.md" -type f | while read -r file; do
        check_file "$file"
    done
else
    echo "错误: $TARGET 不是有效的文件或目录"
    exit 1
fi

# 输出结果
echo ""
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ 格式检查通过"
    exit 0
else
    echo "❌ 发现 $VIOLATIONS 个格式违规"
    exit 1
fi

