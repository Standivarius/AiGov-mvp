"""Sync taxonomy and evidence pack contracts from AiGov-specs into EP."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


_STABLE_SIGNALS_GENERATED_FROM = "AiGov-specs/docs/contracts/taxonomy/signals.json (snapshot)"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync taxonomy and evidence pack contracts from AiGov-specs."
    )
    parser.add_argument(
        "--specs-root",
        default="..\\AiGov-specs",
        help="Path to AiGov-specs repo root",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    specs_root = Path(args.specs_root)
    src_dir = specs_root / "docs" / "contracts" / "taxonomy"
    dest_dir = Path(__file__).resolve().parents[1] / "aigov_ep" / "taxonomy" / "contracts"
    schema_src = specs_root / "schemas" / "behaviour_json_v0_phase0.schema.json"
    schema_dest = Path(__file__).resolve().parents[1] / "aigov_ep" / "contracts"
    evidence_src = specs_root / "docs" / "contracts" / "evidence_pack"
    evidence_dest = schema_dest / "evidence_pack"
    evidence_manifest_src = specs_root / "schemas" / "evidence_pack_manifest_v1.json"

    sources = {
        "signals.json": src_dir / "signals.json",
        "verdicts.json": src_dir / "verdicts.json",
    }
    extra_files = {
        "behaviour_json_v0_phase0.schema.json": schema_src,
    }
    evidence_files = {
        "evidence_pack_v0.schema.json": evidence_src / "evidence_pack_v0.schema.json",
        "evidence_pack_manifest_v1.json": evidence_manifest_src,
    }

    missing = [name for name, path in sources.items() if not path.exists()]
    missing += [name for name, path in extra_files.items() if not path.exists()]
    missing += [name for name, path in evidence_files.items() if not path.exists()]
    if missing:
        print(f"ERROR: missing source files: {', '.join(missing)}")
        return 2

    dest_dir.mkdir(parents=True, exist_ok=True)
    for name, src_path in sources.items():
        dest_path = dest_dir / name
        shutil.copyfile(src_path, dest_path)
        print(f"copied {src_path} -> {dest_path}")

    # Keep vendored signals.json stable to avoid recurring diffs on generated_from.
    signals_path = dest_dir / "signals.json"
    if signals_path.exists():
        payload = json.loads(signals_path.read_text(encoding="utf-8"))
        payload["generated_from"] = _STABLE_SIGNALS_GENERATED_FROM
        signals_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    schema_dest.mkdir(parents=True, exist_ok=True)
    for name, src_path in extra_files.items():
        dest_path = schema_dest / name
        shutil.copyfile(src_path, dest_path)
        print(f"copied {src_path} -> {dest_path}")

    evidence_dest.mkdir(parents=True, exist_ok=True)
    for name, src_path in evidence_files.items():
        dest_path = evidence_dest / name
        shutil.copyfile(src_path, dest_path)
        print(f"copied {src_path} -> {dest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
