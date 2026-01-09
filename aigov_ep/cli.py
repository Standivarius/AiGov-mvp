"""EP runtime CLI skeleton.

Pointers:
- Canonical terminology: AiGov-specs/docs/contracts/terminology.md
- Program pack: AiGov-specs/docs/program/ACTION_PLAN.md
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Optional


NOT_IMPLEMENTED_MESSAGE = "NOT IMPLEMENTED (skeleton)"


def _not_implemented(_: argparse.Namespace) -> int:
    print(NOT_IMPLEMENTED_MESSAGE, file=sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aigov-ep",
        description="AiGov EP runtime (client-run evaluation product)",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    for name in ["intake", "bundle", "execute", "judge", "report"]:
        subparser = subparsers.add_parser(name, help=f"{name} command")
        subparser.set_defaults(func=_not_implemented)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())