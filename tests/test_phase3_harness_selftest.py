"""Phase 3 — Harness honesty: injected pipeline failure must be detectable.

Documents and tests the pipefail contract used by CP10 browser step.
"""
import subprocess
import sys


def test_pipefail_detects_node_exit_1():
    """With pipefail, node exit 1 through tee must yield non-zero pipeline status."""
    script = r"""
set -o pipefail
node -e 'process.exit(1)' | tee /tmp/cp10-phase3-selftest.log
"""
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert r.returncode != 0, "pipefail must surface node exit 1 (harness honesty)"


def test_without_pipefail_masks_node_exit_1():
    """Control: without pipefail, tee success can mask node failure (Phase 2 lesson)."""
    script = r"""
node -e 'process.exit(1)' | tee /tmp/cp10-phase3-selftest-nopipe.log
"""
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    # On bash without pipefail, expected success (0) — documents the defect class
    assert r.returncode == 0, "control: without pipefail, masking is expected"
