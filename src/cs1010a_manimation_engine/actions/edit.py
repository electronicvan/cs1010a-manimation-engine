"""Append and Insert: adding code lines."""

from __future__ import annotations

from manim import Write

from ..timeline import AnimPhase, Step
from .base import ActionType, register_action


@register_action
class Append(ActionType):
    """Add line(s) at the end (multiline Content splits on newlines).

    Each new line becomes the scroll focus, so once the window is full the
    timeline's layout pass scrolls the block up while the line is written.
    """

    name = "Append"
    uses_layout = False

    def build(self, scene, action):
        phases = []
        for line_text in (action.content.splitlines() or [""]):
            new_line = scene.lines.make(line_text)
            def pre(nl=new_line):
                scene.block.add(nl)
                scene.block.focus = nl
            phases.append(AnimPhase(
                anims=[Write(new_line)],
                run_time=0.4 * action.duration,
                pre=pre,
                post=None,
            ))
        return Step(phases)


@register_action
class Insert(ActionType):
    """Insert line(s) before line *Line* (default: at the end)."""

    name = "Insert"
    uses_layout = False

    def build(self, scene, action):
        index = action.line_index if action.line_index is not None else len(scene.block)
        phases = []
        for offset, line_text in enumerate(action.content.splitlines()):
            new_line = scene.lines.make(line_text)
            insert_at = index + offset
            def pre_insert(nl=new_line, ia=insert_at):
                scene.block.insert(ia, nl)
                scene.block.focus = nl
            if insert_at < len(scene.block):
                # Make room first: inserting opens a gap, and the layout pass
                # slides the lines below down into place (fading out any
                # pushed past the bottom of the window).
                phases.append(AnimPhase(
                    anims=[],
                    run_time=0.5 * action.duration,
                    pre=pre_insert,
                    post=None,
                ))
                pre_write = None
            else:
                pre_write = pre_insert
            phases.append(AnimPhase(
                anims=[Write(new_line)],
                run_time=0.4 * action.duration,
                pre=pre_write,
                post=None,
            ))
        return Step(phases)
