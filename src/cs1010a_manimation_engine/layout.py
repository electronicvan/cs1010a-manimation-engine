"""The text area code is laid out in, and the terminal window drawn around it."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from manim import LEFT, RIGHT, UP, Dot, Line, Mobject, RoundedRectangle, Text, VGroup, config

from .theme import Theme

logger = logging.getLogger(__name__)

WINDOW_MARGIN_X = 0.36           # gap between frame edge and terminal window
WINDOW_MARGIN_Y = 0.67
BOTTOM_PADDING = 0.1             # keep text this far above the bottom of the text area
REF_PIXELS_PER_UNIT = 1080 / 8   # theme width/height are pixels at 1080p (frame is 8 units tall)


@dataclass
class TextArea:
    """Where code lines go (scene units) and how many fit."""

    left: float          # left edge of unindented text
    right: float         # text should end before this
    top: float           # centre of line 0
    bottom: float        # text must stay above this (plus padding)
    max_lines: int = 1   # line slots that fit; more lines scroll
    chrome: list[Mobject] = field(default_factory=list)   # drawn behind the text

    @classmethod
    def for_theme(cls, theme: Theme) -> TextArea:
        """Build the theme's text area: inside a terminal window if the theme
        has one, else a plain box."""
        area = _terminal_window(theme) if theme.window else _plain_area(theme)
        half_height = Text("Mg|", font=theme.font, font_size=theme.font_size).height / 2
        lowest_centre = area.bottom + BOTTOM_PADDING + half_height
        area.max_lines = max(1, int((area.top - lowest_centre) / theme.line_height) + 1)
        return area


def box_size(theme: Theme, max_width: float, max_height: float) -> tuple[float, float]:
    """Size (scene units) of the window / text area: the theme's width and
    height in pixels at 1080p, else as large as allowed.

    Pixels are converted at a fixed 1080p scale, so the layout is the same at
    every quality setting — -qh/-qk only change the render resolution.
    """
    sizes = []
    for key, limit in (("width", max_width), ("height", max_height)):
        px = theme.get(key)
        if px is None:
            sizes.append(limit)
            continue
        units = float(px) / REF_PIXELS_PER_UNIT
        if units > limit:
            logger.warning("%s %spx doesn't fit the frame - using %.0fpx", key, px, limit * REF_PIXELS_PER_UNIT)
            units = limit
        sizes.append(units)
    return sizes[0], sizes[1]


def _terminal_window(theme: Theme) -> TextArea:
    """A terminal window (rounded body, traffic-light buttons, divider)
    centred in the frame, with the text area inside it.

    Geometry matches Manim's Code(background='window') as previously used,
    but is built directly so it can be any size (see width/height).
    """
    border = theme.border_color
    width, height = box_size(theme, config.frame_width - 2 * WINDOW_MARGIN_X,
                             config.frame_height - 2 * WINDOW_MARGIN_Y)
    body = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.2,
        fill_color=theme.window_color,
        fill_opacity=1.0,
        stroke_color=border,
        stroke_width=1.5,
    )
    left, right = body.get_left()[0], body.get_right()[0]
    top, bottom = body.get_top()[1], body.get_bottom()[1]

    buttons = VGroup(*[
        Dot(radius=0.094, stroke_width=0, color=c)
        for c in ("#ff5f56", "#ffbd2e", "#27c93f")
    ]).arrange(RIGHT, buff=0.094)
    buttons.move_to([left + 0.19, top - 0.28, 0], aligned_edge=LEFT)

    # Dividing line between buttons and code content
    sep_y = top - 0.66
    separator = Line(
        start=body.get_left() * RIGHT + sep_y * UP,
        end=body.get_right() * RIGHT + sep_y * UP,
        stroke_color=border,
        stroke_width=1.5,
    )

    return TextArea(
        left=left + 0.375,
        right=right - 0.375,
        top=top - 1.06,
        bottom=bottom,
        chrome=[body, buttons, separator],
    )


def _plain_area(theme: Theme) -> TextArea:
    """Text area for window-less themes: a centred box (the whole frame by
    default) with fixed margins."""
    width, height = box_size(theme, config.frame_width, config.frame_height)
    return TextArea(
        left=-width / 2 + 1.1,
        right=width / 2 - 0.4,
        top=height / 2 - 1.0,
        bottom=-height / 2 + 0.4,
    )
