"""Highlight, Pulse and FadeOut: drawing attention to parts of the code."""

from __future__ import annotations

from manim import FadeIn, FadeOut as FadeOutAnim, Indicate, ManimColor, SurroundingRectangle, VGroup

from ..code_block import HIGHLIGHT_OPACITY
from ..text import substring_indices
from ..timeline import AnimPhase, Step, merge_phase_lists
from .base import ActionType, register_action


def highlight_phases(scene, line_index: int, substring: str, effect: tuple[str, ...],
                     duration: float = 1.0) -> list[AnimPhase]:
    """Return phases to highlight a substring with a semi-transparent rectangle.

    - persistent (default): stays visible until a FadeOut action.
    - temporary: fades out automatically when the next highlight appears.
    - A hex colour token (e.g. "#ff7700") or named Manim colour (e.g. "green") in
      the effect list overrides the theme's highlight colour for this overlay.
      It can be combined with temporary/persistent via commas.
    """
    line = scene.block[line_index]
    start, end = substring_indices(line.raw_text, substring)
    if start is None:
        return []

    # Resolve highlight colour: look for a colour token in the effect list.
    # Hex tokens start with '#'; named colours are tried uppercase (e.g. "green" → "GREEN").
    highlight_color = scene.theme.highlight_color
    for token in effect:
        if token in ("temporary", "persistent"):
            continue
        try:
            candidate = token if token.startswith("#") else token.upper()
            highlight_color = ManimColor(candidate)
            break
        except Exception:
            pass

    overlay = SurroundingRectangle(
        line[start:end],
        buff=0.05,
        fill_color=highlight_color,
        fill_opacity=HIGHLIGHT_OPACITY,
        stroke_color=highlight_color,
        stroke_width=1,
        corner_radius=0.05,
    )
    overlay.line = line   # so the overlay scrolls with its line
    overlays = scene.overlays
    anims = [FadeIn(overlay)]
    # Always clear previous temporary overlays
    if overlays.temporary:
        anims += [FadeOutAnim(ov) for ov in overlays.temporary]
        overlays.temporary = []

    def post():
        if "temporary" in effect:
            overlays.temporary.append(overlay)
        else:
            overlays.persistent.append(overlay)

    return [AnimPhase(anims=anims, run_time=0.4 * duration, pre=None, post=post)]


def pulse_phases(scene, line_index: int, substring: str, duration: float = 1.0) -> list[AnimPhase]:
    """Return phases to pulse a substring (scale up + glow, then contract back).

    Uses Manim's Indicate animation on a floating copy layered over the original.
    The original line stays untouched; the copy pulses and is removed afterward.
    Always temporary — no overlay is left behind.

    Note: .animate.become() is NOT used here because .become() is not a valid
    animatable method — it silently fails in the .animate builder. Indicate handles
    the full expand+restore cycle internally and correctly.
    """
    line = scene.block[line_index]
    start, end = substring_indices(line.raw_text, substring)
    if start is None:
        return []

    # Animate a floating copy on top of the original characters.
    # The originals are hidden during the animation to avoid the double-text
    # artifact, then restored afterward.
    target_copy = VGroup(*[line[j].copy() for j in range(start, end)])
    originals = [line[j] for j in range(start, end)]

    def pre():
        for ch in originals:
            ch.set_opacity(0)
        scene.add(target_copy)

    def post():
        scene.remove(target_copy)
        for ch in originals:
            ch.set_opacity(1)

    return [AnimPhase(
        anims=[Indicate(target_copy, color=scene.theme.highlight_color, scale_factor=1.3)],
        run_time=0.6 * duration,
        pre=pre,
        post=post,
    )]


@register_action
class Highlight(ActionType):
    """Box a substring of line *Line* (default: last line); Line='*' boxes it
    on every visible line that contains it."""

    name = "Highlight"

    def build(self, scene, action):
        if action.is_wildcard:
            all_pl = [highlight_phases(scene, i, action.content, action.effects, action.duration)
                      for i in scene.block.matching(action.content, visible_only=True)]
            return Step(merge_phase_lists(all_pl))
        idx = self.target_line(scene, action)
        scrolled = scene.scroll_into_view(idx)
        return Step(highlight_phases(scene, idx, action.content, action.effects, action.duration),
                    elapsed=scrolled)


@register_action
class Pulse(ActionType):
    """Briefly enlarge a substring of line *Line*; Line='*' pulses it on every
    visible line that contains it."""

    name = "Pulse"

    def build(self, scene, action):
        if action.is_wildcard:
            all_pl = [pulse_phases(scene, i, action.content, action.duration)
                      for i in scene.block.matching(action.content, visible_only=True)]
            return Step(merge_phase_lists(all_pl))
        idx = self.target_line(scene, action)
        scrolled = scene.scroll_into_view(idx)
        return Step(pulse_phases(scene, idx, action.content, action.duration), elapsed=scrolled)


@register_action
class FadeOut(ActionType):
    """Fade out all highlight overlays."""

    name = "FadeOut"
    uses_layout = False

    def build(self, scene, action):
        overlays = scene.overlays
        all_overlays = overlays.all()
        if not all_overlays:
            return Step()

        def post():
            overlays.persistent = []
            overlays.temporary = []

        return Step([AnimPhase(
            anims=[FadeOutAnim(ov) for ov in all_overlays],
            run_time=action.duration * 0.3,
            pre=None,
            post=post,
        )])
