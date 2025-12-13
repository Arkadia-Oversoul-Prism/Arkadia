import argparse
import sys
from weaver.agent import run
from weaver import RecursiveEngine

parser = argparse.ArgumentParser(description="Arkadia Weaver CLI")
parser.add_argument("task", nargs="?", default="", help="Task description to run")
parser.add_argument("--recursive", action="store_true", help="Run in recursive multi-step mode")
parser.add_argument("--enabled", action="store_true", help="Enable recursive engine when used")

args = parser.parse_args()

if args.recursive:
    engine = RecursiveEngine(initial_task=args.task, enabled=args.enabled)
    engine.start()
else:
    if not args.task:
        print("Usage: python weaver.py 'task description'")
        sys.exit(1)
    run(args.task)
