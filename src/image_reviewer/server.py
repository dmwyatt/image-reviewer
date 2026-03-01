import json
import threading
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources
from pathlib import Path

from image_reviewer.image_io import encode_image_to_data_url, save_annotated_image


@dataclass
class ViewerResult:
    action: str = "reject"
    annotated_path: str | None = None


@dataclass
class ServerState:
    image_path: Path = field(default_factory=Path)
    output_path: Path = field(default_factory=Path)
    result: ViewerResult = field(default_factory=ViewerResult)
    done_event: threading.Event = field(default_factory=threading.Event)


class ReviewHandler(BaseHTTPRequestHandler):
    state: ServerState

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self._serve_html()
        elif self.path == "/fabric.min.js":
            self._serve_fabric()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/accept":
            self._handle_action("accept")
        elif self.path == "/api/reject":
            self._handle_action("reject")
        else:
            self.send_error(404)

    def _serve_html(self):
        data_url = encode_image_to_data_url(self.state.image_path)
        html_template = _load_asset("app.html")
        html = html_template.replace("__IMAGE_DATA_URL__", data_url)
        self._send_response(html, "text/html")

    def _serve_fabric(self):
        js = _load_asset("fabric.min.js")
        self._send_response(js, "application/javascript")

    def _handle_action(self, action: str):
        annotated_path = self._save_annotations_if_present()
        self.state.result = ViewerResult(action=action, annotated_path=annotated_path)
        self.state.done_event.set()
        self._send_json({"status": "ok"})

    def _save_annotations_if_present(self) -> str | None:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return None
        body = self.rfile.read(content_length)
        if not body.strip():
            return None
        data = json.loads(body)
        image_data = data.get("image", "")
        if not image_data:
            return None
        save_annotated_image(image_data, self.state.output_path)
        return str(self.state.output_path)

    def _send_response(self, content: str, content_type: str):
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _load_asset(name: str) -> str:
    return resources.files("image_reviewer.assets").joinpath(name).read_text("utf-8")


def make_handler(state: ServerState):
    class BoundHandler(ReviewHandler):
        def __init__(self, *args, **kwargs):
            self.state = state
            super().__init__(*args, **kwargs)

    return BoundHandler


def run_server(
    image_path: Path, output_path: Path, port: int = 0
) -> tuple[HTTPServer, int, ServerState]:
    state = ServerState(image_path=image_path, output_path=output_path)
    handler_class = make_handler(state)
    server = HTTPServer(("127.0.0.1", port), handler_class)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.1), daemon=True)
    thread.start()
    return server, actual_port, state
