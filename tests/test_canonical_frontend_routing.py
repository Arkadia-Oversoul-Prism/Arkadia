from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.frontend_routes import configure_frontends


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_canonical_frontend_routes_share_one_origin_and_preserve_backend(tmp_path):
    prism = tmp_path / "web" / "public_prism" / "dist"
    console = tmp_path / "web" / "console" / "dist"
    _write(prism / "index.html", "<html>ARKADIA-PRISM-APP</html>")
    _write(prism / "assets" / "prism.js", "prism-asset")
    _write(prism / "arkadia-mark.svg", "<svg>mark</svg>")
    _write(console / "index.html", "<html>ARKADIA-CONSOLE-APP</html>")
    _write(console / "assets" / "console.js", "console-asset")

    app = FastAPI()

    @app.get("/api/known")
    async def known_api():
        return {"ok": True}

    configure_frontends(app, tmp_path)
    client = TestClient(app)

    assert client.get("/").text == "<html>ARKADIA-PRISM-APP</html>"
    assert client.get("/solariun/opportunity-radar").text == "<html>ARKADIA-PRISM-APP</html>"
    assert client.get("/assets/prism.js").text == "prism-asset"
    assert client.get("/arkadia-mark.svg").text == "<svg>mark</svg>"

    assert client.get("/operator").text == "<html>ARKADIA-CONSOLE-APP</html>"
    assert client.get("/operator/inspector").text == "<html>ARKADIA-CONSOLE-APP</html>"
    assert client.get("/operator/assets/console.js").text == "console-asset"
    assert client.get("/n-atlas-tester").text == "<html>ARKADIA-CONSOLE-APP</html>"

    assert client.get("/api/known").json() == {"ok": True}
    assert client.get("/api/unknown").status_code == 404
    assert client.get("/solspire/not-a-real-route").status_code == 404


def test_frontend_mounts_are_omitted_when_build_output_is_missing(tmp_path):
    app = FastAPI()
    configure_frontends(app, tmp_path)
    client = TestClient(app)

    assert client.get("/api/missing").status_code == 404
