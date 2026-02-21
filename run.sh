#!/usr/bin/env bash
# Favicon tool: normalize names, generate 16×16/32×32, refresh HTML.
# Usage: ./run.sh [--check] [--force] [--clean] [--clean-all]
#   --check     Only regenerate if source is newer than generated files (quick refresh).
#   --force     Regenerate all sizes and HTML regardless of timestamps.
#   --clean     Remove only generated files (-16x16.png, -32x32.png). Keeps source assets.
#   --clean-all Remove all favicon-* images (sources + generated). Empty the assets folder.
# Drop images into this directory (with or without "favicon-" prefix), then run.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FORCE=false
CHECK=false
CLEAN=false
CLEAN_ALL=false
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --check) CHECK=true ;;
    --clean) CLEAN=true ;;
    --clean-all) CLEAN_ALL=true ;;
  esac
done

# Cleanup only, then exit
if [[ "$CLEAN_ALL" == true ]]; then
  echo "Removing all favicon assets and generated files..."
  for ext in png jpg jpeg webp; do
    for f in favicon-*."$ext"; do
      [[ -f "$f" ]] || continue
      rm -v "$f"
    done
  done
  for f in *-16x16.png *-32x32.png; do
    [[ -f "$f" ]] && rm -v "$f"
  done
  [[ -f "favicon-tester.html" ]] && rm -v "favicon-tester.html"
  echo "Done. Folder has no assets. Add images and run ./run.sh again."
  exit 0
fi

if [[ "$CLEAN" == true ]]; then
  echo "Removing generated files (-16x16.png, -32x32.png)..."
  for f in *-16x16.png *-32x32.png; do
    [[ -f "$f" ]] || continue
    rm -v "$f"
  done
  echo "Done. Run ./run.sh to regenerate."
  exit 0
fi

# Image extensions we process
EXTS="png jpg jpeg webp"
# Files we never treat as source assets (our outputs and tool files)
SKIP_PATTERN='-16x16\.|-32x32\.|favicon-tester\.|\.template\.|run\.sh|README'

# Resize helper: $1=source, $2=width, $3=height, $4=output
resize() {
  local src="$1" w="$2" h="$3" out="$4"
  if command -v magick &>/dev/null; then
    magick "$src" -resize "${w}x${h}" "$out"
  elif command -v convert &>/dev/null; then
    convert "$src" -resize "${w}x${h}" "$out"
  elif command -v gm &>/dev/null; then
    gm convert "$src" -resize "${w}x${h}" "$out"
  else
    echo "Need ImageMagick (magick) or GraphicsMagick (gm)." >&2
    exit 1
  fi
}

# 1) Collect image files that are not already generated or tool files
SOURCES=()
for ext in $EXTS; do
  for f in *."$ext"; do
    [[ -f "$f" ]] || continue
    [[ "$f" =~ $SKIP_PATTERN ]] && continue
    SOURCES+=("$f")
  done
done

# 2) Rename any that don't start with "favicon-" to favicon-test-NN.ext
for f in "${SOURCES[@]}"; do
  if [[ "$f" != favicon-* ]]; then
    ext="${f##*.}"
    n=1
    while [[ -f "favicon-test-$(printf '%02d' $n).$ext" ]]; do ((n++)); done
    newname="favicon-test-$(printf '%02d' $n).$ext"
    mv -n "$f" "$newname" 2>/dev/null || true
  fi
done

# Re-collect source list after renames (only favicon-* sources now)
SOURCES=()
for ext in $EXTS; do
  for f in favicon-*."$ext"; do
    [[ -f "$f" ]] || continue
    [[ "$f" =~ -16x16\.|-32x32\. ]] && continue
    SOURCES+=("$f")
  done
done

# Sort so order is stable
SOURCES=($(printf '%s\n' "${SOURCES[@]}" | sort -u))

# 3) For each source, generate -16x16 and -32x32 (unless --check and up to date)
BASE_NAMES=()
for src in "${SOURCES[@]}"; do
  base="${src%.*}"
  ext="${src##*.}"
  out16="${base}-16x16.png"
  out32="${base}-32x32.png"
  BASE_NAMES+=("$base")
  need16=true
  need32=true
  if [[ "$CHECK" == true && "$FORCE" != true ]]; then
    [[ -f "$out16" && "$src" -ot "$out16" ]] && need16=false
    [[ -f "$out32" && "$src" -ot "$out32" ]] && need32=false
  fi
  if [[ "$FORCE" == true ]]; then
    need16=true
    need32=true
  fi
  if [[ "$need16" == true ]]; then
    resize "$src" 16 16 "$out16"
    echo "  $out16"
  fi
  if [[ "$need32" == true ]]; then
    resize "$src" 32 32 "$out32"
    echo "  $out32"
  fi
done

# 4) Build HTML: inject asset rows into template
TEMPLATE="favicon-tester.template.html"
OUT_HTML="favicon-tester.html"
if [[ ! -f "$TEMPLATE" ]]; then
  echo "Missing $TEMPLATE in $SCRIPT_DIR" >&2
  exit 1
fi

# First asset's 16 and 32 for default tab icon
FIRST_16=""
FIRST_32=""
[[ ${#BASE_NAMES[@]} -gt 0 ]] && { FIRST_16="${BASE_NAMES[0]}-16x16.png"; FIRST_32="${BASE_NAMES[0]}-32x32.png"; }

# Build one row per asset: name + 4 sizes (16 → 32 → 48 → 64) in order, then actions
ASSET_ROWS=""
for base in "${BASE_NAMES[@]}"; do
  src="${base}.png"
  for ext in $EXTS; do
    [[ -f "${base}.${ext}" ]] && src="${base}.${ext}" && break
  done
  out16="${base}-16x16.png"
  out32="${base}-32x32.png"
  ASSET_ROWS+="
            <div class=\"asset-row\" data-asset-src=\"$src\">
                <span class=\"asset-name\">$src</span>
                <div class=\"sizes\">
                    <div class=\"size-cell\"><span class=\"label\">16</span><img src=\"$out16\" alt=\"\" width=\"16\" height=\"16\"></div>
                    <div class=\"size-cell\"><span class=\"label\">32</span><img src=\"$out32\" alt=\"\" width=\"32\" height=\"32\"></div>
                    <div class=\"size-cell\"><span class=\"label\">48</span><img src=\"$out32\" alt=\"\" width=\"48\" height=\"48\"></div>
                    <div class=\"size-cell\"><span class=\"label\">64</span><img src=\"$src\" alt=\"\" width=\"64\" height=\"64\"></div>
                </div>
                <div class=\"actions\">
                    <button type=\"button\" class=\"use-tab\">Use as tab</button>
                    <button type=\"button\" class=\"dl dl-16\">Download 16×16</button>
                    <button type=\"button\" class=\"dl dl-32\">Download 32×32</button>
                </div>
            </div>"
done

# "Add another" row (file input)
ASSET_ROWS+="
            <div class=\"asset-row\" data-asset-file>
                <span class=\"asset-name\">Add another (choose file)</span>
                <input type=\"file\" accept=\"image/*\" class=\"third-file\" style=\"font-size: 0.75rem;\">
                <div class=\"sizes\">
                    <div class=\"size-cell\"><span class=\"label\">16</span><img alt=\"\" width=\"16\" height=\"16\"></div>
                    <div class=\"size-cell\"><span class=\"label\">32</span><img alt=\"\" width=\"32\" height=\"32\"></div>
                    <div class=\"size-cell\"><span class=\"label\">48</span><img alt=\"\" width=\"48\" height=\"48\"></div>
                    <div class=\"size-cell\"><span class=\"label\">64</span><img alt=\"\" width=\"64\" height=\"64\"></div>
                </div>
                <div class=\"actions\">
                    <button type=\"button\" class=\"use-tab\" disabled>Use as tab</button>
                    <button type=\"button\" class=\"dl dl-16\" disabled>Download 16×16</button>
                    <button type=\"button\" class=\"dl dl-32\" disabled>Download 32×32</button>
                </div>
            </div>"

# Default tab icon: use first asset's 16/32 if we have any
DEFAULT_16="favicon.ico"
DEFAULT_32="favicon.ico"
[[ -n "$FIRST_16" ]] && DEFAULT_16="$FIRST_16"
[[ -n "$FIRST_32" ]] && DEFAULT_32="$FIRST_32"

ROWS_FILE=$(mktemp)
trap "rm -f '$ROWS_FILE'" EXIT
echo "$ASSET_ROWS" > "$ROWS_FILE"

# Inject: replace __ASSET_ROWS__ with file contents; __FIRST_ICON_16__ / __FIRST_ICON_32__ in template
awk -v first16="$DEFAULT_16" -v first32="$DEFAULT_32" -v rowsfile="$ROWS_FILE" '
  /__ASSET_ROWS__/ {
    while ((getline line < rowsfile) > 0) print line
    close(rowsfile)
    next
  }
  { gsub(/__FIRST_ICON_16__/, first16); gsub(/__FIRST_ICON_32__/, first32); print }
' "$TEMPLATE" > "$OUT_HTML"

echo "Done. Open this file in your browser (${#BASE_NAMES[@]} assets):"
echo "  $SCRIPT_DIR/$OUT_HTML"
