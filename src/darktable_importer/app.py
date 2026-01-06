from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .importer import LRImporter
from .launcher import DarktableLauncher


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    importer = LRImporter()
    images = importer.import_images(Path(args.input))
    if not images:
        print("No images found in the catalogue", file=sys.stderr)
        return 1

    launcher = DarktableLauncher()
    process = launcher.launch(Path(args.output), [image.path for image in images])
    return process.wait()


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import catalogue into darktable")
    parser.add_argument("--input", required=True, help="Path to the input catalogue (.lrcat)")
    parser.add_argument("--output", required=True, help="Path to the target darktable library")
    parser.add_argument(
        "--xmp",
        action="store_true",
        help="Export XMP metadata",
    )
    return parser.parse_args(args=list(argv) if argv is not None else None)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - safety net for CLI entrypoint
        print(f"darktable-importer failed: {exc}", file=sys.stderr)
        raise