import base64
from pathlib import Path

import pytest

from image_reviewer.image_io import (
    detect_mime_type,
    encode_image_to_data_url,
    save_annotated_image,
)


class TestDetectMimeType:
    def test_png(self, sample_png: Path):
        assert detect_mime_type(sample_png) == "image/png"

    def test_jpeg(self, sample_jpeg: Path):
        assert detect_mime_type(sample_jpeg) == "image/jpeg"

    def test_jpg_extension(self, tmp_dir: Path):
        path = tmp_dir / "test.jpg"
        path.write_bytes(b"\xff\xd8\xff")
        assert detect_mime_type(path) == "image/jpeg"

    def test_unsupported_format(self, tmp_dir: Path):
        path = tmp_dir / "test.bmp"
        path.write_bytes(b"BM")
        with pytest.raises(ValueError, match="Unsupported image format"):
            detect_mime_type(path)

    def test_unknown_extension(self, tmp_dir: Path):
        path = tmp_dir / "test.xyz"
        path.write_bytes(b"data")
        with pytest.raises(ValueError, match="Unsupported image format"):
            detect_mime_type(path)


class TestEncodeImageToDataUrl:
    def test_png_encoding(self, sample_png: Path):
        result = encode_image_to_data_url(sample_png)
        assert result.startswith("data:image/png;base64,")
        # Verify the base64 portion decodes back to the original bytes
        b64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        assert decoded == sample_png.read_bytes()

    def test_jpeg_encoding(self, sample_jpeg: Path):
        result = encode_image_to_data_url(sample_jpeg)
        assert result.startswith("data:image/jpeg;base64,")

    def test_nonexistent_file(self, tmp_dir: Path):
        path = tmp_dir / "nonexistent.png"
        with pytest.raises(FileNotFoundError):
            encode_image_to_data_url(path)


class TestSaveAnnotatedImage:
    def test_saves_png_from_data_url(self, tmp_dir: Path):
        # Create a data URL from a known PNG
        import base64 as b64mod

        png_bytes = b64mod.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "2mP8/58BAwAI/AL+hc2rNAAAAABJRU5ErkJggg=="
        )
        data_url = "data:image/png;base64," + b64mod.b64encode(png_bytes).decode()
        output_path = tmp_dir / "output.png"

        save_annotated_image(data_url, output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == png_bytes

    def test_saves_raw_base64(self, tmp_dir: Path):
        """Should handle raw base64 without data URL prefix."""
        import base64 as b64mod

        png_bytes = b64mod.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "2mP8/58BAwAI/AL+hc2rNAAAAABJRU5ErkJggg=="
        )
        raw_b64 = b64mod.b64encode(png_bytes).decode()
        output_path = tmp_dir / "output.png"

        save_annotated_image(raw_b64, output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == png_bytes

    def test_creates_parent_directories(self, tmp_dir: Path):
        import base64 as b64mod

        png_bytes = b64mod.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "2mP8/58BAwAI/AL+hc2rNAAAAABJRU5ErkJggg=="
        )
        data_url = "data:image/png;base64," + b64mod.b64encode(png_bytes).decode()
        output_path = tmp_dir / "subdir" / "output.png"

        save_annotated_image(data_url, output_path)

        assert output_path.exists()
