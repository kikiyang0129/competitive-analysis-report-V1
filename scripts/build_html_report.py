#!/usr/bin/env python3
"""把结构化 Markdown 报告转换为自包含 HTML。仅依赖 Python 标准库。"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def inline(text: str) -> str:
    """处理行内代码和链接。"""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        r'<a href="\1" target="_blank" rel="noopener">\1</a>',
        escaped,
    )
    return escaped


def split_table_row(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def is_sep(row: str) -> bool:
    cells = split_table_row(row)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells)


def slug(index: int) -> str:
    return f"section-{index}"


def markdown_to_html(markdown: str) -> tuple[str, str, str]:
    lines = markdown.splitlines()
    html_parts: list[str] = []
    toc: list[tuple[int, str, str]] = []
    para: list[str] = []
    list_mode: str | None = None
    heading_count = 0
    title = "竞品分析报告"
    i = 0

    def close_para() -> None:
        nonlocal para
        if para:
            html_parts.append("<p>" + inline(" ".join(para).strip()) + "</p>")
            para = []

    def close_list() -> None:
        nonlocal list_mode
        if list_mode:
            html_parts.append(f"</{list_mode}>")
            list_mode = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            close_para()
            close_list()
            i += 1
            continue

        if stripped.startswith("```"):
            close_para()
            close_list()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            html_parts.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_sep(lines[i + 1]):
            close_para()
            close_list()
            headers = split_table_row(stripped)
            aligns = split_table_row(lines[i + 1])
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            table = ['<div class="table-wrap"><table>']
            table.append("<thead><tr>")
            for idx, head in enumerate(headers):
                align = "right" if idx < len(aligns) and aligns[idx].endswith(":") and not aligns[idx].startswith(":") else "left"
                table.append(f'<th class="align-{align}">{inline(head)}</th>')
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                for idx, cell in enumerate(row):
                    align = "right" if idx < len(aligns) and aligns[idx].endswith(":") and not aligns[idx].startswith(":") else "left"
                    score_class = " score" if re.fullmatch(r"[1-5]", cell) else ""
                    table.append(f'<td class="align-{align}{score_class}">{inline(cell)}</td>')
                table.append("</tr>")
            table.append("</tbody></table></div>")
            html_parts.append("".join(table))
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            close_para()
            close_list()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and title == "竞品分析报告":
                title = text
            heading_count += 1
            hid = slug(heading_count)
            toc.append((level, text, hid))
            html_parts.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
            i += 1
            continue

        if re.match(r"^-\s+", stripped):
            close_para()
            if list_mode != "ul":
                close_list()
                html_parts.append("<ul>")
                list_mode = "ul"
            item_text = re.sub(r"^-\s+", "", stripped)
            html_parts.append(f"<li>{inline(item_text)}</li>")
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            close_para()
            if list_mode != "ol":
                close_list()
                html_parts.append("<ol>")
                list_mode = "ol"
            item_text = re.sub(r"^\d+\.\s+", "", stripped)
            html_parts.append(f"<li>{inline(item_text)}</li>")
            i += 1
            continue

        close_list()
        para.append(stripped)
        i += 1

    close_para()
    close_list()

    toc_html = ['<nav class="toc" aria-label="报告目录"><div class="toc-title">目录</div>']
    for level, text, hid in toc:
        if level == 1:
            continue
        toc_html.append(f'<a class="toc-l{level}" href="#{hid}">{inline(text)}</a>')
    toc_html.append("</nav>")
    return title, "\n".join(html_parts), "".join(toc_html)


def main() -> None:
    parser = argparse.ArgumentParser(description="把 Markdown 竞品分析报告转换为 HTML")
    parser.add_argument("input", help="输入 Markdown 文件")
    parser.add_argument("--output", "-o", required=True, help="输出 HTML 文件")
    parser.add_argument("--template", help="HTML 模板路径，默认使用 assets/html-report-template.html")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    script_dir = Path(__file__).resolve().parent
    default_template = script_dir.parent / "assets" / "html-report-template.html"
    template_path = Path(args.template) if args.template else default_template

    markdown = input_path.read_text(encoding="utf-8")
    title, content, toc = markdown_to_html(markdown)
    template = template_path.read_text(encoding="utf-8")
    html_doc = template.replace("{{TITLE}}", html.escape(title, quote=False))
    html_doc = html_doc.replace("{{TOC}}", toc)
    html_doc = html_doc.replace("{{CONTENT}}", content)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
