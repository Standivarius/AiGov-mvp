"""EP runtime CLI skeleton.

Pointers:
- Canonical terminology: AiGov-specs/docs/contracts/terminology.md
- Program pack: AiGov-specs/docs/program/ACTION_PLAN.md
"""

from __future__ import annotations

import argparse
import json
from typing import Callable, Iterable, Optional

from aigov_ep.artifacts.manifests import write_manifest
from aigov_ep.bundle.compiler import compile_bundle
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
        result = run_scenario(args.scenario, args.target, args.out, config)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"RUN_DIR={result.run_dir}")
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
        ("bundle", compile_bundle),
        ("judge", _run_offline_judge_stub),
        ("report", generate_report),
    ]

    for name, action in command_map:
        subparser = subparsers.add_parser(name, help=f"{name} command")
        subparser.set_defaults(func=_make_handler(action))

    execute_parser = subparsers.add_parser("execute", help="execute command")
    execute_parser.add_argument("--scenario", required=True, help="Path to scenario YAML/JSON file")
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
