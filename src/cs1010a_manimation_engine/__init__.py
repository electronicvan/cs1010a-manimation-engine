"""Animate code walkthroughs in Manim from CSV scripts.

Quick start::

    from cs1010a_manimation_engine import render
    render("csv_inputs/example.csv", quality="l", preview=True)

or from a shell: ``manimation csv_inputs/example.csv -pql``.
"""

from .actions import ActionType, register_action
from .render import render
from .scene import CodeScene
from .script import Action, Script
from .theme import Theme
from .timeline import AnimPhase, Step

__all__ = [
    "render", "CodeScene", "Script", "Action", "Theme",
    "ActionType", "register_action", "AnimPhase", "Step",
]
