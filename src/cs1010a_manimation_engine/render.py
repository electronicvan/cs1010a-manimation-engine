"""Rendering a script to a video file."""

from __future__ import annotations

import os
from pathlib import Path

from manim import tempconfig

from .scene import CodeScene
from .script import Script

QUALITIES = {
    "l": "low_quality",         # 854x480, 15 fps
    "m": "medium_quality",      # 1280x720, 30 fps
    "h": "high_quality",        # 1920x1080, 60 fps
    "p": "production_quality",  # 2560x1440, 60 fps
    "k": "fourk_quality",       # 3840x2160, 60 fps
}


def render(script: Script | str | Path, quality: str = "h", preview: bool = False,
           media_dir: str | Path = "media", disable_caching: bool = False,
           scene_class: type[CodeScene] = CodeScene) -> Path:
    """Render *script* (a Script or a CSV path) and return the video's path.

    The video is written to ``<media_dir>/videos/<csv name>/<csv name>.mp4``.
    *quality* is one of l, m, h, p, k (as Manim's -q flag).
    """
    if quality not in QUALITIES:
        raise ValueError(f"quality must be one of {', '.join(QUALITIES)}, not {quality!r}")
    if not isinstance(script, Script):
        path = Path(script)
        if not path.is_file():
            raise FileNotFoundError(f"CSV not found: {str(path)!r}")
        script = Script.from_csv(path)

    # Name both the output folder and the video file after the CSV.
    with tempconfig({
        "quality": QUALITIES[quality],
        "media_dir": str(media_dir),
        "video_dir": os.path.join(str(media_dir), "videos", script.name),
        "output_file": script.name,
        "disable_caching": disable_caching,
    }):
        scene = scene_class(script)
        scene.render(preview=preview)
        return Path(scene.renderer.file_writer.final_file_path)
