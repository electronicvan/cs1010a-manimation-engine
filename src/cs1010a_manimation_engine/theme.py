"""Themes: named presets from YAML, with per-script overrides."""

from __future__ import annotations

import copy
import logging
from importlib.resources import files
from pathlib import Path

import yaml
from manim import ManimColor

logger = logging.getLogger(__name__)

BUNDLED_THEMES = files(__package__) / "themes.yaml"
OPTIONAL_KEYS = {"width", "height"}   # valid overrides even if the theme omits them
SCRIPT_KEYS = {"theme", "themes"}     # header settings that select themes rather than override them


def to_color(value) -> ManimColor:
    """Hex ('#ff7700') or Manim colour name ('yellow', any case) → ManimColor."""
    return ManimColor(str(value))


def load_themes_file(path) -> dict:
    """Read a themes YAML file: {'default': name, 'themes': {name: settings}}."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Theme:
    """The settings one video is rendered with.

    Values keep their YAML keys (kebab-case, e.g. 'font-size'); the properties
    below give typed access to the ones the engine uses.
    """

    def __init__(self, name: str, values: dict):
        self.name = name
        self.values = values

    @classmethod
    def from_settings(cls, settings: dict, base_dir: Path | None = None) -> Theme:
        """Resolve a script's header settings into a Theme.

        ``theme`` picks the preset (default: the themes file's ``default``);
        ``themes`` names an extra YAML file (relative to *base_dir*) whose
        themes are added to / replace the built-in ones.  Every other setting
        overrides that key of the theme; dotted keys reach into nested maps,
        e.g. ``syntax.keyword``.
        """
        data = load_themes_file(BUNDLED_THEMES)
        themes = dict(data["themes"])
        default = data.get("default", "terminal")
        if "themes" in settings:
            user_path = Path(str(settings["themes"]))
            if base_dir is not None and not user_path.is_absolute():
                user_path = base_dir / user_path
            user = load_themes_file(user_path)
            themes.update(user.get("themes") or {})
            default = user.get("default", default)

        name = str(settings.get("theme", default))
        if name not in themes:
            raise ValueError(f"Unknown theme {name!r} - available: {', '.join(themes)}")

        values = copy.deepcopy(themes[name])
        for key, value in settings.items():
            if key in SCRIPT_KEYS:
                continue
            *parents, leaf = key.split(".")
            node = values
            for p in parents:
                node = node.setdefault(p, {})
            if leaf not in node and key not in OPTIONAL_KEYS:
                logger.warning("%r is not a setting of theme %r - check the spelling", key, name)
            node[leaf] = value
        return cls(name, values)

    def __getitem__(self, key: str):
        return self.values[key]

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    # -- typed accessors -----------------------------------------------------

    @property
    def font(self) -> str:
        return self.values["font"]

    @property
    def font_size(self) -> float:
        return self.values["font-size"]

    @property
    def line_height(self) -> float:
        return self.values["line-height"]

    @property
    def indent_width(self) -> float:
        return self.values["indent-width"]

    @property
    def bg_color(self) -> ManimColor:
        return to_color(self.values["bg-color"])

    @property
    def text_color(self) -> ManimColor:
        return to_color(self.values["text-color"])

    @property
    def highlight_color(self) -> ManimColor:
        return to_color(self.values["highlight-color"])

    @property
    def window(self) -> bool:
        return bool(self.values.get("window", False))

    @property
    def window_color(self) -> ManimColor:
        return to_color(self.values["window-color"])

    @property
    def border_color(self) -> ManimColor:
        return to_color(self.values["border-color"])

    @property
    def syntax(self) -> dict:
        """Syntax category → colour value, for the categories the theme colours."""
        return self.values.get("syntax") or {}
