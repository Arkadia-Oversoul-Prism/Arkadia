"""Spiral Codex corpus contract — the shared public corpus reaches the console.

Directive §3.3 requires API evidence before any UI claim, and §3.1 requires one
endpoint registry. This guard binds the console's Encyclopedia Galactica lens to
the **real** served contract, so the surface cannot drift into claiming a corpus
it does not read.

Defects this guard closes, each measured against the canonical deployment at base
``main 68403b9e``:

1.  **An unsurfaced open read.** ``GET /api/codex`` returns ``200`` with 661
    documents / 4,413,059 characters and requires no identity. The archived Prism
    built two routes on it (``/encyclopedia``, ``/spiral-codex``) and the console
    referenced it nowhere, so a verified capability had no surface.

2.  **A dead path a naive port would have reintroduced.** The archive fetched
    ``/api/codex/categories`` in parallel with the corpus
    (``SpiralCodexFeed.tsx:90-91``). That route is **not served** — absent from
    ``app.openapi()`` and ``404`` on production — so a faithful port would fire a
    request that can never succeed. Categories must be derived from the documents.

3.  **A false reason stated in the UI.** ``NovaNetPage`` told the reader the hub
    sub-views' contracts were "either unverified or sovereign-key gated, which the
    authenticated client cannot satisfy". True for ``/api/ims/inquiries`` (403
    ``Sovereign key required``); false for ``/api/codex``, an unauthenticated 200.

The derived helpers are **imported and executed** through Node's native TypeScript
support, so the assertions observe what the shipped module computes — not a
regex-stripped copy of it. Two defects in the first draft of this file are now
guarded, because both were real and both are easy to repeat:

* a source-text detector must run on **comment-stripped** source — a path named
  only in the doc comment explaining why the path is forbidden is not a request;
* prose assertions must be **whitespace-normalised** — JSX wraps a sentence across
  lines, so an exact substring pin fails on correct copy.

Disjoint from ``test_console_endpoint_registry_contract.py`` (registry shape),
``test_console_legacy_route_coverage.py`` (legacy path disposition) and
``test_console_read_aloud_contract.py`` (the voice slice).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"

ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"
CONTRACT_PATH = SRC / "components" / "novaNet" / "spiralCodexContract.ts"
PANEL_PATH = SRC / "components" / "novaNet" / "SpiralCodexPanel.tsx"
NOVANET_PATH = SRC / "pages" / "NovaNetPage.tsx"

ENDPOINTS = ENDPOINTS_PATH.read_text(encoding="utf-8")
CONTRACT = CONTRACT_PATH.read_text(encoding="utf-8")
PANEL = PANEL_PATH.read_text(encoding="utf-8")
NOVANET = NOVANET_PATH.read_text(encoding="utf-8")


def _code_only(source: str) -> str:
    """Source with comments removed.

    A path named only in a doc comment is not a request. Without this, a detector
    searching for a forbidden path matches the comment that *explains why the path
    is forbidden* — which is how the first draft of this guard failed on correct
    source.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", source)


def _flat(text: str) -> str:
    """Whitespace-collapsed text, for assertions over JSX prose.

    JSX wraps a sentence across lines, so an exact substring pin fails on correct
    copy. Normalising is the honest fix; loosening the assertion would not be.
    """
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# The contract is the served one, not an invented one
# ---------------------------------------------------------------------------


def _served_paths() -> set[str]:
    from api.main import app

    return set(app.openapi()["paths"])


def test_the_corpus_path_is_declared_once_in_the_registry():
    """§3.1: one registry. The panel must reference the registry, never inline."""
    assert 'publicCodex: "/api/codex"' in ENDPOINTS, (
        "the shared corpus is not declared in lib/endpoints.ts"
    )
    assert ENDPOINTS.count('"/api/codex"') == 1, (
        "the corpus path is declared more than once in the registry"
    )


def test_the_declared_corpus_path_is_actually_served():
    """The registry entry names a route the application really serves."""
    assert "/api/codex" in _served_paths(), (
        "the registry declares a corpus path the served app does not expose"
    )


def test_the_panel_reads_the_registry_not_a_literal():
    """The panel composes the contract from the registry member."""
    code = _code_only(PANEL)
    assert "endpoints.publicCodex" in code, (
        "SpiralCodexPanel does not read endpoints.publicCodex"
    )
    assert '"/api/codex"' not in code, (
        "SpiralCodexPanel inlines the corpus path instead of using the registry"
    )


def test_the_categories_route_the_archive_used_is_not_served():
    """The reason categories are derived client-side, asserted rather than assumed.

    If the backend ever serves `/api/codex/categories`, this fails and the
    derivation can be revisited deliberately instead of silently diverging.
    """
    assert "/api/codex/categories" not in _served_paths(), (
        "the app now serves /api/codex/categories — revisit the client-side derivation"
    )
    assert "/api/codex/categories" not in _code_only(PANEL), (
        "the panel requests a categories route the app does not serve"
    )


def test_the_registry_distinguishes_the_public_corpus_from_the_personal_one():
    """`/api/codex` (shared) and `/api/me/codex` (personal) are different contracts."""
    assert 'codex: "/api/me/codex"' in ENDPOINTS
    assert 'publicCodex: "/api/codex"' in ENDPOINTS
    assert ENDPOINTS.count('codex: "/api/me/codex"') == 1


# ---------------------------------------------------------------------------
# The derived behaviour is executed through the real module
# ---------------------------------------------------------------------------

_NODE = shutil.which("node")
_needs_node = pytest.mark.skipif(
    _NODE is None, reason="node is required to execute the contract module"
)

_CORPUS = {
    "status": "radiant",
    "total_docs": 3,
    "live_docs": 3,
    "total_chars": 120,
    "scrolls": {
        "alpha": {"id": "alpha", "category": "CREATIVE_OS", "label": "Alpha",
                  "description": "first", "preview": "p1", "chars": 40, "content": "BODY-ALPHA"},
        "beta": {"id": "beta", "category": "CREATIVE_OS", "label": "Beta",
                 "description": "second", "preview": "p2", "chars": 50, "content": "BODY-BETA"},
        "gamma": {"id": "gamma", "category": "SYSTEM", "label": "Gamma",
                  "description": "third", "preview": "p3", "chars": 30, "content": "BODY-GAMMA"},
    },
}

_PROBE = f"""
import {{ toDocuments, deriveCategories, filterDocuments, CODEX_ALL_CATEGORIES, CODEX_DISPLAY_LIMIT }}
  from {json.dumps(str(CONTRACT_PATH))};

const corpus = {json.dumps(_CORPUS)};
// A document with no category: it must be grouped, not dropped, or the facet
// counts would sum to less than the corpus.
const uncategorised = {{ scrolls: {{ delta: {{ id: "delta", label: "Delta", chars: 5 }} }} }};

const docs = toDocuments(corpus);
console.log(JSON.stringify({{
  documents: docs.map((d) => d.key),
  documentCount: docs.length,
  categories: deriveCategories(docs),
  withUncategorised: deriveCategories(toDocuments(uncategorised)),
  allMatch: filterDocuments(docs, CODEX_ALL_CATEGORIES, "").length,
  creativeOnly: filterDocuments(docs, "CREATIVE_OS", "").map((d) => d.key),
  queryLabel: filterDocuments(docs, CODEX_ALL_CATEGORIES, "alph").map((d) => d.key),
  queryDescription: filterDocuments(docs, CODEX_ALL_CATEGORIES, "second").map((d) => d.key),
  queryPreview: filterDocuments(docs, CODEX_ALL_CATEGORIES, "p3").map((d) => d.key),
  // Content is deliberately NOT searched: a match must be explainable from the
  // list, and the list never shows `content`.
  queryContentOnly: filterDocuments(docs, CODEX_ALL_CATEGORIES, "BODY-GAMMA").length,
  caseInsensitive: filterDocuments(docs, CODEX_ALL_CATEGORIES, "ALPHA").length,
  empty: filterDocuments(toDocuments(null), CODEX_ALL_CATEGORIES, "").length,
  limit: CODEX_DISPLAY_LIMIT,
  allKey: CODEX_ALL_CATEGORIES,
}}));
"""


def _run_esm(source: str, module_path: Path) -> dict:
    """Execute a probe against a TypeScript module through Node's native TS support.

    The probe script is written to a temporary directory, never beside the module
    it imports: a scratch file in `src/` is a build input the bundler would pick
    up, and an untracked artifact in the working tree is exactly the staging
    hazard the repository's git-hygiene rules forbid.
    """
    assert _NODE, "node is required to execute the contract module"
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "probe.mjs"
        script.write_text(source, encoding="utf-8")
        result = subprocess.run([_NODE, str(script)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"node failed:\n{result.stderr}"
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def behaviour() -> dict:
    return _run_esm(_PROBE, CONTRACT_PATH)


@_needs_node
def test_documents_normalise_from_the_served_map(behaviour):
    """`scrolls` is a map keyed by id; the reader normalises it to an array."""
    assert behaviour["documentCount"] == 3
    assert behaviour["documents"] == ["alpha", "beta", "gamma"]


@_needs_node
def test_facets_are_derived_from_the_documents(behaviour):
    """Facets come from the documents because no categories route is served."""
    assert behaviour["categories"] == [
        {"name": "CREATIVE_OS", "count": 2},
        {"name": "SYSTEM", "count": 1},
    ]


@_needs_node
def test_a_document_without_a_category_is_grouped_not_dropped(behaviour):
    """Dropping it would make facet counts sum to less than the corpus."""
    assert behaviour["withUncategorised"] == [{"name": "UNCATEGORISED", "count": 1}]


@_needs_node
def test_filtering_by_facet_narrows_the_corpus(behaviour):
    assert behaviour["allMatch"] == 3
    assert behaviour["creativeOnly"] == ["alpha", "beta"]


@_needs_node
def test_search_covers_the_fields_the_list_actually_shows(behaviour):
    """label / description / preview — the three the archived feed searched."""
    assert behaviour["queryLabel"] == ["alpha"]
    assert behaviour["queryDescription"] == ["beta"]
    assert behaviour["queryPreview"] == ["gamma"]


@_needs_node
def test_search_does_not_match_on_content(behaviour):
    """A document must not match on text the list never renders."""
    assert behaviour["queryContentOnly"] == 0, (
        "search matched document content, which the list does not display"
    )


@_needs_node
def test_search_is_case_insensitive(behaviour):
    assert behaviour["caseInsensitive"] == 1


@_needs_node
def test_an_absent_corpus_yields_no_documents_rather_than_raising(behaviour):
    assert behaviour["empty"] == 0


# ---------------------------------------------------------------------------
# Honest presentation: the corpus is large, so the list is bounded and says so
# ---------------------------------------------------------------------------


def test_the_rendered_list_is_bounded_and_the_bound_is_stated():
    """661 documents / ~5 MB must not be rendered silently as the whole corpus."""
    match = re.search(r"CODEX_DISPLAY_LIMIT\s*=\s*(\d+)", CONTRACT)
    assert match, "the contract declares no display limit"
    assert int(match.group(1)) > 0
    assert 'data-testid="codex-truncation"' in PANEL, (
        "the panel does not state that it renders a subset of the corpus"
    )
    assert "CODEX_DISPLAY_LIMIT" in _code_only(PANEL), "the panel does not use the declared bound"


def test_the_panel_renders_real_contract_states():
    """Loading, empty, and failure are distinguished — none is decorative."""
    for token in ("ContractState", "Loading"):
        assert token in PANEL, f"the panel does not use the shared {token} primitive"
    assert 'data-testid="codex-no-matches"' in PANEL, (
        "an empty filter result is not distinguished from an empty corpus"
    )
    # The empty-corpus copy must not claim the backend was unreachable. Asserted
    # over whitespace-normalised prose, because JSX wraps the sentence.
    assert "This is an empty corpus, not an unreachable one" in _flat(PANEL), (
        "the empty-corpus state does not distinguish an empty corpus from an unreachable backend"
    )


def test_the_panel_offers_no_upload_control():
    """The archive offered an upload; it is a mutation and is out of this slice."""
    code = _code_only(PANEL)
    assert "/api/codex/upload" not in code, (
        "the read-only panel wires the corpus upload mutation"
    )
    assert "fetch(" not in code, "the panel performs its own transport instead of apiRequest"
    assert "apiRequest" in code


# ---------------------------------------------------------------------------
# The lens is reachable, and the UI no longer states a false reason
# ---------------------------------------------------------------------------


def test_the_codex_lens_is_declared_and_rendered():
    assert re.search(r'\{\s*id:\s*"codex"', NOVANET), "NovaNetPage declares no codex lens"
    assert "SpiralCodexPanel" in NOVANET, "the codex lens renders no panel"
    assert 'section === "codex"' in NOVANET, "the codex lens is not gated on its section"


def test_the_hub_note_no_longer_calls_the_corpus_unverified():
    """Defect 3: the blanket claim was false for this contract, which is a 200."""
    flat = _flat(NOVANET)
    assert "sovereign-key gated, which the authenticated client cannot satisfy" not in flat, (
        "the blanket 'unverified or sovereign-key gated' claim is still stated"
    )
    assert "/api/ims/inquiries answers 403" in flat, (
        "the corrected note no longer distinguishes the measured reasons"
    )


# ---------------------------------------------------------------------------
# Negative controls: each detector must fail on the shape it exists to catch
# ---------------------------------------------------------------------------


def test_negative_control_detector_flags_a_panel_that_inlines_the_path():
    """The registry-bypass detector must bite on a real inline path in code."""
    mutated = _code_only(PANEL).replace("endpoints.publicCodex", '"/api/codex"')
    assert '"/api/codex"' in mutated, "control did not produce an inline path"
    assert "endpoints.publicCodex" not in mutated


def test_negative_control_detector_flags_a_reintroduced_categories_request():
    """The dead-path detector must bite on the archive's 404 route, in code."""
    mutated = _code_only(PANEL) + '\nfetch("/api/codex/categories");\n'
    assert "/api/codex/categories" in mutated
    # And the same detector must stay silent on a prose-only mention, which is
    # exactly the false positive the first draft of this guard hit.
    assert "/api/codex/categories" not in _code_only(PANEL), (
        "a doc comment that names the dead route was reported as a request"
    )


@_needs_node
def test_negative_control_search_matching_content_is_detected(tmp_path):
    """Prove the content-exclusion assertion is not vacuous.

    The control builds a module whose search includes `content`, and the executed
    behaviour must change — otherwise the exclusion assertion proves nothing.
    """
    mutated = CONTRACT.replace(
        "[doc.label, doc.description, doc.preview].some",
        "[doc.label, doc.description, doc.preview, doc.content].some",
    )
    assert mutated != CONTRACT, "control did not mutate the searched fields"
    module = tmp_path / "mutatedContract.ts"
    module.write_text(mutated, encoding="utf-8")
    observed = _run_esm(
        f"""
import {{ toDocuments, filterDocuments }} from {json.dumps(str(module))};
const c = {{ scrolls: {{ g: {{ id: "g", label: "Gamma", content: "BODY-GAMMA" }} }} }};
console.log(JSON.stringify({{ n: filterDocuments(toDocuments(c), "ALL", "BODY-GAMMA").length }}));
""",
        module,
    )
    assert observed["n"] == 1, (
        "the control did not change behaviour — the content-exclusion assertion is vacuous"
    )
