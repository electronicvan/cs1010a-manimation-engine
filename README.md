# CS1010A Manimation Engine

Animate code walkthroughs in [Manim](https://www.manim.community/) from a CSV script. Appends, inserts, highlights, pulses and replacements are written as rows, with no Python needed.


## Install

```bash
pip install cs1010a-manimation-engine
```

Requires Python 3.11+ and Manim 0.22 (installed automatically; see Manim's install guide if Cairo/Pango are missing on your system).

The built-in themes use the **Martian Mono** font. Install it from [Google Fonts](https://fonts.google.com/specimen/Martian+Mono), or choose another font with `# font: <name>` (see [Themes](#themes)).


## Quick start

```bash
manimation path/to/script.csv -pql
```

Two example scripts are in [`examples/`](examples):
- [`binary_search.csv`](examples/binary_search.csv) builds up a recursive binary search, then rewrites it to use indices.
- [`feature_tour.csv`](examples/feature_tour.csv) shows scrolling, escaped Replace, `*`, `&` batching and a custom window size.

| Option | Meaning |
|--------|---------|
| `-q l\|m\|h\|p\|k` | Quality: 480p15, 720p30, 1080p60 (default), 1440p60, 2160p60 |
| `-p` | Open the video when done |
| `--media-dir DIR` | Output folder (default `./media`) |
| `--disable-caching` | Re-render every animation |

Several CSVs can be given at once. Each video is written to `<media-dir>/videos/<csv name>/<csv name>.mp4` and its path is printed.

The layout does not depend on quality: `-ql` previews are exactly what `-qh` renders, at lower resolution.

### From Python

```python
from cs1010a_manimation_engine import render

video = render("path/to/script.csv", quality="l", preview=True)
```

### With the `manim` command

Subclass `CodeScene` and point it at a script:

```python
# slides.py
from cs1010a_manimation_engine import CodeScene

class BinarySearch(CodeScene):
    script = "examples/binary_search.csv"
```

```bash
manim -pql slides.py BinarySearch
```


## Script format

A script is a CSV where each row is one animation step, optionally preceded by a theme header:

```csv
# theme: terminal
# width: 1300
# height: 600
Rel,Time,Type,Line,Content,Duration,Effect
,,Append,,"def binary_search(key, seq):"
+,1,Append,,    mid = len(seq) // 2
+,1,Highlight,1,len(seq),,temporary
+,1,FadeOut,,,0.5
+,1,Pulse,1,len,2
+,1,Replace,1,len(seq) // 2 -> (low + high) // 2
+,1,Replace,*,seq -> arr,,transform
```

### Columns

| Column | Description |
|--------|-------------|
| `Rel` | `@` = start at the absolute time `Time`; `+` = wait `Time` after the previous action; `&` = play together with the previous row |
| `Time` | `mm:ss` or seconds (`1:30`, `0:10`, `0.5`). The first row always starts at `0:00` |
| `Type` | `Append`, `Insert`, `Highlight`, `Pulse`, `Replace`, `FadeOut`, `Wait` |
| `Line` | 0-based line index (defaults to the last line). `*` = every line containing the substring |
| `Content` | Code to add, the substring to highlight/pulse, or `old -> new` for Replace. Leading spaces are indentation (4 per level) |
| `Duration` | *(optional)* speed multiplier for the animation (default `1.0`); for `Wait`, seconds to hold. Can be blank, left off the row, or dropped from the header |
| `Effect` | *(optional)* Replace: `backspace` (default) or `transform`. Highlight: `persistent` (default) or `temporary`, and/or a colour (`#ff7700`, `green`), comma-separated |

### Action types

| Type | Does |
|------|------|
| `Append` | Adds line(s) at the end (multiline Content adds several) |
| `Insert` | Inserts line(s) before `Line`, sliding the rest down |
| `Highlight` | Boxes the substring. `temporary` boxes vanish when the next highlight appears |
| `Pulse` | Briefly enlarges the substring |
| `Replace` | Replaces every match in the line: `backspace` retypes them left to right, `transform` morphs them all at once |
| `FadeOut` | Removes all highlight boxes |
| `Wait` | Holds for `Duration` seconds (default 1). `Time` is the gap before it, as on any row: `+,2,Wait,,,3` waits 2 s, then holds 3 s. Batched with `&`, it makes the batch last at least `Duration` |

### Replace syntax

`old -> new`. Whitespace around `->` and at either end is ignored. Backslash escapes the next character:

| Escape | Means |
|--------|-------|
| `\->` | a literal `->` (not the separator) |
| `\s` | a literal space, for leading/trailing whitespace that matters |
| `\'` `\"` `\\` | literal quote / backslash |

```csv
+,1,Replace,0,\-> int -> \-> float
+,1,Replace,3,\s//\s -> \s/\s
+,1,Replace,2,foo\s ->
```

Leave `new` empty to delete. The quoted form `'old' -> 'new'` also works.

### Playing rows together

`&` batches a row with the one before it:

```csv
+,2,Pulse,2,rcross_bb,2
&,0,Pulse,3,rcross_bb,2
&,0,Pulse,5,rcross_bb,2
```

A batched row sees lines added earlier in its batch, so this highlights the line being written:

```csv
+,1,Append,,"show(heart_bb)"
&,0,Highlight,,heart_bb
```

If an earlier row in the batch scrolls or shifts lines, that movement plays first, then the batched rows play together at the new positions.

### Scrolling

When code runs past the bottom of the window, the block scrolls up as each new line is written. Acting on a line that has scrolled out of view (Highlight/Pulse/Replace with a line number) scrolls back to it first.

`Line=*` works differently by type:
- **Highlight/Pulse:** only lines currently in view.
- **Replace:** animates the matches in view, then scrolls to each further screenful of matches. When it has to scroll, it plays on its own rather than alongside `&` rows.


## Themes

Built-in themes: `terminal` (default; dark, in a terminal window) and `idle` (Python IDLE colours, no window). Pick one in the header with `# theme: <name>`. Any other `# key: value` line overrides that setting for this video:

| Key | Meaning |
|-----|---------|
| `font`, `font-size` | Text font and size |
| `line-height`, `indent-width` | Scene units between lines / per indent level |
| `bg-color`, `text-color`, `highlight-color` | Colours: hex (`#11111b`) or Manim names (`white`) |
| `window` | `true` draws a terminal window around the code |
| `window-color`, `border-color` | Window body and outline colours |
| `width`, `height` | Window size in pixels on a 1920×1080 frame (default: fill the frame). Video resolution still follows `-q` |
| `syntax.keyword`, `syntax.bool`, `syntax.defname` | Syntax colours |

Unknown keys print a warning, and lines too wide for the window print a warning too.

To define your own themes, write a YAML file shaped like the [built-in one](src/cs1010a_manimation_engine/themes.yaml) and reference it from the script (path relative to the CSV):

```csv
# themes: my_themes.yaml
# theme: chalkboard
```

Its themes are added to the built-in ones, and its `default:` (if any) replaces `terminal`.


## Extending

Register a new action type and it becomes available in the `Type` column:

```python
from manim import Wiggle
from cs1010a_manimation_engine import ActionType, AnimPhase, Step, register_action

@register_action
class Shake(ActionType):
    name = "Shake"

    def build(self, scene, action):
        line = scene.block[self.target_line(scene, action)]
        return Step([AnimPhase(anims=[Wiggle(line)], run_time=action.duration, pre=None, post=None)])
```

`build` receives the `CodeScene` (with `theme`, `block`, `overlays`, `lines`, `timeline`) and the parsed `Action` row. It returns a `Step` of animation phases, which are merged with the rest of the row's `&` batch. Set `uses_layout = False` on types that don't read line positions (like Append), so a batched row of that type doesn't wait for earlier rows' scrolling to finish.


## Development

```bash
uv sync
uv run pytest
```

The tests include rendering both example scripts.


## License

MIT. See [LICENSE](LICENSE).
