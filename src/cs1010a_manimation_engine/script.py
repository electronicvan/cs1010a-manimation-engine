"""Parsing of animation scripts (CSV files) — no Manim needed.

A script is an optional header of ``# key: value`` settings (theme selection
and overrides) followed by a CSV table with the columns
``Rel,Time,Type,Line,Content,Duration,Effect`` (Duration and Effect optional).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path


def parse_time(t: str) -> float:
    """Convert 'mm:ss', 'ss', or '0' → seconds (float)."""
    t = t.strip()
    if not t or t == "0":
        return 0.0
    if ":" in t:
        parts = t.split(":")
        return int(parts[0]) * 60 + float(parts[1])
    return float(t)


def coerce(value: str):
    """Turn a header value into an int / float / bool when it looks like one."""
    low = value.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    for cast in (int, float):
        try:
            return cast(value)
        except ValueError:
            pass
    return value


_LEGACY_REPLACE = (re.compile(r"'(.+?)'\s*->\s*'(.*)'", re.DOTALL),
                   re.compile(r'"(.+?)"\s*->\s*"(.*)"', re.DOTALL))


def parse_replace(content: str) -> tuple[str, str] | None:
    r"""Split Replace content 'old -> new' into (old, new); None if malformed.

    Whitespace around '->' and at either end of each side is trimmed.
    Backslash escapes the next character: ``\->`` is a literal arrow, ``\s`` a
    literal space, ``\'`` / ``\"`` / ``\\`` literal quote / backslash.
    The legacy quoted form ``'old' -> 'new'`` (or ``"old" -> "new"``) is also
    accepted.  An empty *new* means delete.
    """
    for pattern in _LEGACY_REPLACE:
        m = pattern.fullmatch(content.strip())
        if m:
            return m.group(1), m.group(2)

    sides = [[]]   # each side: list of (char, was_escaped)
    i = 0
    while i < len(content):
        c = content[i]
        if c == "\\" and i + 1 < len(content):
            nxt = content[i + 1]
            sides[-1].append((" " if nxt == "s" else nxt, True))
            i += 2
        elif content.startswith("->", i):
            sides.append([])
            i += 2
        else:
            sides[-1].append((c, False))
            i += 1
    if len(sides) != 2:
        return None

    def _trim(chars):
        while chars and not chars[0][1] and chars[0][0].isspace():
            chars.pop(0)
        while chars and not chars[-1][1] and chars[-1][0].isspace():
            chars.pop()
        return "".join(c for c, _ in chars)

    old_sub, new_sub = _trim(sides[0]), _trim(sides[1])
    return (old_sub, new_sub) if old_sub else None


@dataclass(frozen=True)
class Action:
    """One row of a script."""

    rel: str = "@"        # '@' absolute, '+' relative, '&' with the previous row
    time: str = "0"       # raw Time cell (mm:ss or seconds)
    type: str = ""        # lower-case action type, e.g. 'append'
    line: str = ""        # raw Line cell: '', an index, or '*'
    content: str = ""     # raw Content cell (leading whitespace kept)
    duration: float = 1.0
    effects: tuple[str, ...] = ()

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Action:
        """Build an Action from a cleaned CSV row (see Script.from_text)."""
        try:
            duration = float(row.get("Duration") or 1.0)
        except ValueError:
            duration = 1.0
        return cls(
            rel=row.get("Rel", "@").strip(),
            time=row.get("Time", "0").strip(),
            type=row.get("Type", "").strip().lower(),
            line=row.get("Line", "").strip(),
            content=row.get("Content", ""),
            duration=duration,
            effects=tuple(e.strip().lower() for e in row.get("Effect", "").split(",") if e.strip()),
        )

    @property
    def seconds(self) -> float:
        """The Time cell in seconds."""
        return parse_time(self.time)

    @property
    def is_wildcard(self) -> bool:
        """Line='*': apply to every line containing the substring."""
        return self.line == "*"

    @property
    def line_index(self) -> int | None:
        """The Line cell as an index, or None when blank or '*'."""
        return int(self.line) if (self.line and not self.is_wildcard) else None


@dataclass
class Script:
    """A parsed animation script: header settings plus its actions."""

    settings: dict = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)
    source: Path | None = None   # the CSV it was read from, if any

    @property
    def name(self) -> str:
        """Name used for the output video (the CSV's file stem)."""
        return self.source.stem if self.source else "script"

    @classmethod
    def from_csv(cls, path: str | Path) -> Script:
        path = Path(path)
        with open(path, newline="", encoding="utf-8-sig") as f:
            return cls.from_text(f.read(), source=path)

    @classmethod
    def from_text(cls, text: str, source: Path | None = None) -> Script:
        """Parse script text: leading '# key: value' settings, then the CSV."""
        lines = text.splitlines(keepends=True)

        settings = {}
        body_start = len(lines)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                body_start = i
                break
            if ":" in stripped:
                key, value = stripped.lstrip("#").split(":", 1)
                settings[key.strip().lower()] = coerce(value.strip())

        actions = []
        for row in csv.DictReader(io.StringIO("".join(lines[body_start:]))):
            # Strip keys and non-Content values; preserve leading whitespace in Content (used for indentation).
            # Columns left off the end of a short row arrive as None → "".
            clean = {}
            for k, v in row.items():
                if k is None:       # surplus fields beyond the header
                    continue
                k = k.strip()
                clean[k] = "" if not v else (v if k == "Content" else v.strip())
            actions.append(Action.from_row(clean))
        return cls(settings=settings, actions=actions, source=source)
