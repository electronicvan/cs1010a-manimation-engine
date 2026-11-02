"""Wait: hold the current frame."""

from __future__ import annotations

from manim import Wait as Hold

from ..timeline import AnimPhase, Step
from .base import ActionType, register_action


@register_action
class Wait(ActionType):
    """Hold for *Duration* seconds (default 1).

    Like every row, *Time* is the gap before it starts, so ``+,2,Wait,,,3``
    waits 2 s and then holds 3 s.  Batched with '&', the hold plays
    alongside the batch, so the batch lasts at least *Duration*.
    """

    name = "Wait"
    uses_layout = False

    def build(self, scene, action):
        hold = action.duration
        if hold <= 0:
            return Step()
        return Step([AnimPhase(anims=[Hold(run_time=hold)], run_time=hold, pre=None, post=None)])
