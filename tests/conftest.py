import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def sample_png(tmp_dir: Path) -> Path:
    """Create a minimal valid PNG file for testing."""
    # Minimal 1x1 white PNG
    import base64

    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
        "2mP8/58BAwAI/AL+hc2rNAAAAABJRU5ErkJggg=="
    )
    path = tmp_dir / "test.png"
    path.write_bytes(png_data)
    return path


@pytest.fixture
def sample_jpeg(tmp_dir: Path) -> Path:
    """Create a minimal valid JPEG file for testing."""
    import base64

    jpeg_data = base64.b64decode(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgF"
        "BQQEBQoHBwYIDAoMCwsKCwsKDA0QDAsNEA0QCg4RTw8OERYSEhMWFxcX"
        "GBYYGBb/2wBDAQMEBAUEBQkFBQkWDQsNFhYWFhYWFhYWFhYWFhYWFhYW"
        "FhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhb/wAARCAABAAED"
        "ASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAA"
        "AAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAA"
        "AAAAAAAAAAA//aAAwDAQACEQMRAD8AKwA//9k="
    )
    path = tmp_dir / "test.jpg"
    path.write_bytes(jpeg_data)
    return path
