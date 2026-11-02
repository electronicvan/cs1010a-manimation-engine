import pytest

from cs1010a_manimation_engine.script import Action, Script, coerce, parse_replace, parse_time


@pytest.mark.parametrize("text, seconds", [
    ("", 0.0), ("0", 0.0), ("2", 2.0), ("0.5", 0.5), ("1:30", 90.0), (" 0:16 ", 16.0),
])
def test_parse_time(text, seconds):
    assert parse_time(text) == seconds


@pytest.mark.parametrize("text, value", [
    ("400", 400), ("0.6", 0.6), ("true", True), ("No", False), ("black", "black"), ("#11111b", "#11111b"),
])
def test_coerce(text, value):
    assert coerce(text) == value


@pytest.mark.parametrize("content, expected", [
    ("mean -> avg", ("mean", "avg")),
    (r"\-> int -> \-> float", ("-> int", "-> float")),
    (r"\s//\s -> \s/\s", (" // ", " / ")),
    (r"foo\s ->", ("foo ", "")),
    (r"\'a\' -> \"b\"", ("'a'", '"b"')),
    (r"a\\b -> c", ("a\\b", "c")),
    # legacy quoted forms
    ("'acc = 0' -> 'acc = 0.0'", ("acc = 0", "acc = 0.0")),
    ("'(' -> '(scale(1/2,'", ("(", "(scale(1/2,")),
    ("'sail_bb))' -> ''", ("sail_bb))", "")),
    ('"seq[:mid]" -> "low, mid - 1"', ("seq[:mid]", "low, mid - 1")),
    # malformed
    ("a -> b -> c", None),
    ("-> x", None),
    ("no arrow", None),
])
def test_parse_replace(content, expected):
    assert parse_replace(content) == expected


def test_header_settings_and_rows():
    script = Script.from_text(
        "# theme: terminal\n"
        "# width: 1300\n"
        "# bg-color: black\n"
        "Rel,Time,Type,Line,Content,Duration,Effect\n"
        ",,Append,,def f(x):\n"
        "+,0.5,Append,,    return x\n"
        "+,1,Highlight,*,x,2,\"temporary,#ff7700\"\n"
    )
    assert script.settings == {"theme": "terminal", "width": 1300, "bg-color": "black"}
    first, second, third = script.actions
    assert first == Action(rel="", time="", type="append", line="", content="def f(x):")
    assert second.content == "    return x"          # indentation kept
    assert second.seconds == 0.5
    assert third.is_wildcard and third.line_index is None
    assert third.duration == 2.0
    assert third.effects == ("temporary", "#ff7700")


def test_duration_column_optional():
    script = Script.from_text("Rel,Time,Type,Line,Content\n+,1,Pulse,3,x\n")
    (action,) = script.actions
    assert action.duration == 1.0 and action.effects == () and action.line_index == 3


def test_bad_duration_falls_back_to_one():
    (action,) = Script.from_text("Rel,Time,Type,Line,Content,Duration\n+,1,Pulse,,x,abc\n").actions
    assert action.duration == 1.0


def test_from_csv_strips_bom_and_names_script(tmp_path):
    path = tmp_path / "slide7.csv"
    path.write_text("﻿Rel,Time,Type,Line,Content\n+,0,Append,,x\n", encoding="utf-8")
    script = Script.from_csv(path)
    assert script.name == "slide7"
    assert script.actions[0].type == "append"
