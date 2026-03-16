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
        self.check_source_link_existence()
        self.check_crossref_anchors()
        self.check_crossref_targets()
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
        """检查 ASCII art（包括 ASCII 和 Unicode box-drawing）"""
        # Unicode box-drawing 字符
        unicode_pattern = r'[\u2500-\u257F]|[┌┐└┘├┤┬┴┼─│]'
        # ASCII 表格模式：+---+---+ 风格（非 Markdown 表格）
        ascii_table_pattern = r'^\s*\+[-=+]{3,}\+'

        in_code_block = False
        code_block_lang = ''
        for i, line in enumerate(self.lines, 1):
            # 跟踪代码块状态
            if line.strip().startswith('```'):
                if not in_code_block:
                    code_block_lang = line.strip()[3:].strip().lower()
                    in_code_block = True
                else:
                    in_code_block = False
                    code_block_lang = ''
                continue

            # 只有真实代码块（c, bash, python 等）跳过检查
            # text 代码块不跳过——ASCII art 常藏在 text 块里
            if in_code_block and code_block_lang not in ('', 'text'):
                continue

            # 检测 Unicode box-drawing
            if re.search(unicode_pattern, line):
                self.errors.append(ValidationError(i, 'ascii-art', "禁止使用 Unicode box-drawing 字符，请使用 Mermaid 图表"))

            # 检测 ASCII 表格（排除合法的 Markdown 表格分隔行）
            if re.match(ascii_table_pattern, line):
                self.errors.append(ValidationError(i, 'ascii-art', "禁止使用 ASCII 表格（+---+），请使用 Mermaid 图表或 Markdown 表格"))

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

    def check_source_link_existence(self):
        """检查源码链接路径是否指向真实存在的文件"""
        # Match both [text](href) and [text](<href with spaces>)
        link_pattern = re.compile(r'\[([^\]]+)\]\(<?([^<>)]+)>?\)')
        in_code_block = False
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            for match in link_pattern.finditer(line):
                href = match.group(2)
                # Skip URLs, same-page anchors, and cross-references between study docs
                if href.startswith(('http://', 'https://', '#', './')):
                    continue
                # Only check relative paths that go up (source code links)
                if not href.startswith('../'):
                    continue
                # Strip fragment (#L264, #section-name, etc.)
                path_part = href.split('#')[0]
                resolved = (self.file_path.parent / path_part).resolve()
                if not resolved.exists():
                    self.errors.append(ValidationError(
                        i, 'source-link-path',
                        f"源码链接路径不存在：{path_part}"
                    ))

    def check_crossref_anchors(self):
        """检查文档间交叉引用是否包含锚点"""
        crossref_pattern = re.compile(r'\[([^\]]+)\]\((\./[^)]+\.md(?:#[^)]*)?)\)')
        in_code_block = False
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            for match in crossref_pattern.finditer(line):
                text = match.group(1)
                href = match.group(2)
                # Skip if already has anchor
                if '#' in href:
                    continue
                # Skip chapter navigation links where text looks like a filename
                # e.g. [00-overview.md](./00-overview.md) or [快速导览](./00-overview.md)
                filename = href.split('/')[-1]
                bare_name = filename.replace('.md', '')
                if text == filename or text == bare_name:
                    continue
                # Skip links where text is a chapter title pattern (starts with 第/chapter nav)
                if re.match(r'^第\s*\d+\s*章', text):
                    continue
                # Skip links where text matches NN-xxx pattern (chapter file names)
                if re.match(r'^\d{2}-', text):
                    continue
                self.errors.append(ValidationError(
                    i, 'crossref-anchor',
                    f"交叉引用缺少锚点：[{text}]({href})，应为 [{text}]({href}#锚点)"
                ))

    def check_crossref_targets(self):
        """检查跨文件锚点的目标标题是否存在"""
        crossref_pattern = re.compile(r'\[([^\]]+)\]\((\./[^)]+\.md)#([^)]+)\)')
        in_code_block = False
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            for match in crossref_pattern.finditer(line):
                text = match.group(1)
                file_path = match.group(2)
                anchor = match.group(3)
                target = self.file_path.parent / file_path
                if not target.exists():
                    continue  # check_source_link_existence handles missing files
                target_content = target.read_text(encoding='utf-8')
                # Build anchor set from headings in target file
                target_anchors = set()
                for tline in target_content.splitlines():
                    if tline.startswith('#'):
                        heading_text = re.sub(r'^#+\s*', '', tline)
                        # Check for custom {#id} anchor
                        custom = re.search(r'\{#([^}]+)\}', heading_text)
                        if custom:
                            target_anchors.add(custom.group(1))
                            heading_text = re.sub(r'\s*\{#[^}]+\}', '', heading_text)
                        # Generate GFM auto-anchor
                        auto = heading_text.lower().strip()
                        auto = re.sub(r'[^\w\u4e00-\u9fff -]', '', auto)
                        auto = auto.replace(' ', '-')
                        target_anchors.add(auto)
                if anchor not in target_anchors:
                    self.errors.append(ValidationError(
                        i, 'crossref-target',
                        f"跨文件锚点不存在：[{text}]({file_path}#{anchor})，目标文件无此标题"
                    ))

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
