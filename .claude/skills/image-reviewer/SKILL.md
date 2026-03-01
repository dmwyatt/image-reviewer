---
name: image-reviewer
description: Present an image to the user for visual review, approval, or rejection with optional annotations. Use when you need human feedback on an image — screenshots, generated outputs, UI mockups, before/after comparisons, or any visual artifact where user judgment matters. Triggers include needing to verify an image looks correct, asking the user to approve or reject a visual result, or getting annotated feedback on an image.
---

# Image Reviewer

Launch an interactive image review UI where the user can inspect an image, optionally annotate it (draw, rectangles, arrows, text), and accept or reject it.

## Installation

If `image-reviewer` is not on PATH, install it as a uv tool:

```bash
uv tool install git+https://github.com/dmwyatt/image-reviewer.git
```

## Invocation

```bash
image-reviewer --serve <path-to-image> -o <output-path>
```

- `--serve` is required (opens in browser; native window mode cannot be used headlessly)
- `-o` sets where the annotated image is saved (default: `<stem>_annotated<suffix>` next to the original)
- Supported formats: PNG, JPEG, GIF, WebP

## Interpreting Results

- **Exit code 0**: User accepted the image
- **Exit code 1**: User rejected the image
- **stdout**: If the user added annotations, the path to the saved annotated image is printed. If no annotations were made, stdout is empty.

Annotations are orthogonal to accept/reject — the user may reject with annotations (marking what's wrong) or accept with annotations (adding notes).

## Workflow

1. Run `image-reviewer --serve <image>` (blocks until the user acts)
2. Check the exit code to determine accept/reject
3. If stdout is non-empty, read the annotated image path for further use
4. React to the result — retry, proceed, or adjust based on the user's decision

## Example

```bash
# Launch review and capture result
image-reviewer --serve screenshot.png -o screenshot_annotated.png
exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "Accepted"
else
  echo "Rejected"
fi
```

## Annotation Tools Available to the User

The user can annotate before accepting or rejecting:
- **Freehand draw** (D) — sketch directly on the image
- **Rectangle** (R) — outline regions
- **Arrow** (A) — point at specific areas
- **Text** (T) — add text labels
- **Undo** (Ctrl+Z), **Delete** (Del), **Zoom** (scroll wheel)

## Notes

- The server binds to `127.0.0.1` only — local use only
- The browser opens automatically when the server starts
- The command blocks until the user clicks Accept or Reject
