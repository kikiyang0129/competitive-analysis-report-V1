#!/usr/bin/env python3
"""把结构化 Markdown 竞品分析报告转换为自包含可视化 HTML。仅依赖 Python 标准库。"""

from __future__ import annotations

import argparse
import html
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


COLOR_SET = ["#1d4ed8", "#0f9f8f", "#f97316", "#7c3aed", "#64748b", "#dc2626"]
PRIORITY_KEYS = {
    "must": "Must",
    "必须": "Must",
    "必须做": "Must",
    "should": "Should",
    "应该": "Should",
    "应该做": "Should",
    "could": "Could",
    "可以": "Could",
    "可以做": "Could",
}


@dataclass
class ScoreMatrix:
    headers: list[str]
    rows: list[list[str]]
    numeric_cols: list[int]
    title: str


@dataclass
class RenderState:
    title: str = "竞品分析报告"
    subtitle: str = "Competitive Analysis Report"
    heading_count: int = 0
    table_count: int = 0
    score_cell_count: int = 0
    score_matrix_count: int = 0
    visual_panel_count: int = 0
    source_count: int = 0
    path_detail_count: int = 0
    current_h2: str = ""
    current_h3: str = ""
    current_priority: str | None = None
    summary_items: list[str] | None = None
    priority_items: dict[str, list[str]] | None = None
    task_steps: list[str] | None = None

    def __post_init__(self) -> None:
        self.summary_items = []
        self.priority_items = {"Must": [], "Should": [], "Could": []}
        self.task_steps = []


def inline(text: str) -> str:
    """处理常用行内 Markdown。"""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        r'<a href="\1" target="_blank" rel="noopener">\1</a>',
        escaped,
    )
    return escaped


def strip_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text.strip()


def split_table_row(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def is_sep(row: str) -> bool:
    cells = split_table_row(row)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def slug(index: int) -> str:
    return f"section-{index}"


def score_value(text: str) -> float | None:
    clean = strip_inline(text)
    match = re.fullmatch(r"([1-5])(?:\.0)?", clean)
    if match:
        return float(match.group(1))
    return None


def is_score_matrix(headers: list[str], rows: list[list[str]]) -> list[int]:
    if len(headers) < 3 or len(rows) < 3:
        return []
    numeric_cols: list[int] = []
    for col_idx in range(1, len(headers)):
        values = 0
        total = 0
        for row in rows:
            if col_idx >= len(row):
                continue
            total += 1
            if score_value(row[col_idx]) is not None:
                values += 1
        if total and values / total >= 0.6:
            numeric_cols.append(col_idx)
    return numeric_cols if len(numeric_cols) >= 2 else []


def normalize_rows(rows: list[list[str]], size: int) -> list[list[str]]:
    return [row + [""] * max(0, size - len(row)) for row in rows]


def collect_signal(text: str, state: RenderState) -> None:
    clean = strip_inline(text)
    if not clean:
        return
    if len(state.summary_items or []) < 6 and re.search(r"摘要|结论|关键发现|核心发现", state.current_h2 + state.current_h3):
        state.summary_items.append(clean)
    priority_match = re.match(r"^(Must|Should|Could|必须做|应该做|可以做|必须|应该|可以)[：:\-\s]+(.+)$", clean, re.I)
    if priority_match:
        key = PRIORITY_KEYS.get(priority_match.group(1).lower(), PRIORITY_KEYS.get(priority_match.group(1), ""))
        if key and len(state.priority_items[key]) < 6:
            state.priority_items[key].append(priority_match.group(2).strip())
    elif state.current_priority and len(state.priority_items[state.current_priority]) < 6:
        state.priority_items[state.current_priority].append(clean)
    if not state.task_steps:
        arrows = "→" in clean or "->" in clean
        if arrows and re.search(r"路径|流程|步骤|任务", state.current_h2 + state.current_h3 + clean):
            flow_text = re.split(r"(?:竞品差异|行动判断|体验亮点|明显短板|可借鉴点|建议|判断)[：:]", clean)[0]
            parts = re.split(r"\s*(?:→|->)\s*", flow_text)
            parts = [part.strip(" .。；;") for part in parts if len(part.strip()) >= 2]
            if len(parts) >= 3:
                state.task_steps.extend(parts[:7])


def priority_from_heading(text: str) -> str | None:
    lower = text.lower()
    for raw, normalized in PRIORITY_KEYS.items():
        if raw in lower or raw in text:
            return normalized
    return None


def badge_class(text: str) -> str:
    clean = strip_inline(text).lower()
    if clean in {"must", "必须", "必须做"}:
        return "badge badge-must"
    if clean in {"should", "应该", "应该做"}:
        return "badge badge-should"
    if clean in {"could", "可以", "可以做"}:
        return "badge badge-could"
    if clean in {"直接竞品", "direct"}:
        return "badge badge-direct"
    if clean in {"间接竞品", "indirect"}:
        return "badge badge-indirect"
    if clean in {"替代方案", "substitute"}:
        return "badge badge-substitute"
    if clean in {"潜在竞品", "potential"}:
        return "badge badge-potential"
    return ""


def matrix_values(matrix: ScoreMatrix) -> dict[int, list[float]]:
    values: dict[int, list[float]] = {col: [] for col in matrix.numeric_cols}
    for row in matrix.rows:
        for col in matrix.numeric_cols:
            if col >= len(row):
                continue
            value = score_value(row[col])
            if value is not None:
                values[col].append(value)
    return values


def is_source_table(headers: list[str], title: str) -> bool:
    text = " ".join([title, *headers]).lower()
    has_source_context = bool(re.search(r"来源|参考资料|资料来源|source|reference", text))
    has_link_column = bool(re.search(r"链接|url|网址|link|来源", text))
    return has_source_context and has_link_column


def first_url(text: str) -> str:
    match = re.search(r"https?://[^\s|<>)，。；;]+", text)
    return match.group(0) if match else ""


def compact_url_label(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.netloc:
        return url
    path = parsed.path.strip("/")
    if not path:
        return parsed.netloc
    first_segment = path.split("/")[0]
    return f"{parsed.netloc}/{first_segment}..."


def clean_source_text(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    return text.strip(" ，,。；;()（）")


def render_source_cards(headers: list[str], rows: list[list[str]], title: str) -> str:
    rows = normalize_rows(rows, len(headers))
    id_idx = next((idx for idx, head in enumerate(headers) if re.search(r"编号|序号|id", head, re.I)), -1)
    url_idx = next((idx for idx, head in enumerate(headers) if re.search(r"链接|url|网址|link", head, re.I)), -1)
    title_idx = next((idx for idx, head in enumerate(headers) if re.search(r"来源|source|名称|资料", head, re.I)), -1)
    if title_idx == url_idx:
        title_idx = -1

    cards = []
    for row_number, row in enumerate(rows, start=1):
        url = first_url(row[url_idx]) if 0 <= url_idx < len(row) else ""
        if not url:
            url = next((first_url(cell) for cell in row if first_url(cell)), "")
        source_text = row[title_idx].strip() if 0 <= title_idx < len(row) else ""
        if not source_text:
            source_text = next((cell.strip() for cell in row if cell.strip() and not first_url(cell)), "")
        source_text = clean_source_text(source_text)
        if not source_text:
            source_text = compact_url_label(url) if url else f"来源 {row_number}"
        source_id = row[id_idx].strip() if 0 <= id_idx < len(row) and row[id_idx].strip() else f"S{row_number}"

        meta_items = []
        for idx, cell in enumerate(row):
            if idx in {id_idx, title_idx, url_idx} or not cell.strip():
                continue
            cleaned = clean_source_text(cell)
            if not cleaned:
                continue
            label = headers[idx] if idx < len(headers) and headers[idx] else "说明"
            meta_items.append(
                '<div class="source-meta-item">'
                f'<span class="source-meta-label">{inline(label)}</span>'
                f'<span class="source-meta-value">{inline(cleaned)}</span>'
                "</div>"
            )
        link_html = (
            f'<a class="source-link" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(compact_url_label(url))}</a>'
            if url
            else '<span class="source-link source-empty">未提供链接</span>'
        )
        cards.append(
            '<article class="source-card">'
            '<div class="source-card-head">'
            f'<span class="source-index">{inline(source_id)}</span>'
            f"<h3>{inline(source_text)}</h3>"
            "</div>"
            f"{link_html}"
            f'<div class="source-meta">{"".join(meta_items)}</div>'
            "</article>"
        )
    return (
        f'<section class="source-list" aria-label="{html.escape(title or "来源列表", quote=True)}">'
        '<div class="section-kicker">SOURCES</div>'
        f'<div class="source-grid">{"".join(cards)}</div>'
        "</section>"
    )


def render_table(headers: list[str], aligns: list[str], rows: list[list[str]], state: RenderState, title: str) -> str:
    state.table_count += 1
    rows = normalize_rows(rows, len(headers))
    if is_source_table(headers, title):
        return render_source_cards(headers, rows, title)
    if state.current_priority:
        for row in rows:
            if row and row[0].strip() and len(state.priority_items[state.current_priority]) < 6:
                state.priority_items[state.current_priority].append(strip_inline(row[0]))
    numeric_cols = is_score_matrix(headers, rows)
    is_matrix = bool(numeric_cols)
    if is_matrix:
        state.score_matrix_count += 1
    parts: list[str] = []
    if is_matrix and state.visual_panel_count < 3:
        matrix = ScoreMatrix(headers=headers, rows=rows, numeric_cols=numeric_cols, title=title)
        parts.append(render_matrix_visuals(matrix))
        state.visual_panel_count += 1
    table_class = " score-matrix" if is_matrix else ""
    parts.append(f'<div class="table-wrap{table_class}"><table>')
    parts.append("<thead><tr>")
    for idx, head in enumerate(headers):
        align = "right" if idx < len(aligns) and aligns[idx].endswith(":") and not aligns[idx].startswith(":") else "left"
        parts.append(f'<th class="align-{align}">{inline(head)}</th>')
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for idx, cell in enumerate(row[: len(headers)]):
            align = "right" if idx < len(aligns) and aligns[idx].endswith(":") and not aligns[idx].startswith(":") else "left"
            value = score_value(cell)
            score_class = ""
            if value is not None and idx in numeric_cols:
                state.score_cell_count += 1
                score_class = f" heat heat-{int(value)}"
            badge = badge_class(cell)
            content = f'<span class="{badge}">{inline(cell)}</span>' if badge else inline(cell)
            parts.append(f'<td class="align-{align}{score_class}">{content}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render_matrix_visuals(matrix: ScoreMatrix) -> str:
    return (
        '<section class="visual-panel">'
        '<div class="visual-head">'
        f'<div><span class="eyebrow">AUTO VISUAL</span><h3>{inline(matrix.title or "竞品能力概览")}</h3></div>'
        '<p>基于下方 1-5 分评分矩阵自动生成，帮助快速观察能力分布和相对优势。</p>'
        "</div>"
        '<div class="visual-grid">'
        f"{render_radar(matrix)}{render_quadrant(matrix)}{render_score_bars(matrix)}"
        "</div>"
        "</section>"
    )


def render_radar(matrix: ScoreMatrix) -> str:
    categories = [strip_inline(row[0])[:12] for row in matrix.rows[:6]]
    cols = matrix.numeric_cols[:4]
    if len(categories) < 3 or not cols:
        return ""
    width = 360
    height = 300
    cx = width / 2
    cy = height / 2 + 8
    radius = 92
    axis_points = []
    for idx in range(len(categories)):
        angle = -math.pi / 2 + idx * 2 * math.pi / len(categories)
        axis_points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius, angle))
    rings = []
    for level in range(1, 6):
        points = []
        for _, _, angle in axis_points:
            r = radius * level / 5
            points.append(f"{cx + math.cos(angle) * r:.1f},{cy + math.sin(angle) * r:.1f}")
        rings.append(f'<polygon points="{" ".join(points)}" class="radar-ring"/>')
    axes = []
    labels = []
    for idx, (x, y, angle) in enumerate(axis_points):
        axes.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" class="radar-axis"/>')
        lx = cx + math.cos(angle) * (radius + 24)
        ly = cy + math.sin(angle) * (radius + 24)
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" class="radar-label">{html.escape(categories[idx])}</text>')
    polygons = []
    legend = []
    for s_idx, col in enumerate(cols):
        points = []
        for row_idx, row in enumerate(matrix.rows[: len(categories)]):
            value = score_value(row[col]) or 0
            _, _, angle = axis_points[row_idx]
            r = radius * value / 5
            points.append(f"{cx + math.cos(angle) * r:.1f},{cy + math.sin(angle) * r:.1f}")
        color = COLOR_SET[s_idx % len(COLOR_SET)]
        polygons.append(f'<polygon points="{" ".join(points)}" fill="{color}" stroke="{color}" class="radar-series"/>')
        legend.append(f'<span><i style="background:{color}"></i>{inline(matrix.headers[col])}</span>')
    return (
        '<article class="chart-card radar-card">'
        '<div class="chart-title">竞品能力雷达图</div>'
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="竞品能力雷达图">{"".join(rings)}{"".join(axes)}{"".join(polygons)}{"".join(labels)}</svg>'
        f'<div class="chart-legend">{"".join(legend)}</div>'
        "</article>"
    )


def render_quadrant(matrix: ScoreMatrix) -> str:
    if len(matrix.rows) < 2 or len(matrix.numeric_cols) < 2:
        return ""
    x_label = strip_inline(matrix.rows[0][0])[:14]
    y_label = strip_inline(matrix.rows[1][0])[:14]
    width = 360
    height = 300
    left = 54
    top = 34
    chart_w = 250
    chart_h = 210

    def map_x(value: float) -> float:
        return left + (value - 1) / 4 * chart_w

    def map_y(value: float) -> float:
        return top + chart_h - (value - 1) / 4 * chart_h

    values = matrix_values(matrix)
    points = []
    legend = []
    placed: list[tuple[float, float]] = []
    offsets = [(0, 0), (12, -10), (-12, 10), (12, 12), (-12, -12), (0, 16), (0, -16), (16, 0)]
    for idx, col in enumerate(matrix.numeric_cols[:8]):
        x_value = score_value(matrix.rows[0][col]) or 1
        y_value = score_value(matrix.rows[1][col]) or 1
        x = map_x(x_value)
        y = map_y(y_value)
        for dx, dy in offsets:
            candidate_x = min(max(x + dx, left + 14), left + chart_w - 14)
            candidate_y = min(max(y + dy, top + 14), top + chart_h - 14)
            if all(math.hypot(candidate_x - px, candidate_y - py) >= 20 for px, py in placed):
                x, y = candidate_x, candidate_y
                break
        placed.append((x, y))
        col_values = values.get(col, [])
        avg = sum(col_values) / max(1, len(col_values))
        size = min(14, 7 + avg * 1.6)
        color = COLOR_SET[idx % len(COLOR_SET)]
        points.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{color}" class="quad-dot"/>'
            f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" class="quad-index">{idx + 1}</text>'
        )
        legend.append(
            '<span>'
            f'<i style="background:{color}">{idx + 1}</i>'
            f'{inline(matrix.headers[col])}'
            f'<small>{x_label} {x_value:.0f} / {y_label} {y_value:.0f}</small>'
            '</span>'
        )
    return (
        '<article class="chart-card quadrant-card">'
        '<div class="chart-title">定位四象限</div>'
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="定位四象限">'
        f'<line x1="{left}" y1="{top + chart_h / 2}" x2="{left + chart_w}" y2="{top + chart_h / 2}" class="quad-mid"/>'
        f'<line x1="{left + chart_w / 2}" y1="{top}" x2="{left + chart_w / 2}" y2="{top + chart_h}" class="quad-mid"/>'
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" class="quad-box"/>'
        f'<text x="{left + chart_w / 2}" y="{height - 18}" text-anchor="middle" class="axis-title">{html.escape(x_label)}</text>'
        f'<text x="18" y="{top + chart_h / 2}" text-anchor="middle" class="axis-title axis-y" transform="rotate(-90 18 {top + chart_h / 2})">{html.escape(y_label)}</text>'
        '<text x="54" y="264" class="axis-note">低</text><text x="296" y="264" class="axis-note">高</text>'
        '<text x="34" y="238" class="axis-note">低</text><text x="34" y="42" class="axis-note">高</text>'
        f'{"".join(points)}</svg>'
        f'<div class="quad-legend">{"".join(legend)}</div>'
        "</article>"
    )


def render_score_bars(matrix: ScoreMatrix) -> str:
    values = matrix_values(matrix)
    averages = []
    for col in matrix.numeric_cols:
        col_values = values.get(col, [])
        if col_values:
            averages.append((matrix.headers[col], sum(col_values) / len(col_values)))
    averages.sort(key=lambda item: item[1], reverse=True)
    bars = []
    for idx, (name, value) in enumerate(averages[:8]):
        width = max(8, value / 5 * 100)
        color = COLOR_SET[idx % len(COLOR_SET)]
        bars.append(
            '<div class="rank-row">'
            f'<span class="rank-name">{inline(name)}</span>'
            f'<span class="rank-bar"><i style="width:{width:.0f}%;background:{color}"></i></span>'
            f"<strong>{value:.1f}</strong>"
            "</div>"
        )
    return (
        '<article class="chart-card rank-card">'
        '<div class="chart-title">综合评分排行</div>'
        f'{"".join(bars)}'
        "</article>"
    )


def render_summary_cards(items: list[str]) -> str:
    if not items:
        return ""
    cards = []
    for idx, item in enumerate(items[:6], start=1):
        cards.append(
            '<article class="insight-card">'
            f"<span>{idx:02d}</span>"
            f"<p>{inline(item)}</p>"
            "</article>"
        )
    return f'<section class="insight-grid" aria-label="摘要结论">{"".join(cards)}</section>'


def render_priority_board(priority_items: dict[str, list[str]]) -> str:
    if not any(priority_items.values()):
        return ""
    labels = {
        "Must": ("Must", "必须做", "board-must"),
        "Should": ("Should", "应该做", "board-should"),
        "Could": ("Could", "可以做", "board-could"),
    }
    columns = []
    for key in ["Must", "Should", "Could"]:
        en, zh, cls = labels[key]
        items = priority_items.get(key, [])[:5]
        item_html = "".join(f"<li>{inline(item)}</li>" for item in items) if items else "<li>暂无明确条目</li>"
        columns.append(
            f'<article class="priority-col {cls}">'
            f"<h3><span>{en}</span>{zh}</h3>"
            f"<ol>{item_html}</ol>"
            "</article>"
        )
    return (
        '<section class="priority-board">'
        '<div class="section-kicker">PRIORITY</div>'
        "<h2>优先级建议看板</h2>"
        f'<div class="priority-grid">{"".join(columns)}</div>'
        "</section>"
    )


def render_task_flow(steps: list[str]) -> str:
    if len(steps) < 3:
        return ""
    step_html = []
    for idx, step in enumerate(steps[:7], start=1):
        step_html.append(
            '<div class="flow-step">'
            f"<span>{idx}</span>"
            f"<strong>{inline(step)}</strong>"
            "</div>"
        )
    return (
        '<section class="flow-panel">'
        '<div class="section-kicker">TASK FLOW</div>'
        "<h2>关键任务路径</h2>"
        f'<div class="flow-track">{"".join(step_html)}</div>'
        "</section>"
    )


def path_context(state: RenderState, text: str) -> bool:
    heading_text = state.current_h2 + state.current_h3
    return bool(re.search(r"关键任务|任务路径|流程对比|路径对比|路径|流程", heading_text + text))


def source_context(state: RenderState, text: str) -> bool:
    heading_text = state.current_h2 + state.current_h3
    return bool(re.search(r"来源|参考资料|资料来源|source|reference", heading_text + text, re.I))


def split_body_items(body: str) -> list[str]:
    items = [item.strip(" 。；;") for item in re.split(r"[；;]\s*", body) if item.strip(" 。；;")]
    if len(items) < 2 and len(body) > 90:
        items = [item.strip(" 。；;") for item in re.split(r"(?<=。)\s*", body) if item.strip(" 。；;")]
    return items


def render_path_value(body: str) -> str:
    if "→" in body or "->" in body:
        steps = [step.strip(" 。；;") for step in re.split(r"\s*(?:→|->)\s*", body) if step.strip(" 。；;")]
        if len(steps) >= 2:
            return '<div class="step-chain-mini">' + "".join(f"<span>{inline(step)}</span>" for step in steps) + "</div>"
    items = split_body_items(body)
    if len(items) >= 2:
        return "<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>"
    return f"<p>{inline(body.strip())}</p>"


def render_structured_paragraph(text: str, state: RenderState) -> str:
    clean = strip_inline(text)
    labels = ["竞品差异", "行动判断", "关键流程", "体验亮点", "明显短板", "可借鉴点", "建议", "判断"]
    pattern = r"(" + "|".join(labels) + r")[：:]"
    matches = list(re.finditer(pattern, clean))
    if not path_context(state, clean) or ("→" not in clean and "->" not in clean and len(matches) < 2):
        return ""

    subject = ""
    sections: list[tuple[str, str]] = []
    lead = clean[: matches[0].start()].strip() if matches else clean
    subject_match = re.match(r"^([^：:]{1,28})[：:]\s*(.+)$", lead)
    if subject_match:
        subject = subject_match.group(1).strip()
        sections.append(("关键流程", subject_match.group(2).strip()))
    elif lead:
        sections.append(("关键流程", lead))

    for idx, match in enumerate(matches):
        label = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(clean)
        body = clean[start:end].strip(" 。；;")
        if body:
            sections.append((label, body))
    if not sections:
        return ""

    field_html = []
    for label, body in sections:
        field_html.append(
            '<div class="path-field">'
            f"<h4>{inline(label)}</h4>"
            f"{render_path_value(body)}"
            "</div>"
        )
    subject_html = f'<div class="path-subject">{inline(subject)}</div>' if subject else ""
    state.path_detail_count += 1
    return (
        '<section class="path-breakdown">'
        f"{subject_html}"
        f'<div class="path-grid">{"".join(field_html)}</div>'
        "</section>"
    )


def render_list_item(item_text: str, state: RenderState) -> str:
    clean = strip_inline(item_text)
    if source_context(state, clean) and first_url(clean):
        url = first_url(clean)
        base = clean_source_text(clean)
        base = re.sub(r"链接[：:]\s*$", "", base).strip()
        title, desc = base, ""
        if "：" in base or ":" in base:
            title, desc = re.split(r"[：:]", base, maxsplit=1)
        id_match = re.match(r"^(S\d+|\d+)[\s.、-]+(.+)$", title.strip(), re.I)
        source_id = id_match.group(1) if id_match else "SRC"
        source_title = id_match.group(2).strip() if id_match else title.strip()
        desc = re.sub(r"^用于", "", desc).strip(" 。；;")
        meta_html = (
            '<div class="source-meta"><div class="source-meta-item">'
            '<span class="source-meta-label">用途</span>'
            f'<span class="source-meta-value">{inline(desc)}</span>'
            "</div></div>"
            if desc
            else ""
        )
        return (
            '<li class="source-card">'
            '<div class="source-card-head">'
            f'<span class="source-index">{inline(source_id)}</span>'
            f"<h3>{inline(source_title or compact_url_label(url))}</h3>"
            "</div>"
            f'<a class="source-link" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(compact_url_label(url))}</a>'
            f"{meta_html}"
            "</li>"
        )
    match = re.match(r"^([^：:]{2,18})[：:]\s*(.+)$", clean)
    if path_context(state, clean) and match:
        label = match.group(1).strip()
        body = match.group(2).strip()
        state.path_detail_count += 1
        return (
            '<li class="structured-li">'
            f'<strong class="li-label">{inline(label)}</strong>'
            f'<div class="li-body">{render_path_value(body)}</div>'
            "</li>"
        )
    return f"<li>{inline(item_text)}</li>"


def render_hero_stats(state: RenderState) -> str:
    stats = [
        ("章节", str(max(0, state.heading_count - 1)), "分析结构"),
        ("表格", str(state.table_count), "对比材料"),
        ("评分项", str(state.score_cell_count), "热力矩阵"),
        ("来源", str(state.source_count), "证据线索"),
    ]
    return "".join(
        '<article class="hero-stat">'
        f"<span>{label}</span>"
        f"<strong>{value}</strong>"
        f"<small>{desc}</small>"
        "</article>"
        for label, value, desc in stats
    )


def markdown_to_html(markdown: str) -> tuple[str, str, str, str, str]:
    lines = markdown.splitlines()
    html_parts: list[str] = []
    toc: list[tuple[int, str, str]] = []
    para: list[str] = []
    list_mode: str | None = None
    state = RenderState()
    state.source_count = len(re.findall(r"https?://", markdown))
    i = 0

    def close_para() -> None:
        nonlocal para
        if para:
            text = " ".join(para).strip()
            collect_signal(text, state)
            structured = render_structured_paragraph(text, state)
            html_parts.append(structured if structured else "<p>" + inline(text) + "</p>")
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
            html_parts.append(render_table(headers, aligns, rows, state, state.current_h2 or state.current_h3))
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            close_para()
            close_list()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            state.heading_count += 1
            hid = slug(state.heading_count)
            if level == 1 and state.title == "竞品分析报告":
                state.title = text
                state.subtitle = "Product Benchmarking · UX Analysis · Strategy Recommendations"
                i += 1
                continue
            if level == 2:
                state.current_h2 = text
                state.current_h3 = ""
            if level == 3:
                state.current_h3 = text
            state.current_priority = priority_from_heading(text)
            toc.append((level, text, hid))
            html_parts.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
            i += 1
            continue

        if re.match(r"^-\s+", stripped):
            close_para()
            if list_mode != "ul":
                close_list()
                if source_context(state, stripped):
                    list_class = ' class="source-list source-list-inline"'
                elif path_context(state, stripped):
                    list_class = ' class="path-list"'
                else:
                    list_class = ""
                html_parts.append(f"<ul{list_class}>")
                list_mode = "ul"
            item_text = re.sub(r"^-\s+", "", stripped)
            collect_signal(item_text, state)
            html_parts.append(render_list_item(item_text, state))
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            close_para()
            if list_mode != "ol":
                close_list()
                if source_context(state, stripped):
                    list_class = ' class="source-list source-list-inline"'
                elif path_context(state, stripped):
                    list_class = ' class="path-list"'
                else:
                    list_class = ""
                html_parts.append(f"<ol{list_class}>")
                list_mode = "ol"
            item_text = re.sub(r"^\d+\.\s+", "", stripped)
            collect_signal(item_text, state)
            html_parts.append(render_list_item(item_text, state))
            i += 1
            continue

        close_list()
        para.append(stripped)
        i += 1

    close_para()
    close_list()

    toc_html = ['<nav class="toc" aria-label="报告目录"><div class="toc-title">报告目录</div>']
    for level, text, hid in toc:
        if level == 1:
            continue
        toc_html.append(f'<a class="toc-l{level}" href="#{hid}">{inline(text)}</a>')
    toc_html.append("</nav>")

    lead_visuals = render_summary_cards(state.summary_items or [])
    task_flow = "" if state.path_detail_count else render_task_flow(state.task_steps or [])
    tail_visuals = task_flow + render_priority_board(state.priority_items or {})
    content = lead_visuals + "\n".join(html_parts) + tail_visuals
    return state.title, state.subtitle, content, "".join(toc_html), render_hero_stats(state)


def main() -> None:
    parser = argparse.ArgumentParser(description="把 Markdown 竞品分析报告转换为可视化 HTML")
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
    title, subtitle, content, toc, hero_stats = markdown_to_html(markdown)
    template = template_path.read_text(encoding="utf-8")
    html_doc = template.replace("{{TITLE}}", html.escape(title, quote=False))
    html_doc = html_doc.replace("{{SUBTITLE}}", html.escape(subtitle, quote=False))
    html_doc = html_doc.replace("{{GENERATED_AT}}", datetime.now().strftime("%Y-%m-%d"))
    html_doc = html_doc.replace("{{HERO_STATS}}", hero_stats)
    html_doc = html_doc.replace("{{TOC}}", toc)
    html_doc = html_doc.replace("{{CONTENT}}", content)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
