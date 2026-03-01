from pathlib import Path
from unittest.mock import patch

import pytest

from image_reviewer.cli import (
    build_parser,
    resolve_output_path,
    validate_image_path,
)


class TestBuildParser:
    def test_requires_image_argument(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_image_path(self):
        parser = build_parser()
        args = parser.parse_args(["photo.png"])
        assert args.image == "photo.png"

    def test_output_flag(self):
        parser = build_parser()
        args = parser.parse_args(["photo.png", "-o", "out.png"])
        assert args.output == "out.png"

    def test_serve_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--serve", "photo.png"])
        assert args.serve is True

    def test_serve_defaults_false(self):
        parser = build_parser()
        args = parser.parse_args(["photo.png"])
        assert args.serve is False

    def test_port_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--port", "8080", "photo.png"])
        assert args.port == 8080

    def test_port_defaults_zero(self):
        parser = build_parser()
        args = parser.parse_args(["photo.png"])
        assert args.port == 0


class TestValidateImagePath:
    def test_valid_image(self, sample_png: Path):
        result = validate_image_path(str(sample_png))
        assert result == sample_png

    def test_nonexistent_file(self):
        with pytest.raises(SystemExit):
            validate_image_path("/nonexistent/image.png")

    def test_not_a_file(self, tmp_dir: Path):
        with pytest.raises(SystemExit):
            validate_image_path(str(tmp_dir))

    def test_unsupported_format(self, tmp_dir: Path):
        path = tmp_dir / "test.bmp"
        path.write_bytes(b"BM")
        with pytest.raises(SystemExit):
            validate_image_path(str(path))


class TestResolveOutputPath:
    def test_explicit_output(self, sample_png: Path):
        result = resolve_output_path(sample_png, "/tmp/custom.png")
        assert result == Path("/tmp/custom.png")

    def test_default_output(self, sample_png: Path):
        result = resolve_output_path(sample_png, None)
        assert result == sample_png.parent / "test_annotated.png"

    def test_default_output_jpeg(self, sample_jpeg: Path):
        result = resolve_output_path(sample_jpeg, None)
        assert result == sample_jpeg.parent / "test_annotated.jpg"


class TestMain:
    def test_reject_returns_1(self, sample_png: Path):
        from image_reviewer.cli import main
        from image_reviewer.server import ViewerResult

        result = ViewerResult(action="reject")
        with patch("image_reviewer.cli.run_serve_mode", return_value=result):
            exit_code = main(["--serve", str(sample_png)])
        assert exit_code == 1

    def test_accept_returns_0(self, sample_png: Path):
        from image_reviewer.cli import main
        from image_reviewer.server import ViewerResult

        result = ViewerResult(action="accept")
        with patch("image_reviewer.cli.run_serve_mode", return_value=result):
            exit_code = main(["--serve", str(sample_png)])
        assert exit_code == 0

    def test_accept_with_annotated_path_returns_0_and_prints_path(
        self, sample_png: Path, capsys
    ):
        from image_reviewer.cli import main
        from image_reviewer.server import ViewerResult

        result = ViewerResult(
            action="accept", annotated_path="/tmp/annotated.png"
        )
        with patch("image_reviewer.cli.run_serve_mode", return_value=result):
            exit_code = main(["--serve", str(sample_png)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "/tmp/annotated.png" in captured.out

    def test_reject_with_annotated_path_returns_1_and_prints_path(
        self, sample_png: Path, capsys
    ):
        from image_reviewer.cli import main
        from image_reviewer.server import ViewerResult

        result = ViewerResult(
            action="reject", annotated_path="/tmp/annotated.png"
        )
        with patch("image_reviewer.cli.run_serve_mode", return_value=result):
            exit_code = main(["--serve", str(sample_png)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "/tmp/annotated.png" in captured.out
