#!/usr/bin/env python3
"""Generate an original, deterministic GB18030 Chinese long-book fixture.

The generated file is intended for local performance testing only. It contains
synthetic text and should be written under the repository's ignored
.local-test-data/ directory, never committed as a build artifact.
"""
from __future__ import annotations

import argparse
from pathlib import Path

TITLES = (
    "雾夜来信", "旧城回声", "无声的灯", "远行者", "灰色清晨", "山谷尽头",
    "雨后的站台", "空房间", "最后一班车", "微光", "边界之外", "安静的街道",
)

PARAGRAPHS = (
    "夜色沿着旧街缓慢退去，远处的钟声穿过薄雾，落在空无一人的石阶上。",
    "他把记录本合上，确认门窗已经锁好，然后重新检查墙边那盏微微闪烁的灯。",
    "风从走廊尽头吹来，纸页轻轻翻动，屋里的每个人都暂时没有说话。",
    "远处传来三声短促的回响，像有人隔着很长的距离敲了敲一扇看不见的门。",
    "她停下脚步，望向街角的旧招牌，终于想起这条路曾经通往什么地方。",
    "天色还没有亮，窗外的云层却已经变薄，城市在沉默中慢慢恢复轮廓。",
    "这次没有人急着给出答案，他们先把现有线索写下来，再逐项排除不可靠的猜测。",
    "桌面上的水杯已经凉了，墙上的秒针仍按固定节奏前进，没有因为等待而停下。",
)

FILLER = "风声经过窗沿，灯光落在纸面，远处的脚步逐渐消失。"


def heading(chapter: int, chapters: int) -> str:
    title = TITLES[(chapter - 1) % len(TITLES)]
    # Deliberately mix common Chinese TXT heading styles so chapter detection
    # tests do not overfit to a single regular expression.
    if chapter <= max(1, chapters // 3):
        return f"{chapter:03d}{title}"
    if chapter % 17 == 0:
        return f"{chapter}.第{chapter}章{title}"
    return f"第{chapter}章 {title}"


def paragraph(index: int, length: int) -> str:
    text = f"记录{index + 1:06d}：{PARAGRAPHS[index % len(PARAGRAPHS)]}"
    while len(text) < length:
        text += FILLER
    return text[:length]


def generate(chapters: int, target_chars: int, target_lines: int) -> str:
    if chapters < 1:
        raise ValueError("chapters must be >= 1")

    headings = [heading(i, chapters) for i in range(1, chapters + 1)]
    headings.append(f"第{chapters + 1}章 后记")
    body_lines = target_lines - len(headings)
    if body_lines < 2:
        raise ValueError("target_lines is too small for the requested chapters")

    paragraph_count = (body_lines + 1) // 2
    blank_count = body_lines - paragraph_count
    newline_chars = 2 * (target_lines - 1)  # CRLF line endings
    body_char_budget = target_chars - sum(map(len, headings)) - newline_chars
    if body_char_budget < paragraph_count * 8:
        raise ValueError("target_chars is too small for the requested line count")

    base_length, remainder = divmod(body_char_budget, paragraph_count)
    lengths = [base_length + (1 if i < remainder else 0) for i in range(paragraph_count)]

    lines: list[str] = []
    paragraph_index = 0
    blanks_left = blank_count
    for section_index, section_heading in enumerate(headings):
        lines.append(section_heading)
        remaining_sections = len(headings) - section_index
        remaining_paragraphs = paragraph_count - paragraph_index
        count_here = (remaining_paragraphs + remaining_sections - 1) // remaining_sections
        for _ in range(count_here):
            lines.append(paragraph(paragraph_index, lengths[paragraph_index]))
            paragraph_index += 1
            if blanks_left:
                lines.append("")
                blanks_left -= 1

    if paragraph_index != paragraph_count or blanks_left != 0 or len(lines) != target_lines:
        raise RuntimeError("internal fixture sizing error")

    text = "\r\n".join(lines)
    if len(text) != target_chars:
        raise RuntimeError(f"expected {target_chars} chars, generated {len(text)}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".local-test-data/synthetic_long_gb18030.txt"),
    )
    parser.add_argument("--chapters", type=int, default=624)
    parser.add_argument("--target-chars", type=int, default=2_301_482)
    parser.add_argument("--target-lines", type=int, default=73_176)
    args = parser.parse_args()

    text = generate(args.chapters, args.target_chars, args.target_lines)
    data = text.encode("gb18030", errors="strict")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)

    print(f"Generated: {args.output}")
    print("Encoding: GB18030")
    print(f"Chapters: {args.chapters} + afterword")
    print(f"Unicode characters (including CRLF): {len(text):,}")
    print(f"Lines: {len(text.splitlines()):,}")
    print(f"Bytes: {len(data):,}")
    print("Synthetic content only; no external network calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
