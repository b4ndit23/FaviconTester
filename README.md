# Favicon tool

Drop image files into this directory, then run the script. The HTML opens with one row per asset and all previews.

## Usage

```bash
./run.sh           # Full run: rename non-favicon-* files, generate 16×16 & 32×32, refresh HTML
./run.sh --check  # Quick refresh: only regenerate if source is newer than generated files
./run.sh --force  # Regenerate all sizes and HTML regardless of timestamps
```

## What the script does

1. **Names** – Any image that doesn’t start with `favicon-` is renamed to `favicon-test-01.png` (or `.jpg` etc.). If that exists, `favicon-test-02.png`, and so on.
2. **Generates** – For each `favicon-*.png` (or jpg/webp), creates `favicon-<name>-16x16.png` and `favicon-<name>-32x32.png` in the same folder.
3. **HTML** – Writes `favicon-tester.html` with one row per asset (tab size, 32×32, Use as tab, Download 16×16/32×32). Open that file in a browser to compare.

## Requirements

ImageMagick (`magick`) or GraphicsMagick (`gm`) for resizing.
