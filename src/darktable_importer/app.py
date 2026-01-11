from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from .importer import LRImporter
from .launcher import DarktableLauncher

logger = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.verbosity)
    
    # Log derived output path if it was auto-generated
    if not getattr(args, "_output_provided", True):
        logger.info(f"Output library not provided, using derived path: {args.output}")
    
    cli_keywords: list[str] | None = None
    if args.keywords is not None:
        cli_keywords = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]

    importer = LRImporter(Path(args.input))
    images = importer.import_images()
    if not images:
        logger.error("No images found in the catalogue")
        return 1

    if args.xmp:
        logger.info("Exporting XMP metadata")
        importer.export_xmp(images, cli_keywords)
    if args.donotlaunch:
        logger.info("--donotlaunch set; skipping launching of darktable")
        return 0
    logger.info(f"Launching {args.app} with library: {args.output}")
    launcher = DarktableLauncher(darktable_binary=args.app)
    process = launcher.launch(Path(args.output), [image.path for image in images])
    return process.wait()

def _configure_logging(verbosity: str) -> None:
    """Configure logging based on verbosity level."""
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    level = level_map.get(verbosity.lower(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        force=True,
    )

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
    parser.add_argument(
        "--verbosity",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging verbosity level (default: info)",
    )
    parser.add_argument(
        "--donotlaunch",
        action="store_true",
        help="Do not launch darktable after preparing the library and XMP files",
    )
    parsed = parser.parse_args(args=list(argv) if argv is not None else None)
    # If output not provided, derive it from input by changing extension to .db
    if not getattr(parsed, "output", None):
        input_path = Path(parsed.input)
        derived = input_path.with_suffix(".db")
        parsed.output = str(derived)
        parsed._output_provided = False
    else:
        parsed._output_provided = True
    return parsed

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - safety net for CLI entrypoint
        logging.error(f"darktable-importer failed: {exc}")
        raise