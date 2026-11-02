import logging

import pytest
from manim import ManimColor

from cs1010a_manimation_engine.theme import Theme


def test_default_theme_is_terminal():
    theme = Theme.from_settings({})
    assert theme.name == "terminal"
    assert theme.window is True
    assert theme.highlight_color == ManimColor("#FFFF00")


def test_overrides_and_dotted_keys():
    theme = Theme.from_settings({"theme": "idle", "bg-color": "black", "syntax.keyword": "#123456"})
    assert theme.name == "idle"
    assert theme.bg_color == ManimColor("black")
    assert theme.syntax["keyword"] == "#123456"
    assert theme.syntax["defname"] == "#0000ff"   # untouched keys keep the preset's value


def test_width_height_are_valid_without_warning(caplog):
    with caplog.at_level(logging.WARNING):
        theme = Theme.from_settings({"width": 1300, "height": 600})
    assert theme.get("width") == 1300
    assert not caplog.records


def test_unknown_key_warns(caplog):
    with caplog.at_level(logging.WARNING):
        Theme.from_settings({"bg-colour": "black"})
    assert "bg-colour" in caplog.text


def test_unknown_theme_raises():
    with pytest.raises(ValueError, match="nope"):
        Theme.from_settings({"theme": "nope"})


def test_user_themes_file_adds_themes(tmp_path):
    (tmp_path / "mine.yaml").write_text(
        "themes:\n"
        "  chalk:\n"
        "    font: Martian Mono\n"
        "    font-size: 20\n"
        "    line-height: 0.5\n"
        "    indent-width: 1.0\n"
        "    bg-color: '#2b3a2b'\n"
        "    text-color: white\n"
        "    highlight-color: yellow\n",
        encoding="utf-8",
    )
    chalk = Theme.from_settings({"themes": "mine.yaml", "theme": "chalk"}, base_dir=tmp_path)
    assert chalk.font_size == 20
    # built-in themes stay available alongside the user's
    assert Theme.from_settings({"themes": "mine.yaml", "theme": "idle"}, base_dir=tmp_path).name == "idle"
