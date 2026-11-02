"""CodeScene: a Manim Scene that plays an animation script."""

from __future__ import annotations

import logging
from pathlib import Path

from manim import BLACK, Dot, Mobject, Scene

from .actions import ActionType, get_action_type
from .code_block import CodeBlock, Overlays
from .layout import TextArea
from .lines import LineFactory
from .script import Action, Script
from .theme import Theme
from .timeline import SCROLL_TIME, Step, Timeline

logger = logging.getLogger(__name__)


class CodeScene(Scene):
    """Plays a CSV animation script.

    Give it the script either when constructing it (``CodeScene("x.csv")``,
    as ``render()`` does) or as a class attribute, which lets the plain
    ``manim`` command render it::

        class Slide11(CodeScene):
            script = "csv_inputs/L2_1_slide11.csv"

    While constructing, the scene exposes the pieces action types work with:
    ``theme``, ``area`` (text area), ``block`` (code lines + scrolling),
    ``overlays`` (highlights), ``lines`` (line factory) and ``timeline``.
    """

    script: Script | str | Path | None = None

    def __init__(self, script: Script | str | Path | None = None, **kwargs):
        super().__init__(**kwargs)
        if script is not None:
            self.script = script

    def construct(self):
        script = self.script
        if script is None:
            raise ValueError("CodeScene needs a script: CodeScene('file.csv') or a 'script' class attribute")
        if not isinstance(script, Script):
            script = Script.from_csv(script)
        self.script = script

        base_dir = script.source.parent if script.source else None
        self.theme    = Theme.from_settings(script.settings, base_dir=base_dir)
        self.camera.background_color = self.theme.bg_color
        self.overlays = Overlays()
        self.area     = TextArea.for_theme(self.theme)
        self.block    = CodeBlock(self.area, self.theme.line_height, self.overlays)
        self.lines    = LineFactory(self.theme, self.area)
        self.timeline = Timeline(self)

        # Chrome is added before any code lines, so it is naturally behind everything.
        self.add(*self.area.chrome)
        self._bg_anchor = Dot(radius=0, fill_opacity=0, stroke_width=0, color=BLACK)
        self.add(self._bg_anchor)

        self.timeline.run(script.actions)

        self.wait(2)

    # -----------------------------------------------------------------------
    # Services for action types
    # -----------------------------------------------------------------------

    def action_type(self, action: Action) -> type[ActionType] | None:
        """The registered action type for a row's Type, if any."""
        return get_action_type(action.type)

    def build_step(self, action: Action) -> Step | None:
        """Dispatch one row to its action type."""
        action_type = self.action_type(action)
        if action_type is None:
            logger.warning("Unknown action type: %r", action.type)
            return None
        return action_type().build(self, action)

    def is_on_screen(self, mob: Mobject) -> bool:
        return mob in self.mobjects

    def scroll_into_view(self, index: int, to_top: bool = False) -> float:
        """Scroll now (before phases are built from line positions) so line
        *index* is visible.  Returns the time spent."""
        if not 0 <= index < len(self.block) or self.block.is_visible(index):
            return 0.0
        self.block.scroll_for(index, to_top)
        anims = self.block.layout_anims(self.is_on_screen)
        if not anims:
            return 0.0
        self.play(*anims, run_time=SCROLL_TIME)
        return SCROLL_TIME

    def rebuild(self):
        """Rebuild the scene from the code block (after Replace operations).

        self.clear() wipes ALL mobjects (including restructured orphans),
        then we re-add only the objects we intend to keep.
        """
        self.clear()
        # Re-add chrome first so it sits behind everything.
        for mob in self.area.chrome:
            self.add(mob)
        self.add(self._bg_anchor)
        for line in self.block:
            self.add(line)
        for ov in self.overlays.all():
            self.add(ov)
