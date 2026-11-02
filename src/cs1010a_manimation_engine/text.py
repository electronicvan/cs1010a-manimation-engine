"""Mapping between raw source text and Manim Text glyph indices.

Manim's Text has no glyphs for whitespace, so glyph indices skip spaces: the
helpers here translate positions in the raw line (with spaces) to them.
"""

from __future__ import annotations

import re


def manim_index(raw_text: str, raw_idx: int) -> int:
    """Raw-text index (with spaces) → Manim Text index (no spaces)."""
    return sum(1 for c in raw_text[:raw_idx] if not c.isspace())


def find_all(raw_text: str, substring: str) -> list[int]:
    """Raw start index of every non-overlapping match, left to right
    (the same matches str.replace uses)."""
    positions = []
    pos = raw_text.find(substring)
    while pos != -1:
        positions.append(pos)
        pos = raw_text.find(substring, pos + len(substring))
    return positions


def substring_indices(raw_text: str, substring: str) -> tuple[int | None, int | None]:
    """Glyph (start, end) of the first match of *substring*, or (None, None)."""
    start_raw = raw_text.find(substring)
    if start_raw == -1:
        return None, None
    end_raw = start_raw + len(substring)

    start_idx = end_idx = n_chars = 0
    for i, char in enumerate(raw_text):
        if i == start_raw:
            start_idx = n_chars
        if i == end_raw:
            end_idx = n_chars
        if not char.isspace():
            n_chars += 1
    if end_raw == len(raw_text):
        end_idx = n_chars

    return start_idx, end_idx


def pattern_indices(raw_text: str, pattern: str) -> list[tuple[int, int]]:
    """Glyph (start, end) of every non-overlapping regex match (empty ones skipped)."""
    results = []
    for m in re.finditer(pattern, raw_text):
        si = manim_index(raw_text, m.start())
        ei = manim_index(raw_text, m.end())
        if ei > si:
            results.append((si, ei))
    return results
