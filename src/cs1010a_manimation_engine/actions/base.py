"""Base class and registry for action types (the CSV Type column)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from ..scene import CodeScene
    from ..script import Action
    from ..timeline import Step

ACTION_TYPES: dict[str, type[ActionType]] = {}


def register_action(cls: type[ActionType]) -> type[ActionType]:
    """Class decorator: make *cls* available as the Type ``cls.name``
    (matched case-insensitively).  Registering a name again replaces it."""
    ACTION_TYPES[cls.name.lower()] = cls
    return cls


def get_action_type(name: str) -> type[ActionType] | None:
    return ACTION_TYPES.get(name.lower())


class ActionType:
    """Turns one script row into a Step for the timeline.

    Subclasses set ``name`` and implement ``build``.  ``build`` runs just
    before the row's animations start: a leading row before its batch plays,
    an '&' row after the earlier rows in its batch have made their first
    changes (e.g. added their lines).  It may play animations itself (e.g.
    scrolling) and report that time in Step.elapsed.

    ``uses_layout``: whether ``build`` reads on-screen positions.  If so and
    an earlier row in the batch is about to move lines (scroll / insert),
    that movement plays first so ``build`` sees where the lines end up.
    """

    name: ClassVar[str]
    uses_layout: ClassVar[bool] = True

    def build(self, scene: CodeScene, action: Action) -> Step | None:
        raise NotImplementedError

    @staticmethod
    def target_line(scene: CodeScene, action: Action) -> int:
        """The row's line index, defaulting to the last line."""
        idx = action.line_index
        return idx if idx is not None else len(scene.block) - 1
