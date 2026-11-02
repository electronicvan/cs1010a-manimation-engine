"""Phases, steps, and the runner that plays a script's actions in time."""

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scene import CodeScene
    from .script import Action

SCROLL_TIME = 0.3   # seconds for a scroll that isn't part of another animation

AnimPhase = namedtuple("AnimPhase", ["anims", "run_time", "pre", "post"])
"""A single phase of animation: (animations_list, duration, pre_callback, post_callback).

*pre* runs just before the phase plays, *post* just after.  Callbacks run
between ``play()`` calls, so state they change is committed before the next
phase's animations start."""


@dataclass
class Step:
    """What one action contributes to its batch."""

    phases: list[AnimPhase] = field(default_factory=list)   # played merged with the batch
    needs_cleanup: bool = False   # rebuild the scene after the batch (see CodeScene.rebuild)
    elapsed: float = 0.0          # time already played while building (scrolls, waits)


def merge_phase_lists(all_phase_lists: list[list[AnimPhase]]) -> list[AnimPhase]:
    """Zip multiple phase lists into one, combining anims and callbacks per index.

    Used by wildcard (Line='*') dispatch so all matching lines animate
    simultaneously rather than sequentially.
    """
    if not all_phase_lists:
        return []
    max_len = max(len(pl) for pl in all_phase_lists)
    merged = []
    for phase_idx in range(max_len):
        anims     = []
        run_time  = 0.0
        pre_fns   = []
        post_fns  = []
        for pl in all_phase_lists:
            if phase_idx < len(pl):
                p = pl[phase_idx]
                anims.extend(p.anims)
                run_time = max(run_time, p.run_time)
                if p.pre:  pre_fns.append(p.pre)
                if p.post: post_fns.append(p.post)
        def _make_combined(fns):
            if not fns:
                return None
            def _combined(fns=fns):
                for f in fns:
                    f()
            return _combined
        merged.append(AnimPhase(
            anims=anims,
            run_time=run_time,
            pre=_make_combined(pre_fns),
            post=_make_combined(post_fns),
        ))
    return merged


class Timeline:
    """Plays a script's actions on a CodeScene, honouring Rel/Time."""

    def __init__(self, scene: CodeScene):
        self.scene = scene

    def run(self, actions: list[Action]):
        """Interpret each action and play its animations.

        Rows with Rel='&' are batched with the preceding row so their
        animations play simultaneously (phases are merged by index).
        The first row always starts at 0:00.
        """
        scene = self.scene
        elapsed = 0.0

        i = 0
        while i < len(actions):
            action = actions[i]

            # --- timing for the leading row ---
            wait_secs = action.seconds
            if i == 0:
                pass
            elif action.rel == "@":
                gap = wait_secs - elapsed
                if gap > 0:
                    scene.wait(gap)
                    elapsed += gap
            elif action.rel == "+":
                if wait_secs > 0:
                    scene.wait(wait_secs)
                    elapsed += wait_secs

            # --- collect batch: leading row + all trailing '&' rows ---
            batch = [action]
            i += 1
            while i < len(actions) and actions[i].rel == "&":
                batch.append(actions[i])
                i += 1

            elapsed += self._play_batch(batch)

    def _play_batch(self, batch: list[Action]) -> float:
        """Build and play one batch; returns the time played.

        The leading row is built first.  Each '&' row is built only after the
        rows before it have run their first phase's *pre* (where Append and
        Insert add their lines), so it sees those lines — e.g. '&,0,Highlight'
        right after an Append highlights the new line.  Then the whole batch
        plays together.
        """
        scene = self.scene
        all_phase_lists = []
        needs_cleanup = False
        extra_elapsed = 0.0

        # Phase 0 is assembled row by row; its pre callbacks run as each row is built.
        first_anims, first_run_time, first_posts = [], 0.0, []
        for k, a in enumerate(batch):
            if k > 0 and self._uses_layout(a):
                extra_elapsed += self._settle()
            step = scene.build_step(a)
            if step is None:
                continue
            needs_cleanup = needs_cleanup or step.needs_cleanup
            extra_elapsed += step.elapsed
            if not step.phases:
                continue
            all_phase_lists.append(step.phases)
            first = step.phases[0]
            if first.pre:
                first.pre()
            first_anims.extend(first.anims)
            first_run_time = max(first_run_time, first.run_time)
            if first.post:
                first_posts.append(first.post)

        if not all_phase_lists and extra_elapsed == 0:
            return 0.0

        played = 0.0
        if all_phase_lists:
            played += self._play_phase(first_anims, first_run_time, first_posts)
            played += self.play([pl[1:] for pl in all_phase_lists])

        if needs_cleanup:
            scene.rebuild()

        return played + extra_elapsed

    def _uses_layout(self, action: Action) -> bool:
        action_type = self.scene.action_type(action)
        return action_type is not None and action_type.uses_layout

    def _settle(self) -> float:
        """Place lines added so far in this batch and, if on-screen lines must
        move (scroll / insert gap), play that now.  Returns the time played."""
        anims = self.scene.block.layout_anims(self.scene.is_on_screen)
        if not anims:
            return 0.0
        self.scene.play(*anims, run_time=SCROLL_TIME)
        return SCROLL_TIME

    def _play_phase(self, anims: list, run_time: float, posts: list) -> float:
        """Play one merged phase whose pre callbacks have already run, with the
        layout pass alongside it; then run its post callbacks."""
        scene = self.scene
        played = 0.0
        # Slide lines to their slots (insert gaps, scrolling) alongside the phase.
        anims = anims + scene.block.layout_anims(scene.is_on_screen)
        if anims:
            run_time = run_time if run_time > 0 else SCROLL_TIME
            scene.play(*anims, run_time=run_time)
            played = run_time
        for fn in posts:
            fn()
        return played

    def play(self, all_phase_lists: list[list[AnimPhase]]) -> float:
        """Play several phase lists simultaneously (merged by phase index).

        Returns the time played.
        """
        played = 0.0
        max_phase_count = max((len(pl) for pl in all_phase_lists), default=0)
        for phase_idx in range(max_phase_count):
            pre_fns      = []
            merged_anims = []
            max_run_time = 0.0
            post_fns     = []

            for pl in all_phase_lists:
                if phase_idx < len(pl):
                    phase = pl[phase_idx]
                    if phase.pre:
                        pre_fns.append(phase.pre)
                    merged_anims.extend(phase.anims)
                    max_run_time = max(max_run_time, phase.run_time)
                    if phase.post:
                        post_fns.append(phase.post)

            for fn in pre_fns:
                fn()
            played += self._play_phase(merged_anims, max_run_time, post_fns)
        return played
