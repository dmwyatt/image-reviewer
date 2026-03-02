"""Playwright tests for the image-reviewer UI via --serve mode."""

import re
import shutil
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from image_reviewer.server import run_server


def _create_test_png(directory: Path, width: int = 200, height: int = 200) -> Path:
    """Create a solid red PNG of the given dimensions for UI testing."""
    import struct
    import zlib

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + chunk + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b"IHDR", ihdr_data)

    # Red pixel rows
    raw_data = b""
    for _ in range(height):
        raw_data += b"\x00"  # filter byte
        raw_data += b"\xff\x00\x00" * width  # RGB red

    idat = make_chunk(b"IDAT", zlib.compress(raw_data))
    iend = make_chunk(b"IEND", b"")

    png_data = signature + ihdr + idat + iend
    path = directory / "test_ui.png"
    path.write_bytes(png_data)
    return path


@pytest.fixture
def ui_tmp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def ui_server(ui_tmp_dir: Path):
    """Start the server with a test image and return (port, state, output_path)."""
    image_path = _create_test_png(ui_tmp_dir)
    output_path = ui_tmp_dir / "annotated.png"
    server, port, state = run_server(image_path, output_path)
    yield port, state, output_path
    server.shutdown()


@pytest.fixture
def ui_page(page: Page, ui_server):
    """Navigate to the UI server and wait for canvas to load."""
    port, state, output_path = ui_server
    page.goto(f"http://127.0.0.1:{port}/")
    # Wait for canvas to be ready
    page.wait_for_selector("#canvas")
    page.wait_for_timeout(500)  # let Fabric.js initialize
    return page, state, output_path, port


class TestToolSwitching:
    def test_select_tool_active_by_default(self, ui_page):
        page, *_ = ui_page
        btn = page.locator('[data-tool="select"]')
        expect(btn).to_have_class(re.compile(r"active"))

    def test_switch_to_draw_tool(self, ui_page):
        page, *_ = ui_page
        page.click('[data-tool="draw"]')
        btn = page.locator('[data-tool="draw"]')
        expect(btn).to_have_class(re.compile(r"active"))
        # Select should no longer be active
        select_btn = page.locator('[data-tool="select"]')
        expect(select_btn).not_to_have_class(re.compile(r"active"))

    def test_switch_tools_via_keyboard(self, ui_page):
        page, *_ = ui_page
        page.keyboard.press("d")
        expect(page.locator('[data-tool="draw"]')).to_have_class(re.compile(r"active"))
        page.keyboard.press("r")
        expect(page.locator('[data-tool="rectangle"]')).to_have_class(re.compile(r"active"))
        page.keyboard.press("a")
        expect(page.locator('[data-tool="arrow"]')).to_have_class(re.compile(r"active"))
        page.keyboard.press("t")
        expect(page.locator('[data-tool="text"]')).to_have_class(re.compile(r"active"))
        page.keyboard.press("v")
        expect(page.locator('[data-tool="select"]')).to_have_class(re.compile(r"active"))


class TestAcceptReject:
    def test_accept_button(self, ui_page):
        page, state, _, _ = ui_page
        page.click("#btn-accept")
        page.wait_for_timeout(300)
        assert state.result.action == "accept"
        assert state.done_event.is_set()

    def test_reject_button(self, ui_page):
        page, state, _, _ = ui_page
        page.click("#btn-reject")
        page.wait_for_timeout(300)
        assert state.result.action == "reject"
        assert state.done_event.is_set()

    def test_accept_keyboard(self, ui_page):
        page, state, _, _ = ui_page
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        assert state.result.action == "accept"

    def test_reject_keyboard(self, ui_page):
        page, state, _, _ = ui_page
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        assert state.result.action == "reject"


class TestAnnotationAutoSave:
    def _draw_annotation(self, page):
        """Draw a freehand annotation on the canvas."""
        page.click('[data-tool="draw"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 30, cy)
        page.mouse.down()
        page.mouse.move(cx + 30, cy, steps=5)
        page.mouse.up()
        page.wait_for_timeout(300)

    def test_accept_with_annotation_saves_file(self, ui_page):
        page, state, output_path, _ = ui_page
        self._draw_annotation(page)
        page.click("#btn-accept")
        page.wait_for_timeout(500)
        assert state.result.action == "accept"
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_reject_with_annotation_saves_file(self, ui_page):
        page, state, output_path, _ = ui_page
        self._draw_annotation(page)
        page.click("#btn-reject")
        page.wait_for_timeout(500)
        assert state.result.action == "reject"
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_accept_without_annotation_no_file(self, ui_page):
        page, state, output_path, _ = ui_page
        page.click("#btn-accept")
        page.wait_for_timeout(500)
        assert state.result.action == "accept"
        assert not output_path.exists()


class TestAnnotations:
    def test_freehand_draw(self, ui_page):
        page, state, _, _ = ui_page
        page.click('[data-tool="draw"]')
        # Draw on the canvas
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 30, cy)
        page.mouse.down()
        page.mouse.move(cx + 30, cy, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)

    def test_rectangle_draw(self, ui_page):
        page, state, _, _ = ui_page
        page.click('[data-tool="rectangle"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 40, cy - 40)
        page.mouse.down()
        page.mouse.move(cx + 40, cy + 40, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)

    def test_arrow_draw(self, ui_page):
        page, state, _, _ = ui_page
        page.click('[data-tool="arrow"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 50, cy)
        page.mouse.down()
        page.mouse.move(cx + 50, cy, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)

    def test_text_tool(self, ui_page):
        page, state, _, _ = ui_page
        page.click('[data-tool="text"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.click(cx, cy)
        page.wait_for_timeout(300)
        page.keyboard.type("Hello")
        page.wait_for_timeout(200)

    def test_text_tool_space_continues_editing(self, ui_page):
        """Pressing space while editing text should insert a space, not exit editing.

        Regression test: space keyup was calling setActiveTool() which ran
        discardActiveObject(), kicking the user out of text editing mode.
        """
        page, state, _, _ = ui_page
        page.click('[data-tool="text"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.click(cx, cy)
        page.wait_for_timeout(300)
        # Fabric.js creates a hidden textarea for IText editing
        textarea = page.locator("textarea")
        expect(textarea).to_have_count(1)
        # Use individual key presses (closer to real user behavior)
        page.keyboard.type("Hello")
        page.keyboard.down("Space")
        page.wait_for_timeout(50)
        page.keyboard.up("Space")
        page.wait_for_timeout(100)
        # The textarea should still exist and be focused (still in editing mode)
        expect(textarea).to_have_count(1)
        is_focused = page.evaluate(
            "() => document.activeElement === document.querySelector('textarea')"
        )
        assert is_focused, "Textarea lost focus after pressing space"
        page.keyboard.type("World")
        page.wait_for_timeout(200)
        # Verify the textarea contains the full text including the space
        assert textarea.input_value() == "Hello World"


class TestZoom:
    def test_zoom_display_shows_percentage(self, ui_page):
        page, *_ = ui_page
        zoom_display = page.locator("#zoom-display")
        text = zoom_display.text_content()
        assert "%" in text

    def test_fit_button(self, ui_page):
        page, *_ = ui_page
        page.click("#btn-fit")
        page.wait_for_timeout(200)
        text = page.locator("#zoom-display").text_content()
        assert "%" in text

    def test_actual_size_button(self, ui_page):
        page, *_ = ui_page
        page.click("#btn-actual")
        page.wait_for_timeout(200)
        text = page.locator("#zoom-display").text_content()
        assert text == "100%"


class TestColorSwitching:
    def test_color_swatches_exist(self, ui_page):
        page, *_ = ui_page
        swatches = page.locator(".color-swatch")
        assert swatches.count() == 8

    def test_click_color_swatch(self, ui_page):
        page, *_ = ui_page
        # Click second color
        swatches = page.locator(".color-swatch")
        swatches.nth(1).click()
        expect(swatches.nth(1)).to_have_class(re.compile(r"active"))
        expect(swatches.nth(0)).not_to_have_class(re.compile(r"active"))


class TestUndo:
    def test_undo_button(self, ui_page):
        page, *_ = ui_page
        # Draw something then undo
        page.click('[data-tool="draw"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 30, cy)
        page.mouse.down()
        page.mouse.move(cx + 30, cy, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)
        page.click("#btn-undo")
        page.wait_for_timeout(200)

    def test_undo_keyboard(self, ui_page):
        page, *_ = ui_page
        page.click('[data-tool="draw"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 30, cy)
        page.mouse.down()
        page.mouse.move(cx + 30, cy, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)
        page.keyboard.press("Control+z")
        page.wait_for_timeout(200)


@pytest.fixture
def large_image_server(ui_tmp_dir: Path):
    """Start the server with a large (2000x1500) test image."""
    image_path = _create_test_png(ui_tmp_dir, width=2000, height=1500)
    output_path = ui_tmp_dir / "annotated.png"
    server, port, state = run_server(image_path, output_path)
    yield port, state, output_path
    server.shutdown()


@pytest.fixture
def large_image_page(page: Page, large_image_server):
    """Navigate to the UI server with a large image and wait for canvas."""
    port, state, output_path = large_image_server
    page.goto(f"http://127.0.0.1:{port}/")
    page.wait_for_selector("#canvas")
    page.wait_for_timeout(500)
    return page, state, output_path, port


class TestAnnotationScaling:
    def test_text_font_size_scales_with_image_size(self, large_image_page):
        page, *_ = large_image_page
        page.click('[data-tool="text"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.click(cx, cy)
        page.wait_for_timeout(300)

        # The base fontSize at thickness=4 would be 16 + 4*2 = 24.
        # With a 2000px image, scale = 2000/1000 = 2, so fontSize = 24*2 = 48.
        font_size = page.evaluate(
            "() => document.querySelector('#canvas')"
            ".__fabric_canvas.getObjects().find(o => o.type === 'i-text').fontSize"
        )
        base_font_size = 16 + 4 * 2  # 24 at default thickness=4
        assert font_size > base_font_size

    def test_rectangle_stroke_width_scales(self, large_image_page):
        page, *_ = large_image_page
        page.click('[data-tool="rectangle"]')
        canvas = page.locator("#canvas-container")
        box = canvas.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 40, cy - 40)
        page.mouse.down()
        page.mouse.move(cx + 40, cy + 40, steps=5)
        page.mouse.up()
        page.wait_for_timeout(300)

        # Default thickness = 4, scale = 2000/1000 = 2, so strokeWidth = 8
        stroke_width = page.evaluate(
            "() => document.querySelector('#canvas')"
            ".__fabric_canvas.getObjects().find(o => o.type === 'rect').strokeWidth"
        )
        base_thickness = 4  # default
        assert stroke_width > base_thickness

    def test_freehand_brush_width_scales(self, large_image_page):
        page, *_ = large_image_page
        page.click('[data-tool="draw"]')
        page.wait_for_timeout(100)

        # Default thickness = 4, scale = 2000/1000 = 2, so brush width = 8
        brush_width = page.evaluate(
            "() => document.querySelector('#canvas').__fabric_canvas.freeDrawingBrush.width"
        )
        base_thickness = 4  # default
        assert brush_width > base_thickness
