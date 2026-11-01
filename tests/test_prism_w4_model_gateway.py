"""Workstream 4 — model gateway read projection (handler oracle + execution).

The gateway surface (`components/lab/LabModelGateway.tsx` + `labGateway.ts`) is a
pure projection of `GET /api/lab/engineering/gateway`
(`lab.engineering_lab.gateway.describe_gateway` → `ModelGateway.to_dict()`).

Two things make that claim real, and both are measured here rather than asserted:

1. **The shape is the handler's own.** ``describe_gateway()`` is invoked directly
   and its output is what the projection is given, so the fields read
   (`provider`, `model`, `config_class`, `configured`, `status`, `detail`,
   `cost_note`, and the three provider groups) are the handler's keys — not
   inferred from an interface.

2. **The projection behaves as claimed.** ``labGateway.ts`` is pure and
   dependency-free, so it is *executed* (not read) under Node and given the real
   handler output. The reading "model work is blocked" is therefore an observed
   output.

The non-collapses under test are the gateway's own doctrine: a configured key is
not a reachable provider, an AVAILABLE status is not an authorization, a LOCAL
class is not free, and an agent runtime is described without ever being probed.

Node executes the module directly; if Node is unavailable the projection tests
skip with a stated reason rather than silently passing. Negative controls prove
each detector fires on the defect it exists to catch.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PROJECTION = LAB_SRC / "labGateway.ts"


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(view: dict) -> dict:
    """Execute the real ``labGateway.ts`` over *view* and return the ledger."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const view = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify({\n"
        "  ledger: m.buildGatewayLedger(view),\n"
        "  verdict: m.gatewayVerdict(m.buildGatewayLedger(view)),\n"
        "}));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(view)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


# ---------------------------------------------------------------------------
# The shape is the handler's own
# ---------------------------------------------------------------------------


def test_handler_output_carries_the_keys_the_projection_reads():
    """Every field the projection reads must be a key the handler emits.

    A rename on either side would make the surface silently report zero
    configured providers rather than fail, so the keys are measured, not assumed.
    """
    from lab.engineering_lab.gateway import describe_gateway

    view = describe_gateway()
    assert set(view) >= {"local_providers", "remote_providers", "agent_providers", "catalog"}
    assert view["catalog"], "control premise: the handler must describe providers"

    required = {"provider", "model", "config_class", "configured", "status", "detail", "cost_note"}
    for entry in view["catalog"]:
        assert required <= set(entry), f"catalog entry missing {required - set(entry)}"


def test_handler_output_carries_the_dispatch_truth_the_projection_reads():
    """`adapter_bound`/`dispatchable` must be the handler's own keys.

    The projection reads dispatchability from the handler rather than inferring it
    from `status`, so these keys are load-bearing: if the handler renamed one, the
    surface would silently report every provider as non-dispatchable rather than
    fail. Measured against the handler, not an interface.
    """
    from lab.engineering_lab.gateway import describe_gateway

    view = describe_gateway()
    assert view["catalog"], "control premise: the handler must describe providers"
    for entry in view["catalog"]:
        assert {"adapter_bound", "dispatchable"} <= set(entry), f"catalog entry missing {set(entry)}"
        assert isinstance(entry["adapter_bound"], bool)
        assert isinstance(entry["dispatchable"], bool)
        # The handler's own P0.5 rule: a dispatch needs a bound adapter, so
        # dispatchable can never be true without one.
        if entry["dispatchable"]:
            assert entry["adapter_bound"] is True


def test_the_three_groups_partition_the_catalog():
    """The handler's groups must cover its own catalog exactly.

    If a config class were added without a group, a naive group-by would drop the
    provider from the surface entirely — the projection reports it as ungrouped,
    and this asserts the premise that none is ungrouped today.
    """
    from lab.engineering_lab.gateway import describe_gateway

    view = describe_gateway()
    declared = set(view["local_providers"]) | set(view["remote_providers"]) | set(view["agent_providers"])
    described = {entry["provider"] for entry in view["catalog"]}
    assert declared == described, f"group/catalog disagreement: {declared ^ described}"

    ledger = run_projection(view)["ledger"]
    assert ledger["ungrouped_providers"] == []
    assert ledger["duplicate_providers"] == []
    assert ledger["unknown_config_class"] == []


def test_config_class_vocabulary_is_the_gateway_s_own():
    """The projection's class list must be drawn from the handler's classes.

    The handler's ``CONFIG_CLASSES`` is a provider→class *mapping*, so the class
    vocabulary is its values. A console-invented class would let the surface
    label a provider with a grouping the gateway does not have.
    """
    from lab.engineering_lab.gateway import CONFIG_CLASSES

    declared_classes = set(CONFIG_CLASSES.values())
    assert declared_classes == {"LOCAL", "REMOTE", "AGENT_RUNTIME"}

    source = PROJECTION.read_text(encoding="utf-8")
    match = re.search(r"CONFIG_CLASSES:\s*readonly string\[\]\s*=\s*\[(.*?)\]", source, re.DOTALL)
    assert match, "the projection declares no CONFIG_CLASSES list"
    projected = set(re.findall(r'"([A-Z_]+)"', match.group(1)))
    assert projected == declared_classes, f"class vocabulary drift: {projected ^ declared_classes}"


def test_negative_control_class_detector_sees_a_divergent_value():
    """The class detector must report a class the gateway does not declare."""
    from lab.engineering_lab.gateway import CONFIG_CLASSES

    declared_classes = set(CONFIG_CLASSES.values())
    assert "HYBRID" not in declared_classes
    assert {"HYBRID"} - declared_classes == {"HYBRID"}


# ---------------------------------------------------------------------------
# The projection is executed over the real handler output
# ---------------------------------------------------------------------------


def test_projection_reads_the_real_handler_output():
    from lab.engineering_lab.gateway import describe_gateway

    view = describe_gateway()
    result = run_projection(view)
    ledger, verdict = result["ledger"], result["verdict"]

    assert ledger["counts"]["catalog"] == len(view["catalog"])
    assert ledger["counts"]["local"] == len(view["local_providers"])
    assert ledger["counts"]["remote"] == len(view["remote_providers"])
    assert ledger["counts"]["agent_runtime"] == len(view["agent_providers"])
    assert sum(len(g["declared"]) for g in ledger["groups"]) == ledger["counts"]["catalog"]
    assert verdict["state"] in {"NO_CATALOG", "MODEL_WORK_BLOCKED", "PROVIDER_AVAILABLE"}


def test_availability_is_never_inferred_and_never_granted():
    """The gateway holds no authority, and the projection must not confer any.

    ``authority_granted`` is a literal ``false``: availability is a configuration
    fact, and no reading of this surface may be presented as permission to run.
    """
    from lab.engineering_lab.gateway import describe_gateway

    ledger = run_projection(describe_gateway())["ledger"]
    assert ledger["authority_granted"] is False
    assert ledger["usable_provider_present"] == (ledger["counts"]["available"] > 0)


def test_cost_is_not_asserted_so_no_class_reads_as_free():
    """A LOCAL class must not be presented as free.

    The handler's ``cost_note`` explicitly asserts nothing ("cost not asserted;
    provider tiers are not assumed free"). The projection surfaces that fact
    instead of letting locality imply zero cost.
    """
    from lab.engineering_lab.gateway import describe_gateway

    view = describe_gateway()
    ledger = run_projection(view)["ledger"]
    assert ledger["cost_asserted"] is False
    for entry in view["catalog"]:
        assert "not asserted" in entry["cost_note"].lower()


def test_agent_runtimes_are_described_without_being_probed():
    """An agent runtime is never probed, so its status must not read as available.

    The handler returns ``UNCONFIGURED`` for every agent runtime regardless of
    environment, precisely because probing one would be a claim it cannot make.
    """
    from lab.engineering_lab.gateway import AGENT_PROVIDERS, describe_gateway

    view = describe_gateway()
    ledger = run_projection(view)["ledger"]

    for entry in view["catalog"]:
        if entry["config_class"] == "AGENT_RUNTIME":
            assert entry["status"] != "AVAILABLE"
            assert entry["configured"] is False
    assert ledger["agent_runtime_reported_available"] == []
    assert set(ledger["groups"][2]["declared"]) == set(AGENT_PROVIDERS)


# ---------------------------------------------------------------------------
# Missing / partial readings, with negative controls
# ---------------------------------------------------------------------------


def test_negative_control_a_configured_key_without_reachability_is_not_available():
    """The detector must separate 'configured' from 'AVAILABLE'.

    This is the gateway's own doctrine: ``configured`` records that an env var is
    present, ``status`` records the probe result. A surface that collapsed them
    would show a configured key as a usable provider.
    """
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "ollama",
                "model": "llama3",
                "config_class": "LOCAL",
                "configured": True,
                "status": "UNAVAILABLE",
                "detail": "unreachable",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            }
        ],
    }
    result = run_projection(view)
    ledger, verdict = result["ledger"], result["verdict"]

    assert ledger["counts"]["configured"] == 1
    assert ledger["counts"]["available"] == 0
    assert ledger["usable_provider_present"] is False
    assert [e["provider"] for e in ledger["configured_but_not_available"]] == ["ollama"]
    assert verdict["state"] == "MODEL_WORK_BLOCKED"


def test_negative_control_a_provider_in_no_group_is_reported_not_dropped():
    """A catalog provider outside every declared group must be surfaced.

    A naive group-by would omit it and the surface would silently under-report
    the catalog.
    """
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "ollama",
                "model": "llama3",
                "config_class": "LOCAL",
                "configured": False,
                "status": "UNCONFIGURED",
                "detail": "",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            },
            {
                "provider": "ghost",
                "model": "x",
                "config_class": "LOCAL",
                "configured": False,
                "status": "UNCONFIGURED",
                "detail": "",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            },
        ],
    }
    ledger = run_projection(view)["ledger"]
    assert [e["provider"] for e in ledger["ungrouped_providers"]] == ["ghost"]
    assert ledger["counts"]["catalog"] == 2


def test_negative_control_a_declared_group_name_missing_from_the_catalog():
    """A group that names a provider the catalog does not describe is a partial
    link, and must be reported rather than rendered as a described provider."""
    view = {
        "local_providers": ["ollama", "vanished"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "ollama",
                "model": "llama3",
                "config_class": "LOCAL",
                "configured": False,
                "status": "UNCONFIGURED",
                "detail": "",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            }
        ],
    }
    ledger = run_projection(view)["ledger"]
    (group,) = [g for g in ledger["groups"] if g["group"] == "local_providers"]
    assert group["missing_from_catalog"] == ["vanished"]
    assert [e["provider"] for e in group["entries"]] == ["ollama"]


def test_negative_control_a_duplicate_provider_is_reported():
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "ollama",
                "model": "llama3",
                "config_class": "LOCAL",
                "configured": False,
                "status": "UNCONFIGURED",
                "detail": "",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            },
            {
                "provider": "ollama",
                "model": "llama3:70b",
                "config_class": "LOCAL",
                "configured": True,
                "status": "AVAILABLE",
                "detail": "reachable",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            },
        ],
    }
    result = run_projection(view)
    ledger, verdict = result["ledger"], result["verdict"]
    assert ledger["duplicate_providers"] == ["ollama"]
    # The group reading takes the first description; the duplicate stays visible.
    assert ledger["counts"]["catalog"] == 2
    assert verdict["state"] == "PROVIDER_AVAILABLE"


def test_negative_control_a_group_class_mismatch_is_reported():
    """A provider declared under one group but classified as another must show.

    `local_providers` and `config_class == "REMOTE"` cannot both be true; a
    surface that trusted the group list alone would label it local.
    """
    view = {
        "local_providers": ["gemini"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "gemini",
                "model": "gemini-1.5-flash",
                "config_class": "REMOTE",
                "configured": False,
                "status": "UNCONFIGURED",
                "detail": "",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            }
        ],
    }
    ledger = run_projection(view)["ledger"]
    (group,) = [g for g in ledger["groups"] if g["group"] == "local_providers"]
    assert [e["provider"] for e in group["group_class_mismatch"]] == ["gemini"]
    assert [e["provider"] for e in group["entries"]] == ["gemini"]
    assert ledger["counts"]["local"] == 0
    assert ledger["counts"]["remote"] == 1


def test_negative_control_an_unknown_config_class_is_reported():
    view = {
        "local_providers": [],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "mystery",
                "model": "x",
                "config_class": "SOMEWHERE_ELSE",
                "configured": False,
                "status": "UNCONFIGURED",
                "detail": "",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            }
        ],
    }
    ledger = run_projection(view)["ledger"]
    assert [e["provider"] for e in ledger["unknown_config_class"]] == ["mystery"]
    assert [e["provider"] for e in ledger["ungrouped_providers"]] == ["mystery"]


def test_negative_control_an_empty_catalog_is_not_availability():
    """No catalog is an empty reading, not an available model."""
    result = run_projection({"local_providers": [], "remote_providers": [], "agent_providers": [], "catalog": []})
    assert result["verdict"]["state"] == "NO_CATALOG"
    assert result["ledger"]["usable_provider_present"] is False


def test_negative_control_an_available_provider_is_not_an_authorization():
    """The strongest positive reading still confers no authority."""
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            {
                "provider": "ollama",
                "model": "llama3",
                "config_class": "LOCAL",
                "configured": True,
                "status": "AVAILABLE",
                "detail": "reachable via /api/tags",
                "cost_note": "cost not asserted; provider tiers are not assumed free",
            }
        ],
    }
    result = run_projection(view)
    assert result["verdict"]["state"] == "PROVIDER_AVAILABLE"
    assert result["ledger"]["authority_granted"] is False
    assert "not an authorization" in result["verdict"]["note"]


# ---------------------------------------------------------------------------
# Availability is not dispatchability (the handler's P0.5 rule)
# ---------------------------------------------------------------------------


def _descriptor(**overrides) -> dict:
    entry = {
        "provider": "ollama",
        "model": "llama3",
        "config_class": "LOCAL",
        "configured": True,
        "status": "AVAILABLE",
        "detail": "reachable via /api/tags",
        "cost_note": "cost not asserted; provider tiers are not assumed free",
        "adapter_bound": True,
        "dispatchable": True,
    }
    entry.update(overrides)
    return entry


def test_negative_control_an_available_provider_without_a_bound_adapter_is_not_dispatchable():
    """The detector must separate 'AVAILABLE' from 'dispatchable'.

    This is the handler's own P0.5 truthfulness rule: `status` answers "is this
    configured and reachable?", while `dispatchable` answers the different question
    "could a run actually call it right now?" — which additionally needs a bound
    adapter. A projection that read only `status` would present a reachable
    provider as a functioning worker, implying a dispatch that would fail.
    """
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [_descriptor(adapter_bound=False, dispatchable=False)],
    }
    result = run_projection(view)
    ledger, verdict = result["ledger"], result["verdict"]

    assert ledger["counts"]["available"] == 1
    assert ledger["counts"]["dispatchable"] == 0
    assert ledger["dispatchable_provider_present"] is False
    assert [e["provider"] for e in ledger["available_but_not_dispatchable"]] == ["ollama"]
    # Availability is still reported; the surface must not hide the reading, it
    # must refuse to call it dispatchable.
    assert ledger["usable_provider_present"] is True
    assert "none is dispatchable" in verdict["note"]
    assert "not an authorization" in verdict["note"]


def test_a_dispatchable_provider_reads_as_dispatchable():
    """Positive control: the detector must fire in the other direction too.

    Without this, a projection that always reported 'not dispatchable' would pass
    the negative control above.
    """
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [_descriptor()],
    }
    ledger = run_projection(view)["ledger"]
    assert ledger["counts"]["dispatchable"] == 1
    assert ledger["dispatchable_provider_present"] is True
    assert ledger["available_but_not_dispatchable"] == []


def test_dispatchability_is_read_from_the_handler_never_inferred_from_status():
    """A provider the handler marks non-dispatchable must not be promoted.

    `status == AVAILABLE` with `dispatchable == False` is the exact state the
    handler can emit; inferring dispatchability from status would erase it. The
    inverse is also checked, so the field is read rather than assumed false.
    """
    view = {
        "local_providers": ["ollama", "llama_cpp"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [
            _descriptor(provider="ollama", adapter_bound=False, dispatchable=False),
            _descriptor(provider="llama_cpp", adapter_bound=True, dispatchable=True),
        ],
    }
    ledger = run_projection(view)["ledger"]
    assert ledger["counts"]["available"] == 2
    assert ledger["counts"]["dispatchable"] == 1
    assert [e["provider"] for e in ledger["available_but_not_dispatchable"]] == ["ollama"]


def test_negative_control_the_dispatch_detector_sees_an_inferred_value():
    """The detector must fire on a projection that inferred dispatchability.

    Feeding a view whose only dispatchable provider is described *without* the
    handler's `dispatchable` key must not read as dispatchable — that is what
    inference from `status` would produce.
    """
    entry = _descriptor()
    del entry["dispatchable"]
    del entry["adapter_bound"]
    view = {
        "local_providers": ["ollama"],
        "remote_providers": [],
        "agent_providers": [],
        "catalog": [entry],
    }
    ledger = run_projection(view)["ledger"]
    assert ledger["counts"]["available"] == 1
    assert ledger["counts"]["dispatchable"] == 0
    assert ledger["dispatchable_provider_present"] is False


def test_the_real_handler_reports_no_dispatchable_provider_here():
    """Over the live handler output, dispatchability is measured, not assumed.

    In a bare environment every provider is unconfigured, so the strongest honest
    reading is MODEL_WORK_BLOCKED with zero dispatchable providers. The assertion
    is relational (dispatchable <= available), so it stays true in an environment
    that does have a configured provider.
    """
    from lab.engineering_lab.gateway import describe_gateway

    ledger = run_projection(describe_gateway())["ledger"]
    assert ledger["counts"]["dispatchable"] <= ledger["counts"]["available"]
    assert ledger["dispatchable_provider_present"] == (ledger["counts"]["dispatchable"] > 0)
    assert len(ledger["available_but_not_dispatchable"]) == (
        ledger["counts"]["available"] - ledger["counts"]["dispatchable"]
    )



def test_gateway_boolean_fact_preserves_unknown():
    """Execute the real projection helper for true, false, absent and malformed values."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\\n"
        "process.stdout.write(JSON.stringify([\\n"
        "  m.gatewayBooleanFact(true),\\n"
        "  m.gatewayBooleanFact(false),\\n"
        "  m.gatewayBooleanFact(undefined),\\n"
        "  m.gatewayBooleanFact(null),\\n"
        "  m.gatewayBooleanFact('false'),\\n"
        "]));\\n"
    )
    completed = subprocess.run([node, "--input-type=module", "-e", program], capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        pytest.fail(f"gateway boolean projection execution failed: {completed.stderr.strip()[:800]}")
    assert json.loads(completed.stdout) == ["yes", "no", "unknown", "unknown", "unknown"]
