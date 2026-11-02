"""The ``manimation`` command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .render import QUALITIES, render


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="manimation",
        description="Render CSV animation scripts of code walkthroughs to video.",
    )
    parser.add_argument("csv", nargs="+", type=Path, help="script(s) to render")
    parser.add_argument("-q", "--quality", choices=list(QUALITIES), default="h",
                        help="l=480p15, m=720p30, h=1080p60 (default), p=1440p60, k=2160p60")
    parser.add_argument("-p", "--preview", action="store_true", help="open the video when done")
    parser.add_argument("--media-dir", type=Path, default=Path("media"),
                        help="output folder (default: ./media)")
    parser.add_argument("--disable-caching", action="store_true",
                        help="re-render every animation instead of reusing cached ones")
    args = parser.parse_args(argv)

    failed = False
    for csv_path in args.csv:
        try:
            video = render(csv_path, quality=args.quality, preview=args.preview,
                           media_dir=args.media_dir, disable_caching=args.disable_caching)
        except (FileNotFoundError, ValueError) as e:
            print(f"manimation: {e}", file=sys.stderr)
            failed = True
            continue
        print(video)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
