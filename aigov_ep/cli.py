"""EP runtime CLI skeleton.

Pointers:
- Canonical terminology: AiGov-specs/docs/contracts/terminology.md
- Program pack: AiGov-specs/docs/program/ACTION_PLAN.md
"""

from __future__ import annotations

import argparse
from typing import Callable, Iterable, Optional

from aigov_ep.artifacts.manifests import write_manifest
from aigov_ep.bundle.compiler import compile_bundle
from aigov_ep.execute.runner import run_stage_a
from aigov_ep.intake.validate import validate_intake
from aigov_ep.judge.judge import run_offline_judge
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
        ("execute", run_stage_a),
        ("judge", run_offline_judge),
        ("report", generate_report),
    ]

    for name, action in command_map:
        subparser = subparsers.add_parser(name, help=f"{name} command")
        subparser.set_defaults(func=_make_handler(action))

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
