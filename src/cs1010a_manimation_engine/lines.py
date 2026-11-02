"""Creating code-line mobjects with indentation and syntax colouring."""

from __future__ import annotations

import logging

from manim import BLACK, LEFT, Dot, Mobject, Text

from .layout import TextArea
from .text import pattern_indices
from .theme import Theme, to_color

logger = logging.getLogger(__name__)

# Syntax categories, applied in order (later rules win).  A theme colours a
# category by naming it under 'syntax:'; categories it leaves out stay plain.
SYNTAX_PATTERNS = [
    ("keyword", r'\b(def|class|return|if|elif|else|for|while|import|from|as|with|'
                r'pass|break|continue|raise|try|except|finally|lambda|and|or|not|'
                r'in|is|None)\b'),
    ("bool",    r'\b(True|False|None)\b'),
    ("defname", r'(?<=\bdef\s)\w+|(?<=\bclass\s)\w+'),
]


class LineFactory:
    """Makes code-line mobjects in a theme's style.

    Every line carries three attributes besides its glyphs:
    ``raw_text`` (the source line, spaces included), ``indent_shift`` (scene
    units of indentation) and ``in_view`` (whether it is scrolled into view).
    """

    def __init__(self, theme: Theme, area: TextArea):
        self.theme = theme
        self.area = area
        self.syntax_rules = [
            (pattern, to_color(theme.syntax[category]))
            for category, pattern in SYNTAX_PATTERNS
            if theme.syntax.get(category)
        ]

    def make(self, raw_text: str) -> Mobject:
        """
        Creates a Text object stripped of leading whitespace, but remembers
        original indentation. Manim does not index spaces, so we strip them
        for the Text object but store the original string as raw_text.
        """
        leading_spaces = len(raw_text) - len(raw_text.lstrip())
        indent_level   = leading_spaces // 4

        clean_text = raw_text.strip()

        if not clean_text:
            # Blank line: Text(" ") has no glyphs → degenerate points array →
            # get_y() / get_left() crash with "1-dimensional array" IndexError.
            # An invisible Dot always has valid coordinates, so layout works correctly.
            dot = Dot(radius=0, fill_opacity=0, stroke_width=0, color=BLACK)
            dot.raw_text     = raw_text
            dot.indent_shift = 0
            dot.in_view      = True
            return dot

        t = Text(clean_text, font=self.theme.font, font_size=self.theme.font_size, color=self.theme.text_color)
        t.raw_text     = raw_text
        t.indent_shift = indent_level * self.theme.indent_width
        t.in_view      = True
        if self.area.left + t.indent_shift + t.width > self.area.right:
            logger.warning("line is wider than the window: %r", raw_text)
        self._apply_syntax_highlighting(t)
        return t

    def make_like(self, raw_text: str, old_line: Mobject) -> Mobject:
        """Make a line for *raw_text* positioned where *old_line* sits
        (same left edge and centre)."""
        new_line = self.make(raw_text)
        new_line.move_to(old_line.get_center())
        new_line.align_to(old_line, LEFT)
        return new_line

    def _apply_syntax_highlighting(self, line: Text):
        """Colorizes tokens in a Text object according to the syntax rules."""
        for pattern, color in self.syntax_rules:
            for si, ei in pattern_indices(line.raw_text, pattern):
                line[si:ei].set_color(color)
