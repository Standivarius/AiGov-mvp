"""EP runtime CLI skeleton.

Pointers:
- Canonical terminology: AiGov-specs/docs/contracts/terminology.md
- Program pack: AiGov-specs/docs/program/ACTION_PLAN.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Iterable, Optional

from aigov_ep.bundle.compiler import BundleCompileError, compile_single_scenario_bundle
from aigov_ep.execute.runner import run_scenario
from aigov_ep.intake.validate import validate_intake
from aigov_ep.reporting.generate import generate_report


def _make_handler(action: Callable[[], None]) -> Callable[[argparse.Namespace], int]:
    def _handler(_: argparse.Namespace) -> int:
        try:
            action()
        except NotImplementedError as exc:
            print(str(exc))
            return 2
        return 0

    return _handler


def _run_offline_judge_stub() -> None:
    raise NotImplementedError("run_offline_judge: NOT IMPLEMENTED (skeleton)")


def _execute_handler(args: argparse.Namespace) -> int:
    config = {}
    if args.config:
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as exc:
            print(f"ERROR: Invalid JSON for --config ({exc.msg})")
            return 2

    try:
        scenario_path = args.scenario
        if not scenario_path:
            bundle_dir = Path(args.bundle_dir)
            manifest_path = bundle_dir / "bundle_manifest.json"
            if not manifest_path.exists():
                print(f"ERROR: bundle_manifest.json not found in {bundle_dir}")
                return 2
            try:
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    manifest = json.load(handle)
            except json.JSONDecodeError as exc:
                print(f"ERROR: Invalid bundle_manifest.json ({exc.msg})")
                return 2
            scenarios = manifest.get("scenarios") or []
            if not scenarios or not isinstance(scenarios, list):
                print("ERROR: bundle_manifest.json missing scenarios list")
                return 2
            file_path = scenarios[0].get("file_path") if isinstance(scenarios[0], dict) else None
            if not file_path:
                print("ERROR: bundle_manifest.json missing scenarios[0].file_path")
                return 2
            scenario_path = str((bundle_dir / file_path).resolve())
        result = run_scenario(scenario_path, args.target, args.out, config)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"RUN_DIR={result.run_dir}")
    return 0


def _bundle_handler(args: argparse.Namespace) -> int:
    try:
        result = compile_single_scenario_bundle(args.scenario, args.out, args.client_id)
    except BundleCompileError as exc:
        print(f"ERROR: {exc}")
        return 2
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"BUNDLE_DIR={result.get('bundle_dir')}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aigov-ep",
        description="AiGov EP runtime (client-run evaluation product)",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    command_map = [
        ("intake", validate_intake),
        ("judge", _run_offline_judge_stub),
        ("report", generate_report),
    ]

    for name, action in command_map:
        subparser = subparsers.add_parser(name, help=f"{name} command")
        subparser.set_defaults(func=_make_handler(action))

    bundle_parser = subparsers.add_parser("bundle", help="bundle command")
    bundle_parser.add_argument("--scenario", required=True, help="Path to scenario YAML/JSON file")
    bundle_parser.add_argument("--out", default="bundles", help="Output directory")
    bundle_parser.add_argument("--client-id", help="Client identifier")
    bundle_parser.set_defaults(func=_bundle_handler)

    execute_parser = subparsers.add_parser("execute", help="execute command")
    source_group = execute_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--scenario", help="Path to scenario YAML/JSON file")
    source_group.add_argument("--bundle-dir", help="Path to bundle directory")
    execute_parser.add_argument("--target", required=True, help="Target adapter name")
    execute_parser.add_argument("--out", default="runs", help="Output directory")
    execute_parser.add_argument("--config", help="JSON string for target config")
    execute_parser.set_defaults(func=_execute_handler)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
