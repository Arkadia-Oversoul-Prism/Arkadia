"""Workstream 4 — the trace surface renders session-level linkage *by identity*.

``tests/test_prism_w4_run_evidence_trace.py`` measures the ledger's behaviour and
``tests/test_lab_run_trace_contract.py`` measures its read-only ceiling. Neither
covers the property this file exists to hold:

    every session-level classification the ledger computes is *visible*, and
    visible by the identity of the record it classified.

The ledger reports those classifications as a count inside ``ledger.unresolved``
("3 evidence record(s) name a run not in this view"). A count tells a reader that
something failed to resolve; it never says *which* record. That matters most for
the duplicate classifications, where the ledger **drops** the repeated record from
the traced set: the identity is the only route back to the record the surface
left out, so a count-only rendering hides it completely.

The invariant is derived from the ledger's own ``RunTraceLedger`` interface rather
than restated here, so a classification added to the ledger is judged by the same
rule. A hand-copied list drifts, and a drifted list makes the assertion vacuous.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
TRACE_TS = LAB / "labRunTrace.ts"
TRACE_TSX = LAB / "LabRunTrace.tsx"

# Classifications that describe the *session-level* linkage, i.e. records the
# ledger removed from a run's traced set (or never attributed to one). Each one
# carries the record's own id, so each one is renderable by identity.
IDENTITY_FIELDS = (
    "unlinked_events",
    "unlinked_evidence",
    "unattributed_evidence",
    "unlinked_artifacts",
    "unattributed_artifacts",
    "duplicate_evidence_ids",
    "duplicate_artifact_ids",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ledger_interface(source: str) -> str:
    """The body of ``export interface RunTraceLedger``."""
    match = re.search(
        r"export interface RunTraceLedger\s*\{(.*?)\n\}", source, re.DOTALL
    )
    assert match, "labRunTrace.ts declares no RunTraceLedger interface"
    return match.group(1)


def identity_fields(source: str) -> set[str]:
    """Every session-level classification the ledger declares, read from source.

    A classification is a ledger field whose name marks records removed from a
    run's traced set. Derived rather than restated: the live assertion and the
    negative controls below exercise this same function.
    """
    body = ledger_interface(source)
    declared = set(re.findall(r"^\s{2}([a-z_]+)\s*:", body, re.MULTILINE))
    return {
        name
        for name in declared
        if name.startswith(("unlinked_", "unattributed_", "duplicate_"))
    }


def render_body(source: str) -> str:
    """The JSX returned by ``export function LabRunTrace``.

    Scoped deliberately: a ledger field *mentioned* in the linkage array is not
    the same as one *rendered*. Measured on the real component, removing the
    render block left every ``ledger.<field>`` read intact — the array is built
    and then dropped — so an unscoped check passed while the surface showed
    nothing. The render tokens must live inside the returned JSX.
    """
    if "export function LabRunTrace(" not in source:
        return ""
    body = source[source.index("export function LabRunTrace(") :]
    if "return (" not in body:
        return ""
    return body[body.index("return (") :]


def rendered_identity_fields(source: str) -> set[str]:
    """Ledger classifications the component reads *and actually renders*.

    Both conditions are required: the ids must reach the DOM (``ids.join``), and
    the list that carries them must be consumed inside the returned JSX.
    """
    body = render_body(source)
    rendered = bool(
        re.search(r"\{linkage\.map\(", body)
        and re.search(r"ids=\{group\.ids\}", body)
        and re.search(r"ids\.join\(", source)
    )
    if not rendered:
        return set()
    return {name for name in IDENTITY_FIELDS if re.search(rf"ledger\.{name}\b", source)}


def renders_an_empty_group(source: str) -> bool:
    """True if a group with no ids would still produce a visible row."""
    return "if (ids.length === 0) return null;" not in source


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------


def test_every_session_level_classification_is_rendered_by_identity():
    """A classification the ledger computes must be reachable by the record's id.

    A count-only rendering is the defect: it says a reference failed to resolve
    without naming it, and for a duplicate it names nothing at all — the record
    it classified was dropped from the traced set.
    """
    derived = identity_fields(_read(TRACE_TS))
    assert derived, "control premise: the ledger must declare linkage classifications"
    assert derived == set(IDENTITY_FIELDS), (
        "the ledger's linkage vocabulary moved; update IDENTITY_FIELDS deliberately: "
        f"new={derived - set(IDENTITY_FIELDS)} gone={set(IDENTITY_FIELDS) - derived}"
    )

    rendered = rendered_identity_fields(_read(TRACE_TSX))
    missing = derived - rendered
    assert not missing, (
        "the trace surface computes these linkage classifications but never shows "
        f"which record each one names: {sorted(missing)}"
    )


def test_identities_are_read_from_the_ledger_not_invented():
    """Each group must take its ids from the ledger field, so the surface cannot
    display an id the substrate never classified.

    ``unlinked_*`` / ``unattributed_*`` hold records, so they are projected with
    ``.map()``; ``duplicate_*_ids`` is already a list of ids and is read directly.
    """
    source = _read(TRACE_TSX)
    for field in IDENTITY_FIELDS:
        record_fields = not field.endswith("_ids")
        pattern = rf"ledger\.{field}\.map\(" if record_fields else rf"ledger\.{field}\b(?!\.map)"
        assert re.search(pattern, source), (
            f"'{field}' is not projected from the ledger into an id list"
        )


def test_an_empty_classification_renders_nothing():
    """A clean view must not grow an empty linkage row per classification."""
    source = _read(TRACE_TSX)
    assert not renders_an_empty_group(source), (
        "a linkage group renders even when it classified no record"
    )


def test_the_linkage_block_is_reachable_only_when_something_was_classified():
    """The container itself is gated, so a clean view keeps the previous shape."""
    source = _read(TRACE_TSX)
    assert re.search(r"\{linkage\.length > 0 && \(", source), (
        "the linkage container is not gated on having something to show"
    )
    assert re.search(r"\.filter\(\(group\) => group\.ids\.length > 0\)", source), (
        "empty groups are not filtered out of the linkage list"
    )


def test_the_surface_still_issues_no_request_of_its_own():
    """The added rendering must not introduce a second reader of the contract."""
    source = _read(TRACE_TSX)
    assert not re.search(r"\b(fetch|apiRequest|useHydration)\s*[(<]", source), (
        "the trace surface now performs its own network read"
    )


# ---------------------------------------------------------------------------
# Negative controls — each detector fires on the defect it exists to catch
# ---------------------------------------------------------------------------


def test_negative_control_detector_flags_a_count_only_rendering():
    """The pre-repair shape: the ledger classifies, the surface only totals.

    This is the exact form ``main`` carried before this slice, so the control
    proves the live assertion would have failed rather than passing vacuously.
    """
    count_only = """
export function LabRunTrace({ view }: { view: LabTraceSource }) {
  const ledger = buildRunTrace(view);
  return (
    <Panel>
      <p data-testid="lab-trace-unresolved">{ledger.unresolved.join(" ")}</p>
    </Panel>
  );
}
"""
    assert rendered_identity_fields(count_only) == set()
    assert identity_fields(_read(TRACE_TS)) - rendered_identity_fields(count_only)


def test_negative_control_detector_flags_a_built_but_unrendered_list():
    """The hole the first cut of this guard had, measured on the real component.

    The ledger reads are all present and the linkage array is constructed — but
    the block that renders it was removed, so nothing reaches the DOM. A detector
    that only looks for ``ledger.<field>`` passes here; this one must not.
    """
    built_then_dropped = """
export function LabRunTrace({ view }: { view: LabTraceSource }) {
  const ledger = buildRunTrace(view);
  const linkage = [
    { kind: "unlinked-evidence", ids: ledger.unlinked_evidence.map((r) => r.evidence_id) },
  ].filter((group) => group.ids.length > 0);
  return (
    <Panel>
      <p data-testid="lab-trace-unresolved">{ledger.unresolved.join(" ")}</p>
    </Panel>
  );
}
"""
    # Every field is read...
    assert re.search(r"ledger\.unlinked_evidence\b", built_then_dropped)
    # ...but none is rendered.
    assert rendered_identity_fields(built_then_dropped) == set()


def test_negative_control_detector_flags_an_invented_identity_list():
    """A group whose ids are a literal is not reading the ledger."""
    invented = """
export function LabRunTrace({ view }: { view: LabTraceSource }) {
  const linkage = [{ kind: "unlinked-evidence", ids: ["EVD-1"] }].filter((g) => g.ids.length > 0);
  return (
    <Panel>
      <ul>{linkage.map((group) => <li key={group.kind}>{group.ids.join(", ")}</li>)}</ul>
    </Panel>
  );
}
"""
    assert re.search(r"ledger\.unlinked_evidence\b", invented) is None
    assert rendered_identity_fields(invented) == set()


def test_negative_control_detector_flags_ids_that_never_reach_the_dom():
    """A group rendered without its ids shows a count, not the record."""
    count_only_row = """
export function LabRunTrace({ view }: { view: LabTraceSource }) {
  const ledger = buildRunTrace(view);
  const linkage = [{ kind: "unlinked-evidence", ids: ledger.unlinked_evidence.map((r) => r.evidence_id) }];
  return (
    <Panel>
      <ul>{linkage.map((group) => <li key={group.kind}>{group.ids.length}</li>)}</ul>
    </Panel>
  );
}
"""
    assert rendered_identity_fields(count_only_row) == set()


def test_negative_control_detector_flags_an_ungated_empty_group():
    """An empty group that still renders is the defect the guard must see."""
    ungated = """
      function LinkageGroup({ ids }) {
        return <li data-testid="lab-trace-linkage">{ids.length}</li>;
      }
    """
    assert renders_an_empty_group(ungated)


def test_negative_control_the_field_derivation_sees_a_new_classification():
    """A classification added to the interface enters the judged domain."""
    synthetic = """
export interface RunTraceLedger {
  runs: RunTrace[];
  unlinked_events: LabWorkEvent[];
  orphaned_runs: LabRunRecord[];
  acceptance: AcceptanceReading;
}
"""
    assert identity_fields(synthetic) == {"unlinked_events"}
    with_new_field = synthetic.replace(
        "  acceptance: AcceptanceReading;",
        "  unlinked_widgets: W[];\n  acceptance: AcceptanceReading;",
    )
    assert identity_fields(with_new_field) == {"unlinked_events", "unlinked_widgets"}
    # ...and the added field is judged: the surface does not render it.
    assert identity_fields(with_new_field) - rendered_identity_fields(_read(TRACE_TSX))
