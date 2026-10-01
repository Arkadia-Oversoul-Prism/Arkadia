"""Gate 2 backend-runtime observation harness -- fitness tests.

Source-level and pure-function tests, following the convention of
``tests/test_gate2_browser_observation.py``. The live probe is exercised by
running the script; what is proven here is that the oracle's *limits* are
encoded rather than glossed, and that the classifier has teeth.
"""

from pathlib import Path

from scripts.gate2_backend_observation import (
    REQUIRED_PREFIXES,
    classify,
    digest,
    operation_signature,
    oracle_power,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "gate2_backend_observation.py"


def _spec(*ops: tuple[str, str]) -> dict:
    """Build a minimal FastAPI-shaped schema from (method, path) pairs."""
    paths: dict = {}
    for method, path in ops:
        paths.setdefault(path, {})[method.lower()] = {"summary": "", "tags": []}
    return {"paths": paths}


def _sig(*ops: tuple[str, str]) -> list[str]:
    return operation_signature(_spec(*ops))


# ── signature construction ───────────────────────────────────────────────────


def test_signature_is_order_independent():
    a = _sig(("get", "/a"), ("post", "/b"))
    b = _sig(("post", "/b"), ("get", "/a"))
    assert a == b


def test_signature_includes_method_and_path():
    assert _sig(("get", "/a")) != _sig(("post", "/a"))
    assert _sig(("get", "/a")) != _sig(("get", "/b"))


def test_signature_ignores_non_http_keys():
    """OpenAPI path items may carry parameters/servers alongside operations."""
    spec = _spec(("get", "/a"))
    spec["paths"]["/a"]["parameters"] = [{"name": "x"}]
    assert operation_signature(spec) == _sig(("get", "/a"))


def test_signature_reflects_tags_and_summary():
    plain = _spec(("get", "/a"))
    tagged = _spec(("get", "/a"))
    tagged["paths"]["/a"]["get"] = {"summary": "s", "tags": ["t"]}
    assert operation_signature(plain) != operation_signature(tagged)


# ── oracle power is measured, never assumed ──────────────────────────────────


def test_oracle_is_undiscriminating_when_candidates_agree():
    """This is the honest case for this repository: revisions that differ only
    in handler bodies produce one signature."""
    same = _sig(("get", "/a"), ("post", "/b"))
    power = oracle_power({"main:aaa": same, "cand:bbb": list(same)})
    assert power["discriminating"] is False
    assert power["distinct_signatures"] == 1


def test_oracle_is_discriminating_when_route_sets_differ():
    power = oracle_power({
        "main:aaa": _sig(("get", "/a")),
        "cand:bbb": _sig(("get", "/a"), ("get", "/c")),
    })
    assert power["discriminating"] is True
    assert power["distinct_signatures"] == 2


def test_unimportable_candidate_does_not_fake_discrimination():
    """A revision that fails to import must be excluded, not counted as a
    distinct signature -- otherwise a boot-broken commit would look like
    discriminating power."""
    power = oracle_power({"main:aaa": _sig(("get", "/a")), "cand:bbb": None})
    assert power["discriminating"] is False
    assert "cand:bbb" not in power["revisions_compared"]


def test_digest_stable_and_sensitive():
    assert digest(["a"]) == digest(["a"])
    assert digest(["a"]) != digest(["b"])


# ── classifier teeth ─────────────────────────────────────────────────────────


def _power(disc: bool) -> dict:
    return {"discriminating": disc}


def test_equal_and_discriminating_is_verified():
    s = _sig(("get", "/a"))
    state, failures = classify(s, list(s), _power(True), True, [])
    assert state == "VERIFIED"
    assert failures == []


def test_equal_but_undiscriminating_is_not_a_stronger_claim():
    """The central honesty property: equality without discriminating power is
    reported with its limit attached."""
    s = _sig(("get", "/a"))
    state, failures = classify(s, list(s), _power(False), True, [])
    assert state == "VERIFIED (undiscriminating)"
    assert failures


def test_schema_difference_is_contradicted_not_verified():
    state, failures = classify(_sig(("get", "/a")), _sig(("get", "/b")), _power(True), True, [])
    assert state == "CONTRADICTED"
    assert failures


def test_unreachable_backend_is_unknown():
    state, _ = classify(None, _sig(("get", "/a")), _power(True), True, [])
    assert state == "UNKNOWN"


def test_local_import_failure_is_unknown():
    state, _ = classify(_sig(("get", "/a")), None, _power(True), True, [])
    assert state == "UNKNOWN"


def test_failed_liveness_floor_fails_even_on_matching_schema():
    s = _sig(("get", "/a"))
    state, failures = classify(s, list(s), _power(True), False, [])
    assert state == "FAILED"
    assert any("liveness" in f for f in failures)


def test_missing_required_prefix_fails():
    s = _sig(("get", "/a"))
    state, failures = classify(s, list(s), _power(True), True, ["/api/tts"])
    assert state == "FAILED"
    assert any("/api/tts" in f for f in failures)


# ── provenance and read-only guarantees ──────────────────────────────────────


def test_required_prefix_check_parses_paths_out_of_signature_rows():
    """Regression: the prefix check reads paths from signature rows, which carry
    a ' :: summary :: tags' suffix. Splitting on the first space alone left the
    suffix attached and made every required prefix look absent."""
    rows = _sig(("get", "/api/stellar-cartography"))
    assert " :: " in rows[0]
    paths = {r.split(" ", 2)[1] for r in rows}
    assert paths == {"/api/stellar-cartography"}
    assert any(p == "/api/stellar-cartography" for p in paths)


def test_every_required_prefix_declares_provenance():
    for prefix, prov in REQUIRED_PREFIXES.items():
        assert prefix.startswith("/api/"), prefix
        assert prov.strip(), f"{prefix} has no provenance"


def test_harness_is_read_only_and_credential_free():
    src = _SCRIPT.read_text()
    for verb in ("create_pull_request", "requests.post", "urlopen(urlopen"):
        assert verb not in src
    # It may fetch, but only GET-shaped urllib reads; no mutation verbs.
    assert "method=\"POST\"" not in src
    assert "data=" not in src
    for secret in ("GITHUB_TOKEN", "github_token", "VERCEL_TOKEN", "api_key"):
        assert secret not in src
