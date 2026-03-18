#!/usr/bin/env python3
"""study-master 格式验证脚本"""
import sys
import re
from pathlib import Path
from typing import List, Iterator, Tuple

class ValidationError:
    def __init__(self, line: int, rule: str, message: str):
        self.line = line
        self.rule = rule
        self.message = message

class FormatValidator:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lines = file_path.read_text(encoding='utf-8').splitlines()
        self.errors: List[ValidationError] = []

    def _iter_content_lines(self) -> Iterator[Tuple[int, str]]:
        """遍历非代码块内的行，返回 (行号, 行内容)"""
        in_code_block = False
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if not in_code_block:
                yield i, line

    def _iter_lines_with_code_context(self) -> Iterator[Tuple[int, str, bool, str]]:
        """遍历所有行，返回 (行号, 行内容, 是否在代码块内, 代码块语言)"""
        in_code_block = False
        code_block_lang = ''
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('```'):
                if not in_code_block:
                    code_block_lang = line.strip()[3:].strip().lower()
                    in_code_block = True
                else:
                    in_code_block = False
                    code_block_lang = ''
                yield i, line, in_code_block, code_block_lang
                continue
            yield i, line, in_code_block, code_block_lang

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
        self.check_crossref_chinese_anchors_and_targets()
        self.check_api_signature_section()
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
        unicode_pattern = re.compile(r'[\u2500-\u257F]|[┌┐└┘├┤┬┴┼─│]')
        ascii_table_pattern = re.compile(r'^\s*\+[-=+]{3,}\+')

        for i, line, in_code, lang in self._iter_lines_with_code_context():
            # 只有真实代码块（c, bash, python 等）跳过，text 块不跳过
            if in_code and lang not in ('', 'text'):
                continue
            if unicode_pattern.search(line):
                self.errors.append(ValidationError(i, 'ascii-art', "禁止使用 Unicode box-drawing 字符，请使用 Mermaid 图表"))
            if ascii_table_pattern.match(line):
                self.errors.append(ValidationError(i, 'ascii-art', "禁止使用 ASCII 表格（+---+），请使用 Mermaid 图表或 Markdown 表格"))

    def check_code_block_languages(self):
        """检查代码块语言标识"""
        for i, line, in_code, lang in self._iter_lines_with_code_context():
            # 检测刚进入代码块时的语言标识（in_code 刚变为 True 的那一行）
            if line.strip().startswith('```') and in_code and not lang:
                self.errors.append(ValidationError(i, 'code-language', "代码块缺少语言标识"))

    def check_source_location_format(self):
        """检查源码位置格式"""
        pattern = re.compile(r'^>\s*📍\s*源码：\[([^:]+):(\d+)-(\d+)\]\(([^)]+#L\d+)\)')
        for i, line in enumerate(self.lines, 1):
            if '📍' in line and '源码' in line:
                if not pattern.match(line):
                    self.errors.append(ValidationError(i, 'source-location', "源码位置格式错误，应为：> 📍 源码：[文件名:起始行-结束行](路径#L起始行)"))

    def check_absolute_paths(self):
        """检查 file:/// 绝对路径"""
        for i, line in enumerate(self.lines, 1):
            if 'file:///' in line:
                self.errors.append(ValidationError(i, 'absolute-path', "禁止使用 file:/// 绝对路径，请使用相对路径"))

    def check_backtick_in_links(self):
        """检查链接文本中的反引号"""
        pattern = re.compile(r'\[`[^`]+`\]\(')
        for i, line in enumerate(self.lines, 1):
            if pattern.search(line):
                self.errors.append(ValidationError(i, 'link-backtick', "链接文本中不应包含反引号"))

    def check_source_link_existence(self):
        """检查源码链接路径是否指向真实存在的文件"""
        link_pattern = re.compile(r'\[([^\]]+)\]\(<?([^<>)]+)>?\)')
        for i, line in self._iter_content_lines():
            for match in link_pattern.finditer(line):
                href = match.group(2)
                if href.startswith(('http://', 'https://', '#', './')):
                    continue
                if not href.startswith('../'):
                    continue
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
        for i, line in self._iter_content_lines():
            for match in crossref_pattern.finditer(line):
                text = match.group(1)
                href = match.group(2)
                if '#' in href:
                    continue
                filename = href.split('/')[-1]
                bare_name = filename.replace('.md', '')
                if text == filename or text == bare_name:
                    continue
                if re.match(r'^第\s*\d+\s*章', text):
                    continue
                if re.match(r'^\d{2}-', text):
                    continue
                self.errors.append(ValidationError(
                    i, 'crossref-anchor',
                    f"交叉引用缺少锚点：[{text}]({href})，应为 [{text}]({href}#锚点)"
                ))

    def check_crossref_chinese_anchors_and_targets(self):
        """检查跨文件锚点：中文兼容性 + 目标标题存在性"""
        crossref_pattern = re.compile(r'\[([^\]]+)\]\((\./[^)]+\.md)#([^)]+)\)')
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        anchor_cache = {}
        for i, line in self._iter_content_lines():
            for match in crossref_pattern.finditer(line):
                text = match.group(1)
                file_ref = match.group(2)
                anchor = match.group(3)
                if chinese_pattern.search(anchor):
                    self.errors.append(ValidationError(
                        i, 'crossref-chinese-anchor',
                        f"跨文件锚点含中文：[{text}]({file_ref}#{anchor})。"
                        f"修复步骤：1) 用 Edit 将 {file_ref} 中对应的中文标题改为英文；"
                        f"2) 用 Edit 将本文件中的链接锚点更新为新的英文锚点"
                    ))
                target = self.file_path.parent / file_ref
                if not target.exists():
                    continue
                if file_ref not in anchor_cache:
                    anchor_cache[file_ref] = self._build_anchor_set(target)
                if anchor not in anchor_cache[file_ref]:
                    self.errors.append(ValidationError(
                        i, 'crossref-target',
                        f"跨文件锚点不存在：[{text}]({file_ref}#{anchor})，目标文件无此标题"
                    ))

    def _build_anchor_set(self, target: Path) -> set:
        """从目标文件的标题构建锚点集合"""
        heading_re = re.compile(r'^#+\s*')
        clean_re = re.compile(r'[^\w\u4e00-\u9fff -]')
        anchors = set()
        for line in target.read_text(encoding='utf-8').splitlines():
            if not line.startswith('#'):
                continue
            heading_text = heading_re.sub('', line)
            auto = clean_re.sub('', heading_text.lower().strip()).replace(' ', '-')
            anchors.add(auto)
        return anchors

    def check_api_signature_section(self):
        """检查模块章节是否包含 API 签名速查节（仅检查 01-NN 章节）"""
        filename = self.file_path.name
        if not re.match(r'^(0[1-9]|[1-9]\d)', filename):
            return

        has_api_section = False
        api_section_has_code = False
        in_api_section = False
        api_heading_re = re.compile(r'^#{2,}\s+.*API.*(签名|Signature)', re.IGNORECASE)
        section_heading_re = re.compile(r'^#{2,}\s+')
        for line in self.lines:
            if api_heading_re.match(line):
                has_api_section = True
                in_api_section = True
                continue
            if in_api_section and section_heading_re.match(line) and not api_heading_re.match(line):
                in_api_section = False
            if in_api_section and line.strip().startswith('```c'):
                api_section_has_code = True

        if not has_api_section:
            self.errors.append(ValidationError(
                1, 'api-signature-section',
                "模块章节缺少「API 签名速查」节，必须包含所有函数的完整 C 签名"
            ))
        elif not api_section_has_code:
            self.errors.append(ValidationError(
                1, 'api-signature-section',
                "「API 签名速查」节缺少 ```c 代码块，必须展示完整函数签名"
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
