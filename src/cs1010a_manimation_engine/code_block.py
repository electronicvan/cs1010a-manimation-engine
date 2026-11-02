"""The block of code lines on screen: order, scrolling, and the highlight
overlays attached to lines."""

from __future__ import annotations

from typing import Callable

import numpy as np
from manim import Mobject, VGroup

from .layout import TextArea

HIGHLIGHT_OPACITY = 0.25


class Overlays:
    """Highlight rectangles.  Each overlay has a ``line`` attribute (the line
    it marks) so it scrolls with that line."""

    def __init__(self):
        self.persistent: list[Mobject] = []   # stay until FadeOut
        self.temporary: list[Mobject] = []    # cleared when the next highlight appears

    def all(self) -> list[Mobject]:
        return self.persistent + self.temporary

    def retarget(self, old_line: Mobject, new_line: Mobject):
        """Move overlays marking *old_line* onto *new_line*."""
        for ov in self.all():
            if ov.line is old_line:
                ov.line = new_line


class CodeBlock:
    """The ordered code lines plus which of them are scrolled into view."""

    def __init__(self, area: TextArea, line_height: float, overlays: Overlays):
        self.area = area
        self.line_height = line_height
        self.overlays = overlays
        self.lines = VGroup()
        self.scroll_top = 0      # index of the first line in view
        self.focus = None        # line the next layout pass must scroll into view

    def __len__(self) -> int:
        return len(self.lines)

    def __getitem__(self, index: int) -> Mobject:
        return self.lines[index]

    def __iter__(self):
        return iter(self.lines)

    def add(self, line: Mobject):
        self.lines.add(line)

    def insert(self, index: int, line: Mobject):
        self.lines.insert(index, line)

    def swap(self, index: int, new_line: Mobject):
        """Put *new_line* at *index*, moving the old line's overlays onto it."""
        self.overlays.retarget(self.lines[index], new_line)
        self.lines[index] = new_line

    # -- scrolling -----------------------------------------------------------

    def is_visible(self, index: int) -> bool:
        """True if line *index* is inside the scrolled window."""
        return self.scroll_top <= index < self.scroll_top + self.area.max_lines

    def matching(self, substring: str, visible_only: bool = False) -> list[int]:
        """Indices of lines containing *substring* (for Line='*')."""
        return [i for i, line in enumerate(self.lines)
                if substring in line.raw_text and (self.is_visible(i) or not visible_only)]

    def scroll_for(self, index: int, to_top: bool = False):
        """Move scroll_top the minimum distance that brings line *index* into view,
        or with *to_top*, as far as possible towards making it the top line."""
        if index < self.scroll_top:
            self.scroll_top = index
        elif index >= self.scroll_top + self.area.max_lines:
            if to_top:
                self.scroll_top = min(index, max(0, len(self) - self.area.max_lines))
            else:
                self.scroll_top = index - self.area.max_lines + 1

    def layout_anims(self, on_screen: Callable[[Mobject], bool]) -> list:
        """Return animations that bring every line to its slot for the current
        scroll position, first scrolling to any pending focus line.

        Lines already on screen (and their highlight overlays) slide to their
        slot, fading out as they leave the window and back in as they return.
        Lines not yet on screen are just placed, ready to be written.

        Each line is animated individually rather than via a VGroup slice: a
        slice is not in the scene's mobjects, so Cairo may leave lines that were
        added via scene.add() (e.g. replaced lines) in the static background → ghosts.
        """
        if self.focus is not None:
            self.scroll_for(self.lines.submobjects.index(self.focus))
            self.focus = None

        overlays = self.overlays.all()
        anims = []
        for i, line in enumerate(self.lines):
            target = np.array([
                self.area.left + line.indent_shift,
                self.area.top - (i - self.scroll_top) * self.line_height,
                0,
            ])
            shift = target - np.array([line.get_left()[0], line.get_y(), 0])
            visible = self.is_visible(i)
            toggled = visible != line.in_view
            line.in_view = visible

            if not on_screen(line):
                line.shift(shift)
                if toggled:
                    line.set_opacity(1 if visible else 0)
                continue
            if not toggled and np.allclose(shift, 0, atol=1e-6):
                continue

            anim = line.animate.shift(shift)
            if toggled:
                anim = anim.set_opacity(1 if visible else 0)
            anims.append(anim)

            for ov in overlays:
                if ov.line is line:
                    ov_anim = ov.animate.shift(shift)
                    if toggled:
                        ov_anim = (ov_anim.set_fill(opacity=HIGHLIGHT_OPACITY if visible else 0)
                                          .set_stroke(opacity=1 if visible else 0))
                    anims.append(ov_anim)
        return anims
