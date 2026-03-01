# image-reviewer

Human-in-the-loop image review for AI coding agents. When an agent like [Claude Code](https://docs.anthropic.com/en/docs/claude-code) generates a screenshot, UI mockup, chart, or any visual artifact, it can shell out to `image-reviewer` to pause and ask you — the human — whether the result looks right. You can annotate directly on the image (draw, rectangles, arrows, text) to show the agent exactly what needs fixing, then accept or reject.

The agent gets a clear signal back: exit code `0` (accept) or `1` (reject), plus the path to your annotated image on stdout. No copy-pasting descriptions of what's wrong — just circle it.

![Review UI — image loaded for review with toolbar, color palette, and accept/reject controls](https://bloopityseven.fly.dev/dc291fae-2da3-412e-8c45-abc315a9b960.png)

![Annotation tools in action — rectangle, arrow, and text annotations on an image](https://bloopityseven.fly.dev/e78e537f-82fe-4f52-bc43-4f1bd87b56ce.png)

### How it fits into an agent workflow

1. Agent generates or captures an image (screenshot, plot, UI render, etc.)
2. Agent runs `image-reviewer <image>` — this blocks and opens a window for you
3. You inspect the image, optionally annotate what's wrong (or what looks good)
4. You click **Accept** or **Reject**
5. Agent reads the exit code and annotated image, then decides what to do next

A [Claude Code skill](#claude-code-skill) is included so agents already know how to use this tool out of the box.

## Installation

Requires Python 3.14+.

```bash
uv tool install git+https://github.com/dmwyatt/image-reviewer.git
```

For native window mode (default), you also need GTK and WebKit libraries. On Ubuntu/Debian:

```bash
sudo apt install gir1.2-webkit2-4.1 libgirepository1.0-dev
```

If native dependencies aren't available, use `--serve` mode to open the UI in your browser instead.

## Usage

```bash
image-reviewer <image-path> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `-o, --output PATH` | Output path for annotated image (default: `<name>_annotated.<ext>` next to the original) |
| `--serve` | Open UI in system browser instead of native window |
| `--port PORT` | Port for the HTTP server (default: random available port) |

### Examples

```bash
# Review an image in a native window
image-reviewer screenshot.png

# Review in browser mode
image-reviewer screenshot.png --serve

# Specify where to save annotations
image-reviewer mockup.png -o mockup_reviewed.png

# Script integration
annotated_path=$(image-reviewer screenshot.png -o annotated.png)
exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "Accepted"
else
  echo "Rejected"
fi

# annotated_path is non-empty if the user drew annotations
if [ -n "$annotated_path" ]; then
  echo "Annotations saved to: $annotated_path"
fi
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | User accepted the image |
| `1` | User rejected the image |
| `2` | Validation error (file not found, unsupported format) |

### stdout

If the user added annotations, the path to the saved annotated image is printed to stdout. If no annotations were made, stdout is empty. Annotations are orthogonal to accept/reject — you can reject with annotations marking what's wrong, or accept with annotations adding notes.

## Annotation tools

| Tool | Shortcut | Description |
|------|----------|-------------|
| Select | `V` | Select and move annotations |
| Draw | `D` | Freehand drawing |
| Rectangle | `R` | Draw rectangles to outline regions |
| Arrow | `A` | Draw arrows pointing at areas of interest |
| Text | `T` | Place text labels |
| Undo | `Ctrl+Z` | Undo last action |
| Delete | `Del` | Delete selected annotation |
| Fit | `F` | Zoom image to fit the window |
| Actual size | `1` | Zoom to 100% |
| Reject | `Esc` | Reject and close |
| Accept | `Enter` | Accept and close |

Color and line thickness controls are available in the toolbar.

## Supported formats

PNG, JPEG, GIF, WebP.

## Dual UI modes

- **Native** (default) — Opens a pywebview window using GTK/WebKit. Integrated native feel, no browser needed.
- **Serve** (`--serve`) — Opens the same UI in your system browser. Falls back gracefully when native dependencies are unavailable. Server binds to `127.0.0.1` only.

Both modes use the same HTML/JS frontend and HTTP server internally.

## Claude Code skill

The project ships a skill file at `.claude/skills/image-reviewer/SKILL.md`. When this skill is loaded, Claude Code already knows how to install the tool, invoke it, handle native/serve fallback, and interpret the exit code and annotated image — no manual prompting needed.

## Development

```bash
# Clone and install
git clone https://github.com/dmwyatt/image-reviewer.git
cd image-reviewer
uv sync

# Run tests
uv run pytest                    # Unit + integration tests
uv run pytest tests/test_ui.py   # Playwright E2E tests (requires playwright browsers)
```

## License

MIT
