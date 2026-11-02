"""End-to-end renders: a small script exercising every action type, and the examples."""

import logging
from pathlib import Path

import pytest

from cs1010a_manimation_engine import render
from cs1010a_manimation_engine.cli import main

EXAMPLES = Path(__file__).parent.parent / "examples"

SCRIPT = """\
# theme: terminal
# width: 900
# height: 400
Rel,Time,Type,Line,Content,Duration,Effect
,,Append,,def f(xs):
+,0,Append,,    for x in xs:
+,0,Append,,        print(x)
+,0,Append,,    return xs
+,0,Insert,1,    xs = list(xs)
+,0,Highlight,*,xs,,temporary
+,0,Pulse,0,def
+,0,FadeOut,,,0.5
+,0,Replace,*,xs -> items
+,0,Replace,0,f -> g,,transform
+,0,Wait,0.2,
"""


def test_render_script(tmp_path):
    csv = tmp_path / "smoke.csv"
    csv.write_text(SCRIPT, encoding="utf-8")
    video = render(csv, quality="l", media_dir=tmp_path / "media", disable_caching=True)
    assert video.name == "smoke.mp4"
    assert video.parent.name == "smoke"
    assert video.stat().st_size > 0


@pytest.mark.parametrize("example", sorted(EXAMPLES.glob("*.csv")), ids=lambda p: p.stem)
def test_examples_render(tmp_path, example, caplog):
    with caplog.at_level(logging.WARNING, logger="cs1010a_manimation_engine"):
        video = render(example, quality="l", media_dir=tmp_path / "media", disable_caching=True)
    assert video.stat().st_size > 0
    # the engine's own warnings, e.g. a line too wide or an unknown theme key
    ours = [r.getMessage() for r in caplog.records if r.name.startswith("cs1010a_manimation_engine")]
    assert not ours


def test_cli_reports_missing_csv(tmp_path, capsys):
    assert main([str(tmp_path / "missing.csv"), "-ql"]) == 1
    assert "CSV not found" in capsys.readouterr().err
