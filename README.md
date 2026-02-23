# Favicon tool

One Python script: drop image or SVG files in **this folder**, run it, then open **`favicon-tester.html`** in the browser. One row per asset (4 sizes: 16 → 32 → 48 → 64); scroll as you add more.

**Delete:** If you open the HTML by double-clicking (file://), Delete only removes the row and copies a command — paste it in a terminal to delete the file. To have Delete **remove the file from disk** when you click it, run **`python3 favicon_tool.py --serve`** and open **http://127.0.0.1:8765/favicon-tester.html** in the browser.

## Usage

```bash
python3 favicon_tool.py              # Generate favicon-tester.html
python3 favicon_tool.py --check      # Only regenerate if source is newer
python3 favicon_tool.py --force      # Regenerate all
python3 favicon_tool.py --clean      # Remove only -16x16/-32x32
python3 favicon_tool.py --clean-all  # Remove all favicon-* assets
python3 favicon_tool.py --delete F   # Delete one asset, then regenerate
python3 favicon_tool.py --serve      # Generate, then serve at http://127.0.0.1:8765 — Delete removes files
```

## What it does

1. **Names** – Files not starting with `favicon-` are renamed to `favicon-test-01`, `favicon-test-02`, etc.
2. **Generates** – For each raster (png/jpg/webp), creates `-16x16.png` and `-32x32.png`. SVG is shown as-is (no resize).
3. **HTML** – Writes `favicon-tester.html` with one row per asset and “Use as tab” / “Download” / “Delete”.

## Requirements

**Pillow** (`pip install Pillow`) for resizing. If missing, the script tries ImageMagick (`magick`) or GraphicsMagick (`gm`).
