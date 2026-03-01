import base64
import json
from pathlib import Path
from urllib.request import urlopen, Request

import pytest

from image_reviewer.server import run_server


@pytest.fixture
def server_fixture(sample_png: Path, tmp_dir: Path):
    output_path = tmp_dir / "annotated.png"
    server, port, state = run_server(sample_png, output_path)
    yield server, port, state, output_path
    server.shutdown()


class TestServerEndpoints:
    def test_get_root_returns_html(self, server_fixture):
        _, port, _, _ = server_fixture
        resp = urlopen(f"http://127.0.0.1:{port}/")
        body = resp.read().decode()
        assert resp.status == 200
        assert "text/html" in resp.headers["Content-Type"]
        assert "fabric" in body.lower() or "canvas" in body.lower()

    def test_get_root_contains_image_data(self, server_fixture, sample_png: Path):
        _, port, _, _ = server_fixture
        resp = urlopen(f"http://127.0.0.1:{port}/")
        body = resp.read().decode()
        assert "data:image/png;base64," in body

    def test_get_fabric_js(self, server_fixture):
        _, port, _, _ = server_fixture
        resp = urlopen(f"http://127.0.0.1:{port}/fabric.min.js")
        body = resp.read().decode()
        assert resp.status == 200
        assert "fabric" in body.lower()

    def test_post_accept(self, server_fixture):
        _, port, state, _ = server_fixture
        req = Request(
            f"http://127.0.0.1:{port}/api/accept",
            data=b"",
            method="POST",
        )
        resp = urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        assert state.result.action == "accept"
        assert state.done_event.is_set()

    def test_post_reject(self, server_fixture):
        _, port, state, _ = server_fixture
        req = Request(
            f"http://127.0.0.1:{port}/api/reject",
            data=b"",
            method="POST",
        )
        resp = urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        assert state.result.action == "reject"
        assert state.done_event.is_set()

    def test_post_accept_with_annotations(self, server_fixture):
        _, port, state, output_path = server_fixture
        png_b64 = base64.b64encode(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                "2mP8/58BAwAI/AL+hc2rNAAAAABJRU5ErkJggg=="
            )
        ).decode()
        data_url = f"data:image/png;base64,{png_b64}"
        body = json.dumps({"image": data_url}).encode()
        req = Request(
            f"http://127.0.0.1:{port}/api/accept",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        resp = urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        assert state.result.action == "accept"
        assert state.result.annotated_path == str(output_path)
        assert state.done_event.is_set()
        assert output_path.exists()

    def test_post_reject_with_annotations(self, server_fixture):
        _, port, state, output_path = server_fixture
        png_b64 = base64.b64encode(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                "2mP8/58BAwAI/AL+hc2rNAAAAABJRU5ErkJggg=="
            )
        ).decode()
        data_url = f"data:image/png;base64,{png_b64}"
        body = json.dumps({"image": data_url}).encode()
        req = Request(
            f"http://127.0.0.1:{port}/api/reject",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        resp = urlopen(req)
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        assert state.result.action == "reject"
        assert state.result.annotated_path == str(output_path)
        assert state.done_event.is_set()
        assert output_path.exists()

    def test_default_result_is_reject(self, server_fixture):
        _, _, state, _ = server_fixture
        assert state.result.action == "reject"


class TestGet404:
    def test_unknown_path(self, server_fixture):
        _, port, _, _ = server_fixture
        from urllib.error import HTTPError

        with pytest.raises(HTTPError) as exc_info:
            urlopen(f"http://127.0.0.1:{port}/unknown")
        assert exc_info.value.code == 404
