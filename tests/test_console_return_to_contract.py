"""Sign-in return-to-destination journey — PRR-02.

A protected surface renders the auth threshold while the address bar still
holds the path the user asked for. Before this work item, both entries into the
sign-in surface dropped that destination: after a successful sign-in the user
was left on `/login` with no route back to the surface they had requested.

Domain: the Arkadia Console (`web/arkadia_console`), the primary application.
The archived Prism kept its own post-sign-in continuity; the console's threshold
is the equivalent seam and is reconciled here without a second auth system —
identity, session, and `require_auth` contracts are untouched.

What is asserted:

  * `lib/returnTo.ts` is **executed** in Node (surfaces + router + the module
    concatenated with types stripped, `window.sessionStorage` stubbed): the
    remembered destination survives, is cleared on read, an external or
    invented target degrades to the router's own fallback (never off-origin),
    a target resolving back to `/login` is refused, and stored memory wins
    over a `?returnTo=` query;
  * the threshold and the shell's sign-in button both remember the current
    path **before** navigating to the login surface;
  * `SignInPage` consumes the destination only after `signIn` resolves —
    never in the failure path;
  * the pinned sign-in surface testids and the exact `href="/login"` contract
    (`test_aeas05_canonical_frontend_acceptance.py`) are preserved.

Each load-bearing detector carries a negative control that reproduces the
defect shape it exists to catch.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"

SURFACES_PATH = SRC / "lib" / "surfaces.ts"
ROUTER_PATH = SRC / "lib" / "router.ts"
RETURN_TO_PATH = SRC / "lib" / "returnTo.ts"
APP_PATH = SRC / "App.tsx"
SHELL_PATH = SRC / "components" / "Shell.tsx"
SIGNIN_PATH = SRC / "pages" / "SignInPage.tsx"

SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
ROUTER = ROUTER_PATH.read_text(encoding="utf-8")
RETURN_TO = RETURN_TO_PATH.read_text(encoding="utf-8")
APP = APP_PATH.read_text(encoding="utf-8")
SHELL = SHELL_PATH.read_text(encoding="utf-8")
SIGNIN = SIGNIN_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detector — the exact call-order contract of the two threshold entries.
# ---------------------------------------------------------------------------


def _orders_remember_before_navigate(app_source: str) -> bool:
    """True when the shared navigation wrapper records the destination before
    it navigates, guarded on the login surface."""
    wrapper = re.search(
        r"const handleNavigate = \(id[^)]*\) => \{(.*?)\n  \};",
        app_source,
        flags=re.DOTALL,
    )
    if not wrapper:
        return False
    body = wrapper.group(1)
    if "rememberReturnTo(route.path)" not in body:
        return False
    if 'if (id === "login")' not in body:
        return False
    return body.index("rememberReturnTo(") < body.index("navigate(")


def _consume_is_outside_the_failure_path(source: str) -> bool:
    """True when `consumeReturnTo` runs after a resolved signIn and never in `catch`."""
    after_signin = source.find("await signIn(email, password)")
    if after_signin == -1 or source.find("consumeReturnTo(", after_signin) == -1:
        return False
    catch_block = re.search(r"catch\s*\(error\)\s*\{(.*?)\}\s*finally", source, re.DOTALL)
    return bool(catch_block) and "consumeReturnTo" not in catch_block.group(1)


# ---------------------------------------------------------------------------
# Executed half — run the real modules in Node.
# ---------------------------------------------------------------------------


def _strip_ts(source: str) -> str:
    """Remove only module wiring; Node 22 strips the type syntax itself."""
    source = re.sub(r"^import[^;]+;\s*$", "", source, flags=re.MULTILINE)
    source = re.sub(r"^export\s+", "", source, flags=re.MULTILINE)
    return source


def _run(scenarios: list[str]) -> dict:
    """Execute surfaces + router + returnTo in Node; return scenario results."""
    node = shutil.which("node")
    assert node, "node is required to evaluate the return-to module"
    window_stub = (
        "globalThis.window = { location: { pathname: '/', search: '' }, sessionStorage: "
        "(() => { const m = {}; return { "
        "getItem: (k) => (Object.prototype.hasOwnProperty.call(m, k) ? m[k] : null), "
        "setItem: (k, v) => { m[k] = String(v); }, "
        "removeItem: (k) => { delete m[k]; } }; })() };\n"
    )
    script = (
        window_stub
        + _strip_ts(SURFACES)
        + "\n"
        + _strip_ts(ROUTER)
        + "\n"
        + _strip_ts(RETURN_TO)
        + "\n"
        + "function snap(label) { out[label] = { stored: window.sessionStorage.getItem('arkadia.returnTo') }; }\n"
        + "const out = {};\n"
        + "\n".join(scenarios)
        + "\nconsole.log(JSON.stringify(out));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"returnTo evaluation failed:\n{result.stderr.strip()}\n{script}"
    return json.loads(result.stdout)


def test_return_to_roundtrip_survives_and_is_cleared():
    out = _run(
        [
            "rememberReturnTo('/solariun');",
            "out.first = consumeReturnTo('');",
            "snap('afterFirst');",
            "out.second = consumeReturnTo('');",
            "snap('afterSecond');",
        ]
    )
    assert out["first"]["surface"] == "solariun", out
    assert out["afterFirst"]["stored"] is None, "the destination must be cleared after one read"
    assert out["second"] is None, "a spent destination must not return twice"
    assert out["afterSecond"]["stored"] is None


def test_return_to_preserves_the_section_of_the_protected_path():
    out = _run(["rememberReturnTo('/solariun/knowledge');", "out.r = consumeReturnTo('');"])
    assert out["r"]["surface"] == "solariun"
    assert out["r"]["section"] == "knowledge"


def test_sign_in_surface_is_never_remembered_as_a_destination():
    out = _run(
        [
            "rememberReturnTo('/login');",
            "snap('afterRemember');",
            "out.r = consumeReturnTo('');",
        ]
    )
    assert out["afterRemember"]["stored"] is None, "/login must not be stored — nothing to return to"
    assert out["r"] is None


def test_query_deep_link_is_honoured_when_nothing_was_remembered():
    out = _run(["out.r = consumeReturnTo('?returnTo=%2Fknowledge');"])
    assert out["r"]["surface"] == "knowledge", out


def test_remembered_path_wins_over_the_query():
    out = _run(["rememberReturnTo('/weaver');", "out.r = consumeReturnTo('?returnTo=%2Fabout');"])
    assert out["r"]["surface"] == "weaver", out


def test_external_return_target_degrades_to_the_router_fallback():
    """An absolute URL can never become navigation — resolvePath decides."""
    out = _run(
        [
            "rememberReturnTo('https://evil.example/x');",
            "out.r = consumeReturnTo('');",
            "out.q = consumeReturnTo('?returnTo=' + encodeURIComponent('https://evil.example/x'));",
        ]
    )
    for key in ("r", "q"):
        assert out[key] is not None, out
        assert out[key]["surface"] in {"home", "novanet", "arkana", "solariun", "engineering-lab", "solspire", "knowledge", "weaver", "about"}, out[key]
        assert out[key]["path"].startswith("/"), out[key]
        assert "evil.example" not in out[key]["path"], "an external target leaked into the route"


def test_return_target_that_resolves_back_to_sign_in_is_refused():
    out = _run(["out.r = consumeReturnTo('?returnTo=%2Flogin');"])
    assert out["r"] is None, "a destination that loops back to /login must be refused"


def test_no_destination_means_null_not_a_guess():
    out = _run(["out.r = consumeReturnTo('');"])
    assert out["r"] is None


# ---------------------------------------------------------------------------
# Source-contract half — ordering and preserved pins.
# ---------------------------------------------------------------------------


def test_auth_threshold_crosses_through_the_recording_wrapper():
    threshold = re.search(r"function AuthThreshold.*?\n\}", APP, re.DOTALL)
    assert threshold, "App.tsx declares no AuthThreshold"
    assert 'onNavigate("login")' in threshold.group(0), "the threshold must cross to /login"
    assert re.search(r"<AuthThreshold onNavigate=\{handleNavigate\}", APP), (
        "the threshold must cross through the wrapper that records the destination"
    )
    assert _orders_remember_before_navigate(APP), (
        "the shared wrapper must remember the protected path before it navigates"
    )


def test_shell_sign_in_crosses_through_the_recording_wrapper():
    assert 'data-testid="nav-sign-in"' in SHELL, "the shell declares no nav-sign-in control"
    assert "rememberReturnTo" not in SHELL, (
        "the shell must not read the pathname itself — it crosses through the wrapper"
    )
    assert re.search(r"<Shell[^>]*onNavigate=\{handleNavigate\}", APP, re.DOTALL), (
        "the shell's navigation (including sign-in) must go through the wrapper"
    )


def test_signin_page_returns_only_after_a_confirmed_sign_in():
    assert _consume_is_outside_the_failure_path(SIGNIN), (
        "the destination must be consumed after signIn resolves and never on the failure path"
    )
    assert re.search(r"<SignInPage onNavigate=\{handleNavigate\}", APP), (
        "the sign-in page must navigate back through the shared wrapper"
    )


def test_negative_control_detects_navigation_without_remembering():
    synthetic = """
    const handleNavigate = (id, section) => {
      navigate(id, section);
    };
    """
    assert not _orders_remember_before_navigate(synthetic), (
        "a wrapper that navigates without remembering must be flagged"
    )
    reversed_order = """
    const handleNavigate = (id, section) => {
      navigate(id, section);
      if (id === "login") rememberReturnTo(route.path);
    };
    """
    assert not _orders_remember_before_navigate(reversed_order), (
        "remembering after navigating must be flagged — the route has already changed"
    )
    ungated = """
    const handleNavigate = (id, section) => {
      rememberReturnTo(route.path);
      navigate(id, section);
    };
    """
    assert not _orders_remember_before_navigate(ungated), (
        "an ungated remember (every navigation overwrites the destination) must be flagged"
    )


def test_negative_control_detects_consume_in_the_failure_path():
    synthetic = """
    try {
      await signIn(email, password);
      const d = consumeReturnTo(window.location.search);
      if (d) onNavigate(d.surface, d.section);
    } catch (error) {
      const d = consumeReturnTo(window.location.search);
      setLocalError("nope");
    } finally {
      setBusy(false);
    }
    """
    assert not _consume_is_outside_the_failure_path(synthetic), (
        "a consume inside catch must be flagged — a failed sign-in may not spend the destination"
    )


def test_pinned_signin_surface_contracts_are_preserved():
    """`test_aeas05_canonical_frontend_acceptance.py` pins these; the return leg
    must not disturb them."""
    for testid in ("tab-signin", "input-email-signin", "input-password-signin", "button-signin"):
        assert f'data-testid="{testid}"' in SIGNIN, testid
    assert 'href="/login"' in APP, "the threshold anchor must keep the exact pinned href"
    assert 'data-testid="auth-threshold-signin"' in APP
    assert 'path: "/login"' in SURFACES


def test_return_to_module_is_imported_where_it_is_used():
    assert 'from "./lib/returnTo"' in APP
    assert 'from "../lib/returnTo"' in SIGNIN
    assert "returnTo" not in SHELL, "the shell must not touch return-to memory directly"
