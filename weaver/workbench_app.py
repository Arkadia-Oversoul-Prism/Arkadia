"""WEAVER-W1 — Local-first operator entry (stdlib only).

  python -m weaver.workbench_app observatory
  python -m weaver.workbench_app analyze "Explain the current Weaver architecture."

No mutation. No PassSpec inference. No second write path.
"""
from __future__ import annotations

import argparse
import json
import sys

from .workbench_view import (
    observatory,
    render_text_observatory,
    render_text_pipeline,
    run_read_only_pipeline,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Weaver Workbench W1 (read-only default)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("observatory", help="Show repository + authority + lifecycle")

    a = sub.add_parser("analyze", help="Run read-only analysis→plan→changeset→patch pipeline")
    a.add_argument("objective", nargs="+", help="Engineering objective text")
    a.add_argument("--json", action="store_true", help="Emit JSON")

    args = p.parse_args(argv)
    if args.cmd == "observatory":
        state = observatory()
        print(render_text_observatory(state))
        return 0
    if args.cmd == "analyze":
        objective = " ".join(args.objective)
        result = run_read_only_pipeline(objective)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(render_text_pipeline(result))
            print()
            print(render_text_observatory(observatory(pipeline=result.get("pipeline"))))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
