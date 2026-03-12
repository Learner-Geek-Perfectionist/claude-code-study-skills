#!/usr/bin/env python3
"""study-master 格式验证脚本"""
import sys
import re
from pathlib import Path
from typing import List

class ValidationError:
    def __init__(self, line: int, rule: str, message: str):
        self.line = line
        self.rule = rule
        self.message = message

class FormatValidator:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text(encoding='utf-8')
        self.lines = self.content.splitlines()
        self.errors: List[ValidationError] = []

    def validate(self) -> bool:
        self.check_replacement_chars()
        self.check_unicode_math()
        self.check_ascii_art()
        self.check_code_block_languages()
        self.check_source_location_format()
        self.check_absolute_paths()
        self.check_backtick_in_links()
        return len(self.errors) == 0

    def report(self):
        if not self.errors:
            return

        print(f"\n🚫 FORMAT VALIDATION FAILED: {self.file_path.name}", file=sys.stderr)
        print(f"   Found {len(self.errors)} issue(s)\n", file=sys.stderr)

        by_rule = {}
        for err in self.errors:
            by_rule.setdefault(err.rule, []).append(err)

        for rule, errs in sorted(by_rule.items()):
            print(f"  [{rule}] {len(errs)} issue(s):", file=sys.stderr)
            for err in errs[:3]:
                print(f"    Line {err.line}: {err.message}", file=sys.stderr)
            if len(errs) > 3:
                print(f"    ... and {len(errs) - 3} more", file=sys.stderr)

        print("\n💡 Fix these issues using Edit tool.\n", file=sys.stderr)

    def check_replacement_chars(self):
        """检测 Unicode 替换字符 U+FFFD"""
        for i, line in enumerate(self.lines, 1):
            if '\ufffd' in line:
                self.errors.append(ValidationError(i, 'encoding', "检测到乱码字符 U+FFFD"))

    def check_unicode_math(self):
        """检查 Unicode 数学符号"""
        math_chars = {
            '²': '$^2$', '³': '$^3$', '⁰': '$^0$', '¹': '$^1$',
            '⁴': '$^4$', '⁵': '$^5$', '⁶': '$^6$', '⁷': '$^7$',
            '⁸': '$^8$', '⁹': '$^9$',
            '×': r'$\times$', '÷': r'$\div$',
            '≥': r'$\geq$', '≤': r'$\leq$',
            '≠': r'$\neq$', '≈': r'$\approx$'
        }
        for i, line in enumerate(self.lines, 1):
            for char, latex in math_chars.items():
                if char in line:
                    self.errors.append(ValidationError(i, 'math-symbol', f"Unicode 数学符号 '{char}' 应替换为 {latex}"))

    def check_ascii_art(self):
        """检查 ASCII art"""
        pattern = r'[\u2500-\u257F]|[┌┐└┘├┤┬┴┼─│]'
        for i, line in enumerate(self.lines, 1):
            if re.search(pattern, line):
                self.errors.append(ValidationError(i, 'ascii-art', "禁止使用 ASCII art，请使用 Mermaid 图表"))

    def check_code_block_languages(self):
        """检查代码块语言标识"""
        in_code_block = False
        for i, line in enumerate(self.lines, 1):
            if line.startswith('```'):
                if not in_code_block:
                    lang = line[3:].strip()
                    if not lang:
                        self.errors.append(ValidationError(i, 'code-language', "代码块缺少语言标识"))
                    in_code_block = True
                else:
                    in_code_block = False

    def check_source_location_format(self):
        """检查源码位置格式"""
        pattern = r'^>\s*📍\s*源码：\[([^:]+):(\d+)-(\d+)\]\(([^)]+#L\d+)\)'
        for i, line in enumerate(self.lines, 1):
            if '📍' in line and '源码' in line:
                if not re.match(pattern, line):
                    self.errors.append(ValidationError(i, 'source-location', "源码位置格式错误，应为：> 📍 源码：[文件名:起始行-结束行](路径#L起始行)"))

    def check_absolute_paths(self):
        """检查 file:/// 绝对路径"""
        for i, line in enumerate(self.lines, 1):
            if 'file:///' in line:
                self.errors.append(ValidationError(i, 'absolute-path', "禁止使用 file:/// 绝对路径，请使用相对路径"))

    def check_backtick_in_links(self):
        """检查链接文本中的反引号"""
        pattern = r'\[`[^`]+`\]\('
        for i, line in enumerate(self.lines, 1):
            if re.search(pattern, line):
                self.errors.append(ValidationError(i, 'link-backtick', "链接文本中不应包含反引号"))

def main():
    if len(sys.argv) != 2:
        print("Usage: validate_format.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    validator = FormatValidator(file_path)
    if validator.validate():
        sys.exit(0)
    else:
        validator.report()
        sys.exit(2)

if __name__ == "__main__":
    main()
