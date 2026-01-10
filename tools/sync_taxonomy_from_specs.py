"""Sync taxonomy contracts from AiGov-specs into EP."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync taxonomy contracts from AiGov-specs.")
    parser.add_argument("--specs-root", default="..\\AiGov-specs", help="Path to AiGov-specs repo root")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    specs_root = Path(args.specs_root)
    src_dir = specs_root / "docs" / "contracts" / "taxonomy"
    dest_dir = Path(__file__).resolve().parents[1] / "aigov_ep" / "taxonomy" / "contracts"

    sources = {
        "signals.json": src_dir / "signals.json",
        "verdicts.json": src_dir / "verdicts.json",
    }

    missing = [name for name, path in sources.items() if not path.exists()]
    if missing:
        print(f"ERROR: missing source files: {', '.join(missing)}")
        return 2

    dest_dir.mkdir(parents=True, exist_ok=True)
    for name, src_path in sources.items():
        dest_path = dest_dir / name
        shutil.copyfile(src_path, dest_path)
        print(f"copied {src_path} -> {dest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
