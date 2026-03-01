from pathlib import Path

from image_reviewer.image_io import save_annotated_image
from image_reviewer.output import log
from image_reviewer.server import ViewerResult, run_server


class _Api:
    """JS-callable API exposed via window.pywebview.api."""

    def __init__(self, state, output_path, window_ref):
        self._state = state
        self._output_path = output_path
        self._window_ref = window_ref

    def accept(self, image_data=None):
        annotated_path = self._save_annotations(image_data)
        self._state.result = ViewerResult(action="accept", annotated_path=annotated_path)
        self._state.done_event.set()
        self._window_ref[0].destroy()

    def reject(self, image_data=None):
        annotated_path = self._save_annotations(image_data)
        self._state.result = ViewerResult(action="reject", annotated_path=annotated_path)
        self._state.done_event.set()
        self._window_ref[0].destroy()

    def _save_annotations(self, image_data) -> str | None:
        if not image_data:
            return None
        save_annotated_image(image_data, self._output_path)
        return str(self._output_path)


def run_viewer(
    image_path: Path, output_path: Path, port: int = 0
) -> ViewerResult:
    server, actual_port, state = run_server(image_path, output_path, port)
    url = f"http://127.0.0.1:{actual_port}"
    log(f"Opening native window at {url}")

    try:
        import webview

        window_ref = [None]
        api = _Api(state, output_path, window_ref)
        window = webview.create_window("Image Reviewer", url, js_api=api)
        window_ref[0] = window
        webview.start()
    finally:
        server.shutdown()

    return state.result
