"""Boundary guard: a CI verdict step must be able to report failure.

A workflow that wants a soft step to still fail the job writes a terminal
enforcement asserting ``test '${{ steps.<id>.outcome }}' = success``. That
assertion is only meaningful when the step it names actually exists and its
``outcome`` actually reflects the command's exit status. Two defects break that,
and both leave a gate that *looks* enforced while being unable to fail.

1. **Phantom reference.** The enforcement names ``steps.<id>.outcome`` but no
   step in the job declares ``id: <id>``. GitHub substitutes the empty string, so
   the assertion degenerates and any summary line that prints it renders blank.
   The source shape is ``main`` @ ``850216fc``: ``sg-02-fe-2-v.yml`` printed
   ``Grove contracts: ${{ steps.grove.outcome }}`` in its evidence summary while
   the "Grove contracts" step declared no ``id``. The runtime log is run
   ``38150620847`` (``event=push``, head ``56ada9dd``), whose
   ``sg-02-fe-2-v.yml`` is byte-identical to ``main``'s and which is a ``main``
   ancestor; it shows the substituted line ``echo "Grove contracts: "`` — the
   value was empty, and the step was named by no enforcement.

2. **Masked verdict.** The step pipes a verdict command (``pytest``, ``node``,
   ``npm``, ...) into a passthrough (``tee``) without ``set -o pipefail``, so the
   pipeline's exit status is the passthrough's and is always ``0``. The step's
   ``outcome`` is then ``success`` no matter what the tests did, and the
   enforcement that is supposed to fail the job cannot. Measured in the same run
   (``38150620847``): the ``lab`` step printed ``2 failed, 9 passed`` and the
   terminal enforcement still printed ``test 'success' = success`` for all 16 of
   its assertions. (Count by *echoed command lines*: the log yields 16 of them,
   not 17 — a fixed-string ``grep`` also matches the ``##[group]Run test
   'success' = success`` header. The count is convention-dependent; the
   load-bearing fact is that no assertion could fail.)

3. **Exempt enforcement.** The enforcement step's own exit status is discarded, so
   the assertion it runs cannot fail the job. ``continue-on-error`` is the
   discarding property, at *either* level: a step-level ``continue-on-error: true``
   makes the step's ``outcome`` ``failure`` but its ``conclusion`` ``success``, and
   a job-level ``continue-on-error: true`` does the same to every step in the job.
   A non-``always()`` ``if:`` is the other discarding property, because it decides
   *whether* the step runs at all — an enforcement guarded by ``if: success()``
   never runs once something fails, which is exactly when it must run. ``if:
   always()`` does **not** discard the status: it changes whether the step runs,
   not what its exit status does, so it is the correct form for a terminal
   enforcement and is not reported. The corpus shape is ``sg-02-fe-2-v.yml``'s
   ``Enforce CP10 executable gates`` (``if: always()``, no ``continue-on-error``),
   which is why its assertions are live: GitHub's default shell for an unspecified
   ``shell`` is ``bash -e {0}``, so the first failing ``test`` aborts the step and
   the trailing ``exit 0`` is reached only when every assertion passed. Detector 4
   asserts that premise rather than assuming it.

4. **Abortless shell.** An enforcement step that runs under a shell without
   ``errexit`` evaluates every assertion and reaches its trailing ``exit 0``
   regardless, so it reports success whatever the steps it names did. ``bash -e``
   is what gives the assertions teeth: the first failing ``test`` aborts the step,
   and ``exit 0`` is reachable only when all of them passed. Setting ``shell:`` on
   the step, ``defaults.run.shell`` on the job, or ``set +e`` inside the script
   removes that, and detectors 1–3 stay green because none of them looks at the
   shell. Measured on the corpus shape (``sg-02-fe-2-v.yml``, run ``38099353157``,
   head ``c081d200``): under the default shell the enforcement step's conclusion is
   ``failure`` and the job is red; under ``bash {0}`` the same 17 assertions are
   all satisfied, the step exits ``0``, and the job would be green. The default is
   not merely assumed here — the corpus declares no ``shell`` anywhere, so an
   explicit abortless shell is a change to a currently-compliant surface.

All four are the same failure mode: a guard that cannot fail. The detectors below
are stated generically over the whole workflow corpus, derived from ``git ls-files``
at test time, so a new workflow is judged by the same rule without editing this
file. Each carries a negative control proving it reports the form it is meant to
catch, so a rewrite of a workflow cannot silently disarm the boundary.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# A command whose exit status is a verdict on the change under test.
_VERDICT_COMMAND = re.compile(
    r"(?:^|[\s;&|(])(?:python\s+-m\s+pytest|pytest|node|npm|pnpm|tsc)\b"
)

# A pipe target that forwards its input and reports its own exit status, hiding
# the verdict command's. `2>&1` is a redirection, not a pipe, so the split below
# must not treat it as a segment boundary.
_PASSTHROUGH = {"tee", "cat"}
_PIPE = re.compile(r"(?<!\|)\|(?!\|)")

# `\` + newline is a line continuation: the shell parses the continuation as
# part of the *same* command, so a pipeline split across it must be scanned as
# one logical line. Scanning physical lines misses the shape entirely.
_CONTINUATION = re.compile(r"\\\r?\n")

# `steps.<id>.<field>` — any reference to a step output.
_STEP_REFERENCE = re.compile(r"steps\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)")

# The repo's enforcement convention: `test '${{ steps.<id>.outcome }}' = success`.
_ENFORCEMENT = re.compile(r"steps\.([A-Za-z0-9_-]+)\.outcome\s*}}'\s*=\s*success")

# `always()` — the one condition that runs the step whatever happened before it,
# so it does not discard the step's exit status. A condition that is anything
# else decides *whether* the enforcement runs and is treated as an exemption.
_ALWAYS = re.compile(r"always\s*\(\s*\)")

# `-e` / `errexit` as a shell option. Matching the option rather than the shell
# name keeps the detector open to `bash -eo pipefail`, `sh -e`, and `zsh -e`.
# The option must start a whitespace-delimited token with a *single* dash:
# `--noprofile` and `-x` are not errexit, and a class that admits a second dash
# or any letter before the `e` reads them as one (measured: `--noprofile`
# contains an `e`, so `bash --noprofile {0}` was scored abortive).
_ERREXIT = re.compile(r"(?:^|\s)-[A-Za-z]*e[A-Za-z]*(?=\s|$)|(?:^|\s)(?:-o\s+)?errexit(?=\s|$)")

# An `errexit` that is *removed* inside the script. `set +e` (and its long form)
# turns abort-on-error off for the rest of the shell, so the trailing `exit 0`
# becomes unconditional even though the step's `shell:` looks abortive.
_SET_PLUS_E = re.compile(r"(?:^|[;&|(\s])set\s+\+[A-Za-z]*e[A-Za-z]*(?:\s|$)")


def _shell_aborts(shell: str | None, run: str) -> bool:
    """Does this enforcement step abort on the first failing assertion?

    GitHub's default for an unspecified ``shell`` is ``bash -e {0}``, so an
    absent declaration is abortive. An explicit declaration is abortive only when
    it names ``-e``/``errexit``; and a script that turns ``errexit`` back off with
    ``set +e`` reaches its trailing ``exit 0`` however the assertions went.
    """
    if isinstance(shell, str) and shell.strip() and not _ERREXIT.search(shell):
        return False
    return not _SET_PLUS_E.search(run)


# Enforced verdict steps whose exit status is currently destroyed by a pipe
# without `pipefail`. Recorded, not repaired: the repair is not this
# workstream's to make, and applying it here would turn `main` red on debt this
# change did not introduce.
#
#   lab      the two failing pins are in `tests/test_engineering_lab_api.py`
#            (`require_auth` -> `require_lab_auth`, and the new
#            `/api/lab/engineering/n-atlas/*` mutating endpoints). Repairing
#            them edits `api/lab_routes.py`, an authority surface carrying the
#            Lab mutation boundary — sovereign-only.
#   backend  `python -m pytest tests/` interrupts on the CE-01
#            `weaver.autonomy` module-vs-package collection error and runs no
#            tests at all; it needs `--continue-on-collection-errors` first.
#            CE-01 is reserved to the sovereign.
#
# The set is an inventory, not a filter: an entry that stops being masked fails
# `test_registered_masked_steps_are_still_masked`, so repairing one forces its
# removal rather than leaving a stale exemption standing.
REGISTERED_MASKED_VERDICT_STEPS = {
    ("sg-02-fe-2-v.yml", "lab"),
    ("sg-02-fe-2-v.yml", "backend"),
}

# Enforcement steps whose own exit status is currently discarded, so the
# assertions they run cannot fail the job. Recorded as an inventory for the same
# reason as the set above: the set must keep describing the repository, and a
# repaired entry has to be removed rather than left standing. Empty is the
# correct state — the corpus enforcement step is live.
#
# The corpus shape is `sg-02-fe-2-v.yml`'s `Enforce CP10 executable gates`
# (`if: always()`, no `continue-on-error`), which is why its 16 assertions are
# live: the default shell is `bash -e`, so the first failing `test` aborts it.
REGISTERED_EXEMPT_ENFORCEMENT_STEPS: set[tuple[str, str]] = set()

# Enforcement steps that run under a shell without `errexit`, so their assertions
# are all evaluated and `exit 0` is reached whatever the named steps did. Recorded
# as an inventory for the same reason as the sets above, and empty for the same
# reason: no workflow in the corpus declares a `shell` at all, so every
# enforcement runs under GitHub's abortive default.
REGISTERED_ABORTLESS_ENFORCEMENT_STEPS: set[tuple[str, str]] = set()


# ---------------------------------------------------------------------------
# Workflow loading
# ---------------------------------------------------------------------------


def _tracked_workflow_paths() -> list[Path]:
    """Every tracked workflow file — the guard's own domain, never restated."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", ".github/workflows/*.yml"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / p for p in result.stdout.decode().split("\0") if p]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _jobs(workflow: dict) -> dict:
    return workflow.get("jobs") or {}


def _steps(job: dict) -> list[dict]:
    return [s for s in (job.get("steps") or []) if isinstance(s, dict)]


def _strings(value) -> list[str]:
    """Every string nested anywhere inside a job/step value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


# ---------------------------------------------------------------------------
# Detector 1 — phantom step references
# ---------------------------------------------------------------------------


def phantom_step_references(job: dict) -> list[tuple[str, str]]:
    """``(referenced_id, offending_step)`` for every unresolved step reference.

    A reference resolves when some step in the *same job* declares that ``id``;
    ``steps`` is job-scoped, so a sibling job's id does not resolve it.
    """
    declared = {s["id"] for s in _steps(job) if isinstance(s.get("id"), str)}
    found: list[tuple[str, str]] = []
    for step in _steps(job):
        for text in _strings(step):
            for match in _STEP_REFERENCE.finditer(text):
                if match.group(1) not in declared:
                    found.append(
                        (match.group(1), str(step.get("id") or step.get("name") or "?"))
                    )
    return found


# ---------------------------------------------------------------------------
# Detector 2 — masked verdict steps
# ---------------------------------------------------------------------------


def masked_verdict_lines(run: str) -> list[str]:
    """Lines that pipe a verdict command into a passthrough without ``pipefail``.

    ``set -o pipefail`` anywhere in the script clears the whole step: it is a
    shell option, so it governs every pipeline in that shell.
    """
    if "pipefail" in run:
        return []
    offending: list[str] = []
    for line in _CONTINUATION.sub(" ", run).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "|" not in stripped:
            continue
        segments = [p.strip() for p in _PIPE.split(stripped)]
        if len(segments) < 2:
            continue
        head = segments[0]
        tail = segments[-1].split()
        if not tail:
            continue
        if tail[0] in _PASSTHROUGH and _VERDICT_COMMAND.search(head):
            offending.append(stripped)
    return offending


def enforced_ids(workflow: dict) -> set[str]:
    return {
        m.group(1)
        for text in _strings(workflow)
        for m in _ENFORCEMENT.finditer(text)
    }


def masked_enforced_steps(path: Path, workflow: dict) -> set[str]:
    """``(workflow, step_id)``-style ids that are both enforced and masked."""
    enforced = enforced_ids(workflow)
    masked: set[str] = set()
    for job in _jobs(workflow).values():
        if not isinstance(job, dict):
            continue
        for step in _steps(job):
            sid = step.get("id")
            run = step.get("run")
            if not isinstance(sid, str) or sid not in enforced:
                continue
            if isinstance(run, str) and masked_verdict_lines(run):
                masked.add(sid)
    return masked


def masked_enforced_inventory() -> dict[tuple[str, str], list[str]]:
    inventory: dict[tuple[str, str], list[str]] = {}
    for path in _tracked_workflow_paths():
        workflow = _load(path)
        for sid in sorted(masked_enforced_steps(path, workflow)):
            inventory[(path.name, sid)] = []
    return inventory


# ---------------------------------------------------------------------------
# Detector 3 — exempt enforcement steps
# ---------------------------------------------------------------------------


def _is_exempt(step: dict, job: dict) -> bool:
    """The step's exit status is discarded, or the step may not run at all.

    ``continue-on-error`` at either level discards the status; a condition that is
    not ``always()`` means the enforcement can be skipped precisely when something
    failed. Both leave an assertion that cannot fail the job.
    """
    if job.get("continue-on-error") or step.get("continue-on-error"):
        return True
    condition = step.get("if")
    if isinstance(condition, str) and condition.strip() and not _ALWAYS.search(condition):
        return True
    return False


def exempt_enforcement_steps(workflow: dict) -> list[str]:
    """Steps that run a ``steps.<id>.outcome`` enforcement but cannot fail the job."""
    offenders: list[str] = []
    for job in _jobs(workflow).values():
        if not isinstance(job, dict):
            continue
        for step in _steps(job):
            run = step.get("run")
            if not isinstance(run, str) or not _ENFORCEMENT.search(run):
                continue
            if _is_exempt(step, job):
                offenders.append(str(step.get("id") or step.get("name") or "?"))
    return offenders


def exempt_enforcement_inventory() -> dict[tuple[str, str], list[str]]:
    inventory: dict[tuple[str, str], list[str]] = {}
    for path in _tracked_workflow_paths():
        for name in exempt_enforcement_steps(_load(path)):
            inventory[(path.name, name)] = []
    return inventory


# ---------------------------------------------------------------------------
# Detector 4 — enforcement steps that run under a shell without `errexit`
# ---------------------------------------------------------------------------


def abortless_enforcement_steps(workflow: dict) -> list[str]:
    """Enforcement steps whose shell will not abort on a failing assertion.

    ``shell:`` on the step wins; otherwise ``defaults.run.shell`` on the job
    applies; otherwise GitHub's ``bash -e {0}``. A step that declares a shell
    without ``-e``/``errexit``, or that clears it with ``set +e``, evaluates all
    of its assertions and still reaches ``exit 0``.
    """
    offenders: list[str] = []
    for job in _jobs(workflow).values():
        if not isinstance(job, dict):
            continue
        job_shell = ((job.get("defaults") or {}).get("run") or {}).get("shell")
        for step in _steps(job):
            run = step.get("run")
            if not isinstance(run, str) or not _ENFORCEMENT.search(run):
                continue
            shell = step.get("shell") or job_shell
            if not _shell_aborts(shell, run):
                offenders.append(str(step.get("id") or step.get("name") or "?"))
    return offenders


def abortless_enforcement_inventory() -> dict[tuple[str, str], list[str]]:
    inventory: dict[tuple[str, str], list[str]] = {}
    for path in _tracked_workflow_paths():
        for name in abortless_enforcement_steps(_load(path)):
            inventory[(path.name, name)] = []
    return inventory


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def _synthetic_workflow(steps: list[dict]) -> dict:
    return {"jobs": {"validate": {"steps": steps}}}


def test_detector_reports_a_phantom_reference():
    # Negative control: the exact pre-repair shape measured on `main` @ `850216fc`
    # — the summary prints `steps.grove.outcome` while no step declares the id.
    workflow = _synthetic_workflow(
        [
            {"name": "Grove contracts", "run": "python -m pytest tests/ -q"},
            {"name": "summary", "run": 'echo "Grove contracts: ${{ steps.grove.outcome }}"'},
        ]
    )
    found = phantom_step_references(workflow["jobs"]["validate"])
    assert found == [("grove", "summary")], found


def test_detector_is_silent_when_the_step_declares_the_id():
    # Positive control: adding `id: grove` resolves the reference.
    workflow = _synthetic_workflow(
        [
            {"name": "Grove contracts", "id": "grove", "run": "python -m pytest tests/ -q"},
            {"name": "summary", "run": 'echo "Grove contracts: ${{ steps.grove.outcome }}"'},
        ]
    )
    assert phantom_step_references(workflow["jobs"]["validate"]) == []


def test_detector_reports_a_masked_verdict_line():
    # Negative control: `pytest | tee log` with no pipefail reports success
    # whatever the tests did.
    run = "python -m pytest tests/ -q 2>&1 | tee cp10-lab.log"
    assert masked_verdict_lines(run) == [run]


def test_detector_is_silent_when_pipefail_is_set():
    run = "set -o pipefail\npython -m pytest tests/ -q 2>&1 | tee cp10-lab.log"
    assert masked_verdict_lines(run) == []


def test_detector_ignores_a_redirection_and_a_non_verdict_pipe():
    # `2>&1` is a redirection, not a pipe; and piping a non-verdict command into
    # tee does not hide a test result.
    assert masked_verdict_lines("python -m pytest tests/ -q 2>&1") == []
    assert masked_verdict_lines("git log --oneline | tee /dev/null") == []
    assert masked_verdict_lines("python -m pytest tests/ -q | grep -v slow") == []


def test_detector_reports_a_masked_verdict_split_across_a_continuation():
    # Negative control: `\` + newline is a line continuation, so the shell runs
    # this as ONE pipeline and `tee` still hides pytest's status. Scanning
    # physical lines found no `|` on the command's first line and reported
    # nothing, so the shape measured on PR #432's `w4_surfaces` step was
    # invisible. Reported as one logical line, with the continuation normalised.
    run = (
        "python -m pytest \\\n"
        "  tests/test_a.py \\\n"
        "  tests/test_b.py \\\n"
        "  -q 2>&1 | tee cp10-w4.log"
    )
    found = masked_verdict_lines(run)
    assert len(found) == 1, found
    assert "| tee cp10-w4.log" in found[0]
    assert "\n" not in found[0]


def test_detector_is_silent_when_a_continuation_carries_pipefail():
    # Positive control for the same shape: pipefail clears it however the
    # command is folded.
    run = "set -o pipefail\npython -m pytest \\\n  tests/test_a.py -q 2>&1 | tee cp10-w4.log"
    assert masked_verdict_lines(run) == []


def test_masked_enforced_requires_both_properties():
    masked_but_unenforced = _synthetic_workflow(
        [{"id": "x", "run": "python -m pytest tests/ -q | tee log"}]
    )
    assert masked_enforced_steps(Path("synthetic.yml"), masked_but_unenforced) == set()

    enforced_but_unmasked = _synthetic_workflow(
        [
            {"id": "x", "run": "python -m pytest tests/ -q | tee log", "continue-on-error": True},
            {"run": "test '${{ steps.x.outcome }}' = success"},
        ]
    )
    assert masked_enforced_steps(Path("synthetic.yml"), enforced_but_unmasked) == {"x"}

    clean = _synthetic_workflow(
        [
            {
                "id": "x",
                "run": "set -o pipefail\npython -m pytest tests/ -q | tee log",
                "continue-on-error": True,
            },
            {"run": "test '${{ steps.x.outcome }}' = success"},
        ]
    )
    assert masked_enforced_steps(Path("synthetic.yml"), clean) == set()


def test_detector_reports_a_continue_on_error_enforcement_step():
    # Negative control: the enforcement runs, but its exit status is discarded, so
    # the assertion cannot fail the job.
    workflow = _synthetic_workflow(
        [
            {"id": "x", "run": "python -m pytest tests/ -q"},
            {"name": "enforce", "run": "test '${{ steps.x.outcome }}' = success", "continue-on-error": True},
        ]
    )
    assert exempt_enforcement_steps(workflow) == ["enforce"]


def test_detector_reports_a_job_level_continue_on_error_enforcement_step():
    # A job-level `continue-on-error` discards every step's status, so an
    # enforcement in that job is decoration however the step itself is written.
    workflow = {
        "jobs": {
            "validate": {
                "continue-on-error": True,
                "steps": [
                    {"id": "x", "run": "python -m pytest tests/ -q"},
                    {"name": "enforce", "run": "test '${{ steps.x.outcome }}' = success"},
                ],
            }
        }
    }
    assert exempt_enforcement_steps(workflow) == ["enforce"]


def test_detector_reports_an_enforcement_guarded_by_a_non_always_condition():
    # `if: success()` skips the enforcement exactly when something failed.
    workflow = _synthetic_workflow(
        [
            {"id": "x", "run": "python -m pytest tests/ -q"},
            {"name": "enforce", "if": "success()", "run": "test '${{ steps.x.outcome }}' = success"},
        ]
    )
    assert exempt_enforcement_steps(workflow) == ["enforce"]


def test_detector_is_silent_on_the_live_enforcement_form():
    # Positive control: `if: always()` is the correct terminal-enforcement form —
    # it runs whatever happened, and its exit status still fails the job. The
    # corpus enforcement step is exactly this shape, so the detector must be
    # silent on it or it would be reporting the live repository.
    workflow = _synthetic_workflow(
        [
            {"id": "x", "run": "python -m pytest tests/ -q", "continue-on-error": True},
            {"name": "enforce", "if": "always()", "run": "test '${{ steps.x.outcome }}' = success"},
        ]
    )
    assert exempt_enforcement_steps(workflow) == []


def test_detector_ignores_a_non_enforcement_step():
    # A soft step that runs no `steps.<id>.outcome` assertion is not an
    # enforcement, so exempting it hides no verdict.
    workflow = _synthetic_workflow(
        [{"id": "x", "run": "python -m pytest tests/ -q", "continue-on-error": True}]
    )
    assert exempt_enforcement_steps(workflow) == []


# --- Detector 4: abortless shell -------------------------------------------

_VERDICT_STEP = {"id": "lab", "run": "test '${{ steps.lab.outcome }}' = success\nexit 0"}


def test_detector_reports_a_step_shell_without_errexit():
    # Negative control: `bash {0}` runs the assertions and reaches `exit 0`
    # however they went, so the step reports success whatever `lab` did.
    workflow = _synthetic_workflow([{**_VERDICT_STEP, "shell": "bash {0}"}])
    assert abortless_enforcement_steps(workflow) == ["lab"]


def test_detector_reports_a_job_default_shell_without_errexit():
    workflow = {
        "jobs": {
            "validate": {
                "defaults": {"run": {"shell": "sh {0}"}},
                "steps": [_VERDICT_STEP],
            }
        }
    }
    assert abortless_enforcement_steps(workflow) == ["lab"]


def test_detector_reports_errexit_cleared_inside_the_script():
    workflow = _synthetic_workflow(
        [{**_VERDICT_STEP, "run": "set +e\n" + _VERDICT_STEP["run"]}]
    )
    assert abortless_enforcement_steps(workflow) == ["lab"]


def test_detector_is_silent_when_the_shell_keeps_errexit():
    # Positive control: an explicit shell that carries `-e` is abortive, and an
    # undeclared shell is GitHub's abortive default.
    for shell in ("bash -e {0}", "bash -eo pipefail {0}", "sh -e {0}", None):
        step = {**_VERDICT_STEP, **({"shell": shell} if shell else {})}
        assert abortless_enforcement_steps(_synthetic_workflow([step])) == []


def test_errexit_detection_does_not_read_a_long_option_as_errexit():
    # A long option merely containing an `e` is not errexit. Measured defect: a
    # character class admitting a second dash scored `bash --noprofile {0}`
    # abortive, so this step — which evaluates every assertion — went unreported.
    for shell in ("bash --noprofile {0}", "bash -x {0}", "bash --norc {0}"):
        step = {**_VERDICT_STEP, "shell": shell}
        assert abortless_enforcement_steps(_synthetic_workflow([step])) == ["lab"], (
            f"{shell!r} was scored abortive, so an abortless enforcement would "
            "go unreported"
        )


def test_detector_is_silent_on_a_non_enforcement_step_with_a_loose_shell():
    # A soft step under a non-abortive shell runs no verdict assertion, so it
    # hides nothing; the detector must not report it.
    workflow = _synthetic_workflow(
        [{"id": "x", "run": "python -m pytest tests/ -q", "shell": "bash {0}"}]
    )
    assert abortless_enforcement_steps(workflow) == []


# ---------------------------------------------------------------------------
# The invariants, over the live tracked workflow corpus
# ---------------------------------------------------------------------------


def test_no_workflow_references_an_undeclared_step_id():
    """Every ``steps.<id>`` reference must resolve inside its own job."""
    offenders: list[str] = []
    for path in _tracked_workflow_paths():
        for job_name, job in _jobs(_load(path)).items():
            if not isinstance(job, dict):
                continue
            for referenced, where in phantom_step_references(job):
                offenders.append(f"{path.name} [{job_name}] step '{where}' -> steps.{referenced}")
    assert not offenders, (
        "step references that no step in the same job declares; GitHub "
        "substitutes the empty string, so the assertion is vacuous:\n"
        + "\n".join(offenders)
    )


def test_masked_enforced_steps_are_the_registered_set():
    """A newly masked enforced verdict step fails here rather than shipping."""
    measured = set(masked_enforced_inventory())
    unregistered = measured - REGISTERED_MASKED_VERDICT_STEPS
    assert not unregistered, (
        "enforced verdict steps that destroy their own exit status and are not "
        f"recorded: {sorted(unregistered)}. Add `set -o pipefail`, or record the "
        "step in REGISTERED_MASKED_VERDICT_STEPS with the measured reason."
    )


def test_registered_masked_steps_are_still_masked():
    """The registry is an inventory, not a filter — a repaired entry is stale."""
    measured = set(masked_enforced_inventory())
    stale = REGISTERED_MASKED_VERDICT_STEPS - measured
    assert not stale, (
        f"recorded masked verdict steps that are no longer masked: {sorted(stale)}. "
        "Remove them from REGISTERED_MASKED_VERDICT_STEPS so the inventory keeps "
        "describing the repository."
    )


@pytest.mark.parametrize("entry", sorted(REGISTERED_MASKED_VERDICT_STEPS))
def test_registered_masked_steps_are_still_enforced(entry: tuple[str, str]):
    """A recorded entry that nothing asserts on is not a verdict step at all."""
    name, sid = entry
    enforced = enforced_ids(_load(WORKFLOWS / name))
    assert sid in enforced, (
        f"{name}: recorded masked verdict step '{sid}' is named by no "
        "`steps.<id>.outcome` enforcement; the entry no longer describes a "
        "verdict step"
    )


def test_enforcement_steps_are_not_exempt_from_failing():
    """Every enforcement step must be able to fail the job it runs in.

    An enforcement carrying `continue-on-error` at either level, or guarded by a
    condition other than `always()`, is decoration: its assertion runs (or is
    skipped) while its exit status cannot fail the job.
    """
    measured = set(exempt_enforcement_inventory())
    unregistered = measured - REGISTERED_EXEMPT_ENFORCEMENT_STEPS
    assert not unregistered, (
        "enforcement steps whose exit status is discarded, so their assertions "
        f"cannot fail the job: {sorted(unregistered)}. Remove the "
        "`continue-on-error`, or use `if: always()` so the enforcement runs on "
        "failure and its exit status fails the job. If the exemption is "
        "deliberate, record it in REGISTERED_EXEMPT_ENFORCEMENT_STEPS with the "
        "measured reason."
    )


def test_registered_exempt_enforcement_steps_are_still_exempt():
    """The registry is an inventory, not a filter — a repaired entry is stale."""
    measured = set(exempt_enforcement_inventory())
    stale = REGISTERED_EXEMPT_ENFORCEMENT_STEPS - measured
    assert not stale, (
        f"recorded exempt enforcement steps that are no longer exempt: {sorted(stale)}. "
        "Remove them from REGISTERED_EXEMPT_ENFORCEMENT_STEPS so the inventory "
        "keeps describing the repository."
    )


def test_the_corpus_enforcement_step_is_reported_when_exempted():
    """Live negative control: exempting the real enforcement step must redden this.

    The detector is exercised against the *live* `sg-02-fe-2-v.yml`, not a
    synthetic fixture, so a rewrite of the file is judged by the file. The
    enforcement step is mutated in memory only — the tree is not touched.
    """
    name = "sg-02-fe-2-v.yml"
    workflow = _load(WORKFLOWS / name)
    assert exempt_enforcement_steps(workflow) == [], (
        "the live corpus enforcement step is already exempt; the negative "
        "control below cannot distinguish a detector defect from a live defect"
    )
    for job in _jobs(workflow).values():
        if not isinstance(job, dict):
            continue
        for step in _steps(job):
            run = step.get("run")
            if isinstance(run, str) and _ENFORCEMENT.search(run):
                step["continue-on-error"] = True
    assert exempt_enforcement_steps(workflow), (
        "exempting the live enforcement step was not reported — the detector is "
        "disarmed"
    )


def test_abortless_enforcement_steps_are_the_registered_set():
    """A newly abortless enforcement fails here rather than shipping."""
    measured = set(abortless_enforcement_inventory())
    unregistered = measured - REGISTERED_ABORTLESS_ENFORCEMENT_STEPS
    assert not unregistered, (
        "enforcement steps whose shell does not abort on a failing assertion, so "
        f"every assertion is evaluated and `exit 0` is always reached: "
        f"{sorted(unregistered)}. Remove the `shell:` override (GitHub's default "
        "`bash -e {0}` is abortive), or use a shell carrying `-e`, or drop the "
        "`set +e`. If the shell is deliberate, record it in "
        "REGISTERED_ABORTLESS_ENFORCEMENT_STEPS with the measured reason."
    )


def test_registered_abortless_steps_are_still_abortless():
    """The registry is an inventory, not a filter — a repaired entry is stale."""
    measured = set(abortless_enforcement_inventory())
    stale = REGISTERED_ABORTLESS_ENFORCEMENT_STEPS - measured
    assert not stale, (
        f"recorded abortless enforcement steps that are no longer abortless: "
        f"{sorted(stale)}. Remove them from "
        "REGISTERED_ABORTLESS_ENFORCEMENT_STEPS so the inventory keeps describing "
        "the repository."
    )


def test_the_corpus_enforcement_step_is_reported_when_its_shell_is_loosened():
    """Live negative control: an abortless shell on the real step must redden this.

    Exercised against the *live* `sg-02-fe-2-v.yml` rather than a synthetic
    fixture, so a rewrite of that file is judged by the file. The shell is
    loosened in memory only — the tree is not touched.
    """
    name = "sg-02-fe-2-v.yml"
    workflow = _load(WORKFLOWS / name)
    assert abortless_enforcement_steps(workflow) == [], (
        "the live corpus enforcement step is already abortless; the negative "
        "control below cannot distinguish a detector defect from a live defect"
    )
    for job in _jobs(workflow).values():
        if not isinstance(job, dict):
            continue
        for step in _steps(job):
            run = step.get("run")
            if isinstance(run, str) and _ENFORCEMENT.search(run):
                step["shell"] = "bash {0}"
    assert abortless_enforcement_steps(workflow), (
        "loosening the live enforcement step's shell was not reported — the "
        "detector is disarmed"
    )
