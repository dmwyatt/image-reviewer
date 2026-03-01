# image-reviewer

Desktop image review and annotation tool. Users load an image, optionally annotate it (draw, rectangles, arrows, text), and accept or reject it. Exits with code 0 (accept) or 1 (reject), printing the annotated image path to stdout if annotations were saved.

## Architecture

- `cli.py` — CLI entry point, argument parsing, orchestration
- `server.py` — HTTP server serving the review UI, handles accept/reject POST endpoints
- `viewer.py` — Native window mode via pywebview (wraps the same HTTP server)
- `image_io.py` — Image loading, MIME detection, base64 encoding, annotated image saving
- `output.py` — Logging utilities
- `assets/app.html` — Complete frontend UI (vanilla JS + Fabric.js canvas)
- `assets/fabric.min.js` — Bundled Fabric.js library

## Dual UI modes

- **Native** (default): pywebview window via GTK/WebKit
- **Serve** (`--serve`): Opens in system browser, same HTML UI

Both modes use the same HTTP server and JavaScript frontend. The JS auto-detects whether `pywebview.api` is available and falls back to HTTP POST.

## Testing

```bash
uv run pytest                    # Unit + integration tests
uv run pytest tests/test_ui.py   # Playwright end-to-end tests (requires playwright browsers)
```

## Skill

The Claude Code skill at `.claude/skills/image-reviewer/SKILL.md` teaches agents how to use this tool to get human image review feedback. When the CLI interface, exit codes, or annotation behavior changes, update the skill to match.
