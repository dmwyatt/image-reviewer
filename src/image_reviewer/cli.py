import argparse
import os
import sys
import webbrowser
from pathlib import Path

from image_reviewer.image_io import detect_mime_type
from image_reviewer.output import log, log_error
from image_reviewer.server import ViewerResult, run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-reviewer",
        description="Review and annotate images with a native or browser UI.",
    )
    parser.add_argument("image", help="Path to the image file to review")
    parser.add_argument("-o", "--output", help="Output path for annotated image")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Open in browser instead of native window",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for HTTP server (default: random)",
    )
    return parser


def validate_image_path(path_str: str) -> Path:
    path = Path(path_str).resolve()
    if not path.exists():
        log_error(f"File not found: {path}")
        sys.exit(2)
    if not path.is_file():
        log_error(f"Not a file: {path}")
        sys.exit(2)
    try:
        detect_mime_type(path)
    except ValueError as e:
        log_error(str(e))
        sys.exit(2)
    return path


def resolve_output_path(image_path: Path, output_arg: str | None) -> Path:
    if output_arg:
        return Path(output_arg)
    stem = image_path.stem
    suffix = image_path.suffix
    return image_path.parent / f"{stem}_annotated{suffix}"


def run_serve_mode(
    image_path: Path, output_path: Path, port: int = 0
) -> ViewerResult:
    server, actual_port, state = run_server(image_path, output_path, port)
    url = f"http://127.0.0.1:{actual_port}"
    log(f"Serving at {url}")
    webbrowser.open(url)
    try:
        state.done_event.wait()
    except KeyboardInterrupt:
        log("\nInterrupted")
    finally:
        server.shutdown()
    return state.result


def run_native_mode(
    image_path: Path, output_path: Path, port: int = 0
) -> ViewerResult:
    import webview

    from image_reviewer.viewer import run_viewer

    return run_viewer(image_path, output_path, port)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    image_path = validate_image_path(args.image)
    output_path = resolve_output_path(image_path, args.output)

    if args.serve:
        result = run_serve_mode(image_path, output_path, args.port)
    else:
        result = run_native_mode(image_path, output_path, args.port)

    code = _exit_code(result)

    if not args.serve:
        # GTK leaves non-daemon threads that prevent clean exit.
        # All I/O is done, so hard-exit is safe.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)

    return code


def _exit_code(result: ViewerResult) -> int:
    if result.annotated_path:
        print(result.annotated_path)
    return 0 if result.action == "accept" else 1
