from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .importer import LRImporter
from .launcher import DarktableLauncher


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    cli_keywords: list[str] | None = None
    if args.keywords is not None:
        cli_keywords = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]

    importer = LRImporter(Path(args.input))
    images = importer.import_images()
    if not images:
        print("No images found in the catalogue", file=sys.stderr)
        return 1

    if args.xmp:
        importer.export_xmp(images, cli_keywords)
    launcher = DarktableLauncher(darktable_binary=args.app)
    process = launcher.launch(Path(args.output), [image.path for image in images])
    return process.wait()

def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import catalogue into darktable")
    parser.add_argument("--input", required=True, help="Path to the input catalogue (.lrcat)")
    parser.add_argument("--output", required=False, help="Path to the target darktable library (defaults to input with .db extension)")
    parser.add_argument(
        "--xmp",
        action="store_true",
        help="Export XMP metadata",
    )
    parser.add_argument(
        "--keywords",
        help="Comma-separated list of keywords to append to the exported XMP files",
    )
    parser.add_argument(
        "--app",
        default="darktable",
        help="Name of darktable binary to use (default: darktable)",
    )
    parsed = parser.parse_args(args=list(argv) if argv is not None else None)
    # If output not provided, derive it from input by changing extension to .db
    if not getattr(parsed, "output", None):
        input_path = Path(parsed.input)
        derived = input_path.with_suffix(".db")
        parsed.output = str(derived)
        print(f"Output library not provided, using derived path: {parsed.output}", file=sys.stderr)
    return parsed

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - safety net for CLI entrypoint
        print(f"darktable-importer failed: {exc}", file=sys.stderr)
        raise