# Favicon tool

Drop image files into **this directory**, run the script, then open **`favicon-tester.html`** (the one in this folder) in your browser. You get one row per asset with four size previews (16 → 32 → 48 → 64); scroll down as you add more.

## Usage

```bash
./run.sh            # Full run: rename non-favicon-* files, generate 16×16 & 32×32, refresh HTML
./run.sh --check    # Quick refresh: only regenerate if source is newer than generated files
./run.sh --force    # Regenerate all sizes and HTML regardless of timestamps
./run.sh --clean    # Remove only generated files (-16x16, -32x32). Keeps source assets.
./run.sh --clean-all # Remove all favicon-* images (sources + generated). Empty the folder.
```

## What the script does

1. **Names** – Any image that doesn’t start with `favicon-` is renamed to `favicon-test-01.png` (or `.jpg` etc.). If that exists, `favicon-test-02.png`, and so on.
2. **Generates** – For each `favicon-*.png` (or jpg/webp), creates `favicon-<name>-16x16.png` and `favicon-<name>-32x32.png` in the same folder.
3. **HTML** – Writes `favicon-tester.html` with one row per asset (4 sizes: 16, 32, 48, 64 px), plus “Use as tab” and “Download 16×16” / “Download 32×32”. Open **this folder’s** `favicon-tester.html` in the browser (not a copy in another directory).

## Requirements

ImageMagick (`magick`) or GraphicsMagick (`gm`) for resizing.
