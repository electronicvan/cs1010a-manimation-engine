from cs1010a_manimation_engine.actions import ACTION_TYPES, ActionType, get_action_type, register_action
from cs1010a_manimation_engine.text import find_all, manim_index, pattern_indices, substring_indices
from cs1010a_manimation_engine.timeline import AnimPhase, merge_phase_lists


def test_manim_index_skips_whitespace():
    raw = "    acc = acc + x"
    assert manim_index(raw, 0) == 0
    assert manim_index(raw, 4) == 0          # indentation has no glyphs
    assert manim_index(raw, 8) == 3          # just past 'acc '


def test_glyph_count_matches_non_space_chars():
    raw = "    acc = acc + x"
    assert manim_index(raw, len(raw)) == len(raw.replace(" ", ""))


def test_find_all_matches_str_replace():
    raw = "total(xs) // len(xs)"
    assert find_all(raw, "xs") == [6, 17]
    assert find_all("abb", "ab") == [0]
    assert find_all("aaaa", "aa") == [0, 2]   # non-overlapping, like str.replace


def test_substring_indices():
    assert substring_indices("def f(x):", "f(x)") == (3, 7)
    assert substring_indices("def f(x):", "zzz") == (None, None)
    assert substring_indices("a b", "b") == (1, 2)   # end of line


def test_pattern_indices():
    assert pattern_indices("if x in xs:", r"\b(if|in)\b") == [(0, 2), (3, 5)]


def test_merge_phase_lists_takes_longest_run_time_and_chains_callbacks():
    calls = []
    a = [AnimPhase(["a0"], 0.4, lambda: calls.append("pre a"), None),
         AnimPhase(["a1"], 0.1, None, lambda: calls.append("post a"))]
    b = [AnimPhase(["b0"], 0.6, lambda: calls.append("pre b"), None)]
    merged = merge_phase_lists([a, b])
    assert [p.anims for p in merged] == [["a0", "b0"], ["a1"]]
    assert [p.run_time for p in merged] == [0.6, 0.1]
    merged[0].pre()
    merged[1].post()
    assert calls == ["pre a", "pre b", "post a"]
    assert merged[1].pre is None


def test_builtin_action_types_registered():
    assert set(ACTION_TYPES) >= {"append", "insert", "highlight", "pulse", "replace", "fadeout", "wait"}
    assert get_action_type("HIGHLIGHT").name == "Highlight"


def test_register_custom_action():
    @register_action
    class Shake(ActionType):
        name = "Shake"
        def build(self, scene, action):
            return None
    try:
        assert get_action_type("shake") is Shake
    finally:
        del ACTION_TYPES["shake"]
