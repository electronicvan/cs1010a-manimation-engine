"""Timing of Wait rows and what '&' rows see — small renders at low quality."""

import numpy as np
import pytest
from manim import tempconfig

from cs1010a_manimation_engine import CodeScene, Script

HEADER = "Rel,Time,Type,Line,Content,Duration,Effect\n"
FINAL_WAIT = 2.0    # CodeScene holds the last frame this long
WRITE = 0.4         # one Append at Duration 1


def play(tmp_path, rows: str) -> CodeScene:
    # The scene must be created inside tempconfig: it reads the config when constructed.
    with tempconfig({"quality": "low_quality", "media_dir": str(tmp_path), "disable_caching": True}):
        scene = CodeScene(Script.from_text(HEADER + rows))
        scene.render()
    return scene


@pytest.mark.parametrize("rows, expected", [
    # Time is the gap before the row; Duration is the hold (default 1 s).
    (",,Append,,x\n+,2,Wait,,,2\n", WRITE + 2 + 2),
    (",,Append,,x\n+,2,Wait\n", WRITE + 2 + 1),
    (",,Append,,x\n@,0:03,Wait,,,0.5\n", 3 + 0.5),
    (",,Append,,x\n+,0,Wait\n", WRITE + 1),
    # Batched: holds alongside the batch, which lasts max(write, hold).
    (",,Append,,x\n+,0,Append,,y\n&,0,Wait,,,1.5\n", WRITE + 1.5),
])
def test_wait_timing(tmp_path, rows, expected):
    assert play(tmp_path, rows).time == pytest.approx(expected + FINAL_WAIT, abs=0.07)


def test_batched_highlight_targets_line_appended_in_same_batch(tmp_path):
    scene = play(tmp_path, ",,Append,,x = 1\n+,0,Append,,foo = 2\n&,0,Highlight,,foo\n")
    (overlay,) = scene.overlays.persistent
    assert overlay.line is scene.block[1]
    assert overlay.line.raw_text == "foo = 2"
    # drawn around the new line where it ended up, not where it was created
    assert abs(overlay.get_y() - overlay.line.get_y()) < 0.1


def test_batched_row_sees_insert_shift(tmp_path):
    scene = play(tmp_path, ",,Append,,a\n+,0,Append,,b\n+,0,Insert,0,z\n&,0,Highlight,1,a\n")
    assert [line.raw_text for line in scene.block] == ["z", "a", "b"]
    (overlay,) = scene.overlays.persistent
    assert overlay.line.raw_text == "a"
    assert abs(overlay.get_y() - overlay.line.get_y()) < 0.1


def test_batched_highlight_after_scroll_lands_on_final_position(tmp_path):
    rows = ",,Append,,line0\n" + "".join(f"+,0,Append,,line{i}\n" for i in range(1, 9))
    rows += "+,0,Append,,last\n&,0,Highlight,,last\n"      # 10th line scrolls the window
    scene = play(tmp_path, rows)
    assert scene.block.scroll_top == 1
    (overlay,) = scene.overlays.persistent
    assert overlay.line.raw_text == "last"
    assert np.allclose(overlay.get_center()[1], overlay.line.get_center()[1], atol=0.1)
