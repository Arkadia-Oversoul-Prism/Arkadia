"""Distribution upload — the stored extension is derived from the content type.

``api/distribution.py`` writes uploads into ``static/releases``, and ``api.main`` mounts
``/static`` from that tree, so the extension of a stored file decides the ``Content-Type``
the canonical origin serves those bytes with. Measured at ``main`` ``cb284195`` against the
real handler: the stored name took its extension from the *client's filename* while only the
client's ``content_type`` was validated, so

    POST /api/distribution/upload   filename="track.html", content_type="audio/mpeg"

was accepted and stored as ``<uuid>_audio.html``, and ``GET /static/releases/<that name>``
answered ``200`` with ``content-type: text/html`` and the uploaded body. The upload route
declares no ``security`` requirement, so that was an anonymous stored-content-injection
primitive on the production origin. The artwork field had the same defect.

The repair derives both the accepted set and the stored extension from one map per field,
so a client filename can no longer choose what the origin serves. This guard pins that:

* every accepted type is stored with its canonical extension;
* a client filename cannot choose the extension, and the served ``Content-Type`` is the
  audio/image type rather than ``text/html`` (the negative control for the defect shape);
* a filename carrying path segments cannot place a file outside ``UPLOAD_DIR``;
* an unsupported type is still rejected, and rejects nothing else.

No production mutation was performed: this guard exercises the handler in-process against a
temporary working directory.
"""
from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

import api.distribution as dist


def _extension_from_filename(filename: str) -> str:
    """The pre-repair expression, kept so the control can prove the defect shape."""
    return filename.rsplit(".", 1)[-1] if filename and "." in filename else "mp3"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A client over the real router, serving the real relative upload tree.

    The working directory moves to ``tmp_path`` so ``static/releases`` and ``data/`` resolve
    inside the test, and ``/static`` is mounted the way ``api.main`` mounts it.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "static" / "releases").mkdir(parents=True)
    app = FastAPI()
    app.include_router(dist.router)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    with TestClient(app) as test_client:
        yield test_client


def _upload(client, *, audio=("track.mp3", "audio/mpeg"), artwork=("cover.png", "image/png")):
    return client.post(
        "/api/distribution/upload",
        files={
            "audio": (audio[0], b"<script>alert(document.domain)</script>", audio[1]),
            "artwork": (artwork[0], b"\x89PNG\r\n", artwork[1]),
        },
        data={"title": "probe", "artistName": "probe"},
    )


def test_the_allowlists_only_map_to_media_extensions():
    """A future accepted type cannot arrive with a browser-interpretable extension."""
    assert set(dist.AUDIO_EXTENSION_BY_TYPE.values()) <= {"mp3", "wav", "flac"}
    assert set(dist.ARTWORK_EXTENSION_BY_TYPE.values()) <= {"jpg", "png"}


@pytest.mark.parametrize(
    "content_type,expected",
    [
        ("audio/mpeg", "mp3"),
        ("audio/mp3", "mp3"),
        ("audio/wav", "wav"),
        ("audio/x-wav", "wav"),
        ("audio/flac", "flac"),
        ("audio/x-flac", "flac"),
    ],
)
def test_accepted_audio_types_are_stored_with_their_canonical_extension(
    client, tmp_path, content_type, expected
):
    response = _upload(client, audio=("anything.bin", content_type))
    assert response.status_code == 200, response.text
    stored = sorted(os.listdir(tmp_path / "static" / "releases"))
    audio_files = [name for name in stored if "_audio." in name]
    assert len(audio_files) == 1
    assert audio_files[0].endswith(f"_audio.{expected}")


@pytest.mark.parametrize(
    "content_type,expected", [("image/jpeg", "jpg"), ("image/jpg", "jpg"), ("image/png", "png")]
)
def test_accepted_artwork_types_are_stored_with_their_canonical_extension(
    client, tmp_path, content_type, expected
):
    response = _upload(client, artwork=("anything.html", content_type))
    assert response.status_code == 200, response.text
    stored = sorted(os.listdir(tmp_path / "static" / "releases"))
    artwork_files = [name for name in stored if "_artwork." in name]
    assert len(artwork_files) == 1
    assert artwork_files[0].endswith(f"_artwork.{expected}")


def test_negative_control_a_client_filename_cannot_choose_the_served_content_type(
    client, tmp_path
):
    """The defect shape: an HTML filename over an accepted audio type.

    Pre-repair this stored ``<uuid>_audio.html`` and the origin served the body as
    ``text/html``. The control proves the detector discriminates: the old expression on the
    same input yields ``html``, while the handler must not.
    """
    assert _extension_from_filename("track.html") == "html", "control premise"

    response = _upload(client, audio=("track.html", "audio/mpeg"))
    assert response.status_code == 200, response.text

    stored_name = response.json()["release"]["audioUrl"].rsplit("/", 1)[-1]
    assert stored_name.endswith("_audio.mp3"), stored_name
    assert not stored_name.endswith(".html")

    served = client.get(f"/static/releases/{stored_name}")
    assert served.status_code == 200
    assert served.headers["content-type"].startswith("audio/"), served.headers["content-type"]
    assert "text/html" not in served.headers["content-type"]


def test_negative_control_a_filename_cannot_escape_the_upload_directory(client, tmp_path):
    """A filename carrying path segments must not place a file outside ``UPLOAD_DIR``."""
    response = _upload(client, audio=("song.mp3/../../../../escaped.mp3", "audio/mpeg"))
    assert response.status_code == 200, response.text

    upload_root = (tmp_path / "static" / "releases").resolve()
    written = [
        path for path in tmp_path.rglob("*") if path.is_file() and path.name != "releases.json"
    ]
    assert written, "the upload must still store its two files"
    for path in written:
        assert upload_root in path.resolve().parents, path

    stored_name = response.json()["release"]["audioUrl"].rsplit("/", 1)[-1]
    assert "/" not in stored_name and ".." not in stored_name


def test_an_unsupported_content_type_is_rejected_and_writes_nothing(client, tmp_path):
    response = _upload(client, audio=("track.mp3", "text/html"))
    assert response.status_code == 400
    assert "Audio must be MP3, WAV, or FLAC" in response.json()["detail"]
    assert list((tmp_path / "static" / "releases").iterdir()) == []

    response = _upload(client, artwork=("cover.png", "image/svg+xml"))
    assert response.status_code == 400
    assert "Artwork must be JPEG or PNG" in response.json()["detail"]
    assert list((tmp_path / "static" / "releases").iterdir()) == []
