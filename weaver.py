import sys
from weaver.agent import run

if len(sys.argv) < 2:
    print("Usage: python weaver.py 'task description'")
    sys.exit(1)

run(sys.argv[1])
