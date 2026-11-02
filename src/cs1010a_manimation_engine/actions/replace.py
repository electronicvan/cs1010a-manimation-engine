"""Replace: changing text in a line, by backspace-and-retype or by morphing."""

from __future__ import annotations

import logging

from manim import LEFT, RIGHT, FadeIn, FadeOut, ReplacementTransform, TransformMatchingShapes, VGroup

from ..script import parse_replace
from ..text import find_all, manim_index
from ..timeline import AnimPhase, Step, merge_phase_lists
from .base import ActionType, register_action

logger = logging.getLogger(__name__)


def transform_phases(scene, line_index: int, old_sub: str, new_sub: str,
                     duration: float = 1.0) -> list[AnimPhase]:
    """Return phases for a transform-style replacement.

    Every match morphs into its replacement at once; the text between and
    after the matches slides to its new position.
    """
    old_line = scene.block[line_index]
    old_raw  = old_line.raw_text
    positions = find_all(old_raw, old_sub)
    if not positions:
        logger.warning("Replace: %r not found on line %d", old_sub, line_index)
        return []

    new_raw  = old_raw.replace(old_sub, new_sub)
    new_line = scene.lines.make_like(new_raw, old_line)

    animations = []
    targets    = []   # new-line slices the animations add to the scene
    def morph(old_part, new_part, anim_cls):
        if len(old_part) and len(new_part):
            animations.append(anim_cls(old_part, new_part))
            targets.append(new_part)
        elif len(old_part):
            animations.append(FadeOut(old_part))
        elif len(new_part):
            animations.append(FadeIn(new_part))
            targets.append(new_part)

    old_cursor = new_cursor = None   # glyph index just past the previous match
    for k, pos in enumerate(positions):
        new_pos = pos + k * (len(new_sub) - len(old_sub))
        so = manim_index(old_raw, pos)
        eo = manim_index(old_raw, pos + len(old_sub))
        sn = manim_index(new_raw, new_pos)
        en = manim_index(new_raw, new_pos + len(new_sub))
        if old_cursor is not None:   # text between the previous match and this one
            morph(old_line[old_cursor:so], new_line[new_cursor:sn], ReplacementTransform)
        morph(old_line[so:eo], new_line[sn:en], TransformMatchingShapes)
        old_cursor, new_cursor = eo, en
    if len(old_line) > old_cursor and len(new_line) > new_cursor:   # suffix
        morph(old_line[old_cursor:], new_line[new_cursor:], ReplacementTransform)

    def post():
        scene.remove(old_line, *targets)
        scene.add(new_line)
        scene.block.swap(line_index, new_line)

    return [AnimPhase(
        anims=animations,
        run_time=1.0 * duration,
        pre=None,
        post=post,
    )]


def backspace_phases(scene, line_index: int, old_sub: str, new_sub: str,
                     duration: float = 1.0) -> list[AnimPhase]:
    """Return phases for a backspace-style replacement.

    Matches are retyped one after another, left to right: each step turns
    the line into an intermediate line with one more match replaced.
    The timeline rebuilds the scene once after the entire batch completes.
    """
    cur_line = scene.block[line_index]
    positions = find_all(cur_line.raw_text, old_sub)
    if not positions:
        logger.warning("Replace: %r not found on line %d", old_sub, line_index)
        return []

    phases = []
    for k, pos in enumerate(positions):
        # Earlier steps have already changed the text before this match.
        pos += k * (len(new_sub) - len(old_sub))
        raw = cur_line.raw_text
        next_raw  = raw[:pos] + new_sub + raw[pos + len(old_sub):]
        next_line = scene.lines.make_like(next_raw, cur_line)
        phases += _backspace_step(scene, line_index, cur_line, next_line,
                                  pos, len(old_sub), len(new_sub), duration)
        cur_line = next_line
    return phases


def _backspace_step(scene, line_index: int, old_line, new_line, pos: int,
                    old_len: int, new_len: int, duration: float) -> list[AnimPhase]:
    """Return phases that backspace one match out of *old_line* and type its
    replacement, leaving *new_line* in place.

    Phases: [setup, bs_N-1, …, bs_0, add_new, type_0, …, type_M-1, cleanup]
    """
    start_idx_old = manim_index(old_line.raw_text, pos)
    end_idx_old   = manim_index(old_line.raw_text, pos + old_len)
    start_idx_new = manim_index(new_line.raw_text, pos)
    end_idx_new   = manim_index(new_line.raw_text, pos + new_len)

    CHAR_TIME = 0.06 * duration

    n_old = end_idx_old - start_idx_old
    n_new = end_idx_new - start_idx_new
    has_suffix = end_idx_old < len(old_line)

    if has_suffix:
        # Total width of old substring = from its left edge to its right edge.
        # We use get_right() of the last old char (not get_left() of end_idx_old)
        # so that the suffix shifts by the full character width, not just to the
        # next character's left edge (which misses that character's own body).
        total_backspace = (
            old_line[end_idx_old - 1].get_right()[0] - old_line[start_idx_old].get_left()[0]
        )
        per_backspace = total_backspace / n_old if n_old > 0 else 0

        if end_idx_new < len(new_line):
            total_type = (
                new_line[end_idx_new - 1].get_right()[0] - new_line[start_idx_new].get_left()[0]
            )
        else:
            total_type = 0
        per_type = total_type / n_new if n_new > 0 else 0
    else:
        per_backspace = per_type = 0

    # ===================================================================
    # ROOT CAUSE OF GHOST ARTIFACTS:
    # Remove old_line IMMEDIATELY. Build independent copies. Animate only
    # copies. The timeline rebuilds the scene after all phases finish.
    # ===================================================================

    # --- Build independent copies for the visual ---
    prefix_copies  = [old_line[j].copy() for j in range(start_idx_old)]
    old_sub_copies = [old_line[j].copy() for j in range(start_idx_old, end_idx_old)]
    suffix_copies  = [old_line[j].copy() for j in range(end_idx_old, len(old_line))]
    suffix_group   = VGroup(*suffix_copies) if suffix_copies else VGroup()

    # Build new_sub copies (hidden until typed)
    new_sub_copies = []
    for j in range(start_idx_new, end_idx_new):
        c = new_line[j].copy()
        c.set_opacity(0)
        new_sub_copies.append(c)

    phases = []

    # --- Setup: swap scene objects ---
    def setup():
        scene.remove(old_line)
        for c in prefix_copies:
            scene.add(c)
        for c in old_sub_copies:
            scene.add(c)
        if len(suffix_group) > 0:
            scene.add(suffix_group)
    phases.append(AnimPhase(anims=[], run_time=0, pre=setup, post=None))

    # --- Backspace: fade out chars right-to-left; shift suffix in post callback.
    #
    # WHY NOT .animate.shift() in anims:
    # suffix_group.animate.shift() returns an _AnimationBuilder constructed at
    # phase-build time. All N builders reference the same suffix_group object.
    # When Manim resolves each builder at play() time it snapshots the
    # mobject's current position — BUT the previous play() has not yet committed
    # the new position back to the mobject (Cairo defers this until after the
    # animation clip is written). So every builder sees the original position and
    # all N shifts start from the same point, effectively stacking on top of each
    # other rather than accumulating. Calling suffix_group.shift() directly in a
    # post callback runs between play() calls when Cairo HAS committed the
    # previous frame, so positions accumulate correctly. ---
    for idx in range(len(old_sub_copies) - 1, -1, -1):
        if len(suffix_group) > 0:
            def _post_bs(sg=suffix_group, pb=per_backspace):
                sg.shift(LEFT * pb)
            post_fn = _post_bs
        else:
            post_fn = None
        phases.append(AnimPhase(
            anims=[FadeOut(old_sub_copies[idx])],
            run_time=CHAR_TIME,
            pre=None,
            post=post_fn,
        ))

    # --- Add new_sub copies to scene ---
    def add_new():
        for c in new_sub_copies:
            scene.add(c)
    phases.append(AnimPhase(anims=[], run_time=0, pre=add_new, post=None))

    # --- Type: reveal chars left-to-right; shift suffix in post callback (same reason). ---
    for c in new_sub_copies:
        if len(suffix_group) > 0:
            def _post_type(sg=suffix_group, pt=per_type):
                sg.shift(RIGHT * pt)
            post_fn_type = _post_type
        else:
            post_fn_type = None
        phases.append(AnimPhase(
            anims=[c.animate.set_opacity(1)],
            run_time=CHAR_TIME,
            pre=None,
            post=post_fn_type,
        ))

    # --- Cleanup: show new_line in place of the copies, so the next step (if
    # any) starts from it; the scene rebuild is still done by the timeline ---
    def cleanup():
        scene.remove(*prefix_copies, *old_sub_copies, suffix_group, *new_sub_copies)
        scene.add(new_line)
        scene.block.swap(line_index, new_line)
    phases.append(AnimPhase(anims=[], run_time=0, pre=None, post=cleanup))

    return phases


@register_action
class Replace(ActionType):
    """Replace every match of *old* with *new* in line *Line* (Content
    'old -> new').  Effect 'transform' morphs; default 'backspace' retypes.
    Line='*' does every line containing *old*, scrolling to each screenful.
    """

    name = "Replace"

    def build(self, scene, action):
        parsed = parse_replace(action.content)
        if parsed is None:
            logger.warning("Replace content must be 'old -> new' with exactly one unescaped '->': %r",
                           action.content)
            return None
        old_sub, new_sub = parsed
        phases_for = transform_phases if "transform" in action.effects else backspace_phases
        # Both styles need a scene rebuild: transforms on slices of a line leave
        # orphaned glyphs behind (Scene.remove splits the line's family), which
        # show up as ghosts once the block scrolls.
        if action.is_wildcard:
            matches = scene.block.matching(old_sub)
            if all(scene.block.is_visible(i) for i in matches):
                all_pl = [phases_for(scene, i, old_sub, new_sub, action.duration) for i in matches]
                return Step(merge_phase_lists(all_pl), needs_cleanup=True)
            # Some matches are scrolled out of view: visit each screenful in turn.
            played = self._replace_in_screenfuls(scene, matches, phases_for, old_sub, new_sub,
                                                 action.duration)
            return Step(elapsed=played)
        idx = self.target_line(scene, action)
        scrolled = scene.scroll_into_view(idx)
        return Step(phases_for(scene, idx, old_sub, new_sub, action.duration),
                    needs_cleanup=True, elapsed=scrolled)

    @staticmethod
    def _replace_in_screenfuls(scene, matches, phases_for, old_sub, new_sub, duration) -> float:
        """Line='*' Replace whose matches don't all fit in the window: animate
        the matches in view, then scroll to each further screenful in turn.

        Plays immediately (phases are built from on-screen positions, so each
        screenful must be built after its scroll).  Returns the time played.
        """
        played = 0.0
        remaining = list(matches)
        while remaining:
            if not any(scene.block.is_visible(i) for i in remaining):
                played += scene.scroll_into_view(remaining[0], to_top=True)
            group = [i for i in remaining if scene.block.is_visible(i)]
            remaining = [i for i in remaining if i not in group]
            played += scene.timeline.play(
                [phases_for(scene, i, old_sub, new_sub, duration) for i in group])
            scene.rebuild()
        return played
