"""Action types — one class per value of the CSV Type column.

Importing this package registers the built-in types.  Add your own with::

    from cs1010a_manimation_engine.actions import ActionType, register_action

    @register_action
    class Shake(ActionType):
        name = "Shake"
        def build(self, scene, action):
            ...  # return a Step
"""

from .base import ACTION_TYPES, ActionType, get_action_type, register_action
from .edit import Append, Insert
from .marks import FadeOut, Highlight, Pulse
from .replace import Replace
from .wait import Wait

__all__ = [
    "ACTION_TYPES", "ActionType", "get_action_type", "register_action",
    "Append", "Insert", "Highlight", "Pulse", "FadeOut", "Replace", "Wait",
]
