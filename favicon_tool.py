#!/usr/bin/env python3
"""
Favicon tool: one script to generate the tester HTML and (optional) serve it so Delete removes files from disk.
Usage:
  python3 favicon_tool.py              # Generate favicon-tester.html
  python3 favicon_tool.py --check      # Only regenerate if source newer
  python3 favicon_tool.py --force      # Regenerate all
  python3 favicon_tool.py --clean      # Remove only -16x16/-32x32
  python3 favicon_tool.py --clean-all  # Remove all favicon-* assets
  python3 favicon_tool.py --delete F   # Delete one asset, then regenerate
  python3 favicon_tool.py --serve      # Generate, then serve at http://127.0.0.1:8765 (Delete removes files)
Drop images/SVGs in this folder, then run. Open favicon-tester.html (or the URL when using --serve).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

SCRIPT_DIR = Path(__file__).resolve().parent
EXTS = ("png", "jpg", "jpeg", "webp", "svg")
SKIP = re.compile(r"-16x16\.|-32x32\.|favicon-tester\.|\.template\.|run\.sh|README|favicon_tool\.py")
OUT_HTML = "favicon-tester.html"
PORT = 8765

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Favicon Tester</title>
__FIRST_ICON_LINKS__
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2rem; background: #1a1a2e; color: #eaeaea; min-height: 100vh; }
        h1 { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; }
        .sub { color: #888; font-size: 0.9rem; margin-bottom: 2rem; }
        .assets-section { margin-bottom: 2rem; }
        .assets-section h2 { font-size: 0.95rem; font-weight: 600; margin-bottom: 1rem; color: #ccc; }
        .asset-list { display: flex; flex-direction: column; gap: 0; }
        .asset-row { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; background: #16213e; border-bottom: 1px solid #2a2a4a; flex-wrap: wrap; }
        .asset-row:last-of-type { border-bottom: none; }
        .asset-name { font-size: 0.8rem; color: #aaa; min-width: 140px; word-break: break-all; }
        .asset-row .sizes { display: flex; align-items: center; gap: 0.75rem; flex-wrap: nowrap; }
        .asset-row .size-cell { display: flex; flex-direction: column; align-items: center; gap: 0.2rem; background: #0f0f1a; border-radius: 6px; padding: 0.35rem; image-rendering: pixelated; image-rendering: crisp-edges; }
        .asset-row .size-cell .label { font-size: 0.65rem; color: #666; }
        .asset-row .size-cell img { display: block; vertical-align: bottom; }
        .asset-row .actions { display: flex; gap: 0.5rem; margin-left: auto; flex-shrink: 0; }
        .asset-row .actions button { font-size: 0.7rem; padding: 0.3rem 0.5rem; background: #2a2a4a; color: #eaeaea; border: none; border-radius: 6px; cursor: pointer; }
        .asset-row .actions button:hover { background: #3a3a5a; }
        .asset-row .actions button.dl { background: #1a3a2a; }
        .asset-row .actions button.dl:hover { background: #2a4a3a; }
        .asset-row .actions a.dl-svg { font-size: 0.7rem; padding: 0.3rem 0.5rem; background: #1a3a2a; color: #eaeaea; border-radius: 6px; text-decoration: none; }
        .asset-row .actions a.dl-svg:hover { background: #2a4a3a; }
        .asset-row .actions button.btn-delete { font-size: 0.7rem; padding: 0.3rem 0.5rem; background: #4a2a2a; color: #eaeaea; border: none; border-radius: 6px; cursor: pointer; }
        .asset-row .actions button.btn-delete:hover { background: #5a3a3a; }
        .actual-tab-section { margin-bottom: 2rem; padding-top: 1rem; border-top: 1px solid #2a2a4a; }
        .actual-tab-section h2 { font-size: 0.95rem; font-weight: 600; margin-bottom: 0.75rem; color: #ccc; }
        .actual-tab-row { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
        .actual-size-box { width: 16px; height: 16px; flex-shrink: 0; overflow: hidden; background: #0f0f1a; image-rendering: pixelated; image-rendering: crisp-edges; }
        .actual-size-box img { display: block; width: 16px; height: 16px; }
        .zoomed-box { width: 128px; height: 128px; flex-shrink: 0; overflow: hidden; background: #0f0f1a; border-radius: 8px; image-rendering: pixelated; image-rendering: crisp-edges; }
        .zoomed-box img { display: block; width: 128px; height: 128px; }
        .actual-tab-label { font-size: 0.8rem; color: #888; }
        .note { max-width: 560px; font-size: 0.85rem; color: #888; line-height: 1.5; }
    </style>
</head>
<body>
    <h1>Favicon Tester</h1>
    <p class="sub">Drop images in this folder, run <code>python3 favicon_tool.py</code> (or <code>--check</code>). Each row = one asset.</p>
    <section class="assets-section" aria-label="All assets">
        <h2>All assets — one row each, 4 sizes (16 → 32 → 48 → 64). Scroll down as you add more.</h2>
        <div class="asset-list">
__ASSET_ROWS__
        </div>
    </section>
    <section class="actual-tab-section" aria-label="Actual tab size">
        <h2>Exactly as in browser tab (16×16 px)</h2>
        <div class="actual-tab-row">
            <div class="actual-size-box" title="Real tab size"><img id="tab-actual-16" src="__FIRST_ICON_16__" alt="" width="16" height="16"></div>
            <div class="zoomed-box" title="8× zoom"><img id="tab-zoomed-16" src="__FIRST_ICON_16__" alt="" width="128" height="128"></div>
            <span class="actual-tab-label">Left = real tab size · Right = 8× zoom</span>
        </div>
    </section>
    <p class="note">Use "Use as tab" on any asset. "Delete" removes the row and copies the delete command; with <code>--serve</code>, Delete removes the file from disk. Reload after running the script.</p>
    <script>
        var q = '?t=' + Date.now();
        (function () {
            document.querySelectorAll('link[rel="icon"]').forEach(function (link) {
                var h = link.getAttribute('href');
                if (h && h.indexOf('?') === -1) link.setAttribute('href', h + q);
            });
            var tabActual = document.getElementById('tab-actual-16');
            var tabZoomed = document.getElementById('tab-zoomed-16');
            if (tabActual && tabZoomed && tabActual.src && tabActual.src.indexOf('?') === -1) { tabActual.src += q; tabZoomed.src = tabActual.src; }
            document.querySelectorAll('.asset-row[data-asset-src] .size-cell img').forEach(function (img) {
                var s = img.getAttribute('src');
                if (s && s.indexOf('?') === -1) img.setAttribute('src', s + q);
            });
        })();
        function scaleToDataUrl(img, w, h) {
            var c = document.createElement('canvas');
            c.width = w; c.height = h;
            var ctx = c.getContext('2d');
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, 0, 0, w, h);
            return c.toDataURL('image/png');
        }
        function fillRow(row, data16, data32) {
            row._data16 = data16;
            row._data32 = data32;
            row.querySelectorAll('.use-tab, .dl-16, .dl-32').forEach(function (b) { b.disabled = false; });
        }
        function bindRow(row) {
            var useTab = row.querySelector('.use-tab');
            var dl16 = row.querySelector('.dl-16');
            var dl32 = row.querySelector('.dl-32');
            var isSvg = row.getAttribute('data-svg') === 'true';
            if (useTab) useTab.addEventListener('click', function () {
                var href = isSvg ? (row.getAttribute('data-asset-src') + q) : row._data16;
                if (!href) return;
                var link = document.querySelector('link[rel="icon"]') || document.createElement('link');
                link.rel = 'icon';
                link.type = isSvg ? 'image/svg+xml' : 'image/png';
                link.href = href;
                if (!link.parentNode) document.head.appendChild(link);
            });
            if (dl16) dl16.addEventListener('click', function () {
                if (!row._data16) return;
                var a = document.createElement('a');
                a.href = row._data16;
                a.download = 'favicon-16x16.png';
                a.click();
            });
            if (dl32) dl32.addEventListener('click', function () {
                if (!row._data32) return;
                var a = document.createElement('a');
                a.href = row._data32;
                a.download = 'favicon-32x32.png';
                a.click();
            });
            var btnDelete = row.querySelector('.btn-delete');
            if (btnDelete) btnDelete.addEventListener('click', function () {
                var filename = btnDelete.getAttribute('data-filename');
                if (!filename) return;
                var cmd = 'python3 favicon_tool.py --delete ' + filename;
                if (window.__FAVICON_SERVE__) {
                    fetch('/delete?file=' + encodeURIComponent(filename), { method: 'POST' }).then(function (r) {
                        if (r.ok) row.remove();
                        else r.text().then(function (t) { alert('Delete failed: ' + t); });
                    }).catch(function (e) { alert('Delete failed: ' + e.message); });
                } else {
                    row.remove();
                    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(cmd);
                }
            });
        }
        document.querySelectorAll('.asset-row[data-asset-src]').forEach(function (row) {
            bindRow(row);
            if (row.getAttribute('data-svg') === 'true') return;
            var src = row.getAttribute('data-asset-src') + q;
            var img = new Image();
            img.onload = function () { fillRow(row, scaleToDataUrl(img, 16, 16), scaleToDataUrl(img, 32, 32)); };
            img.onerror = function () { row.querySelector('.asset-name').textContent += ' (load failed)'; };
            img.src = src;
        });
        var addRow = document.querySelector('.asset-row[data-asset-file]');
        if (addRow) {
            bindRow(addRow);
            addRow.querySelector('.third-file').addEventListener('change', function () {
                var file = this.files && this.files[0];
                if (!file) return;
                var url = URL.createObjectURL(file);
                var img = new Image();
                img.onload = function () {
                    fillRow(addRow, scaleToDataUrl(img, 16, 16), scaleToDataUrl(img, 32, 32));
                    addRow.querySelector('.asset-name').textContent = file.name;
                    var cells = addRow.querySelectorAll('.size-cell img');
                    var d16 = scaleToDataUrl(img, 16, 16), d32 = scaleToDataUrl(img, 32, 32);
                    if (cells[0]) cells[0].src = d16;
                    if (cells[1]) cells[1].src = d32;
                    if (cells[2]) cells[2].src = d32;
                    if (cells[3]) cells[3].src = scaleToDataUrl(img, 64, 64);
                    URL.revokeObjectURL(url);
                };
                img.onerror = function () { URL.revokeObjectURL(url); };
                img.src = url;
            });
        }
    </script>
</body>
</html>
"""


def collect_sources() -> list[Path]:
    sources = []
    for ext in EXTS:
        for p in SCRIPT_DIR.glob("*." + ext):
            if p.is_file() and not SKIP.search(p.name):
                sources.append(p)
    return sorted(set(sources))


def rename_non_favicon(sources: list[Path]) -> None:
    for p in list(sources):
        if not p.name.startswith("favicon-"):
            ext = p.suffix.lstrip(".")
            n = 1
            while (SCRIPT_DIR / f"favicon-test-{n:02d}.{ext}").exists():
                n += 1
            new_path = SCRIPT_DIR / f"favicon-test-{n:02d}.{ext}"
            p.rename(new_path)


def resize_pil(src: Path, w: int, h: int, out: Path) -> None:
    if Image is None:
        raise SystemExit("Install Pillow: pip install Pillow")
    with Image.open(src) as im:
        im = im.convert("RGBA") if im.mode != "RGBA" else im
        im.resize((w, h), Image.Resampling.NEAREST).save(out, "PNG")


def resize_cli(src: Path, w: int, h: int, out: Path) -> None:
    for cmd in (["magick", str(src), "-resize", f"{w}x{h}", str(out)], ["convert", str(src), "-resize", f"{w}x{h}", str(out)]):
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=SCRIPT_DIR)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise SystemExit("Need ImageMagick (magick) or Pillow (pip install Pillow)")


def resize(src: Path, w: int, h: int, out: Path) -> None:
    try:
        resize_pil(src, w, h, out)
    except Exception:
        resize_cli(src, w, h, out)


def do_delete(filename: str) -> None:
    path = SCRIPT_DIR / filename
    if not path.is_file():
        return
    if ".." in filename or not filename.startswith("favicon-"):
        raise SystemExit("Invalid filename")
    path.unlink()
    base = path.stem
    for suffix in ("-16x16.png", "-32x32.png"):
        p = SCRIPT_DIR / f"{base}{suffix}"
        if p.is_file():
            p.unlink()
    print(f"Deleted {filename}. Regenerating...")


def do_clean_all() -> None:
    for ext in ("png", "jpg", "jpeg", "webp", "svg"):
        for p in SCRIPT_DIR.glob("favicon-*." + ext):
            if p.is_file():
                p.unlink()
                print(f"  removed {p.name}")
    for p in list(SCRIPT_DIR.glob("*-16x16.png")) + list(SCRIPT_DIR.glob("*-32x32.png")):
        if p.is_file():
            p.unlink()
            print(f"  removed {p.name}")
    (SCRIPT_DIR / OUT_HTML).unlink(missing_ok=True)
    print("Done. Add images and run again.")


def do_clean() -> None:
    for p in list(SCRIPT_DIR.glob("*-16x16.png")) + list(SCRIPT_DIR.glob("*-32x32.png")):
        if p.is_file():
            p.unlink()
            print(f"  removed {p.name}")
    print("Done. Run script to regenerate.")


def generate(check: bool, force: bool, inject_serve: bool = False) -> int:
    os.chdir(SCRIPT_DIR)
    sources = collect_sources()
    rename_non_favicon(sources)
    sources = collect_sources()
    base_names: list[str] = []
    for src in sources:
        base = src.stem
        base_names.append(base)
        if src.suffix.lower() == ".svg":
            print(f"  (SVG: {src.name} — no resize)")
            continue
        out16 = SCRIPT_DIR / f"{base}-16x16.png"
        out32 = SCRIPT_DIR / f"{base}-32x32.png"
        need16 = force or not out16.exists() or (check and src.stat().st_mtime > out16.stat().st_mtime)
        need32 = force or not out32.exists() or (check and src.stat().st_mtime > out32.stat().st_mtime)
        if need16:
            resize(src, 16, 16, out16)
            print(f"  {out16.name}")
        if need32:
            resize(src, 32, 32, out32)
            print(f"  {out32.name}")

    # First icon links
    first_16 = first_32 = "favicon.ico"
    first_links = '    <link rel="icon" href="favicon.ico">'
    if base_names:
        first_base = base_names[0]
        first_src = None
        for ext in EXTS:
            p = SCRIPT_DIR / f"{first_base}.{ext}"
            if p.exists():
                first_src = p.name
                break
        if first_src:
            if first_src.endswith(".svg"):
                first_16 = first_32 = first_src
                first_links = f'    <link rel="icon" type="image/svg+xml" href="{first_src}">'
            else:
                first_16 = f"{first_base}-16x16.png"
                first_32 = f"{first_base}-32x32.png"
                first_links = f'    <link rel="icon" type="image/png" sizes="32x32" href="{first_32}">\n    <link rel="icon" type="image/png" sizes="16x16" href="{first_16}">'

    # Build asset rows
    add_row = """
            <div class="asset-row" data-asset-file>
                <span class="asset-name">Add another (choose file)</span>
                <input type="file" accept="image/*" class="third-file" style="font-size: 0.75rem;">
                <div class="sizes">
                    <div class="size-cell"><span class="label">16</span><img alt="" width="16" height="16"></div>
                    <div class="size-cell"><span class="label">32</span><img alt="" width="32" height="32"></div>
                    <div class="size-cell"><span class="label">48</span><img alt="" width="48" height="48"></div>
                    <div class="size-cell"><span class="label">64</span><img alt="" width="64" height="64"></div>
                </div>
                <div class="actions">
                    <button type="button" class="use-tab" disabled>Use as tab</button>
                    <button type="button" class="dl dl-16" disabled>Download 16×16</button>
                    <button type="button" class="dl dl-32" disabled>Download 32×32</button>
                </div>
            </div>"""
    rows = []
    for base in base_names:
        src_name = None
        for ext in EXTS:
            p = SCRIPT_DIR / f"{base}.{ext}"
            if p.exists():
                src_name = p.name
                break
        if not src_name:
            continue
        if src_name.endswith(".svg"):
            rows.append(f'''
            <div class="asset-row" data-asset-src="{src_name}" data-svg="true">
                <span class="asset-name">{src_name}</span>
                <div class="sizes">
                    <div class="size-cell"><span class="label">16</span><img src="{src_name}" alt="" width="16" height="16"></div>
                    <div class="size-cell"><span class="label">32</span><img src="{src_name}" alt="" width="32" height="32"></div>
                    <div class="size-cell"><span class="label">48</span><img src="{src_name}" alt="" width="48" height="48"></div>
                    <div class="size-cell"><span class="label">64</span><img src="{src_name}" alt="" width="64" height="64"></div>
                </div>
                <div class="actions">
                    <button type="button" class="use-tab use-tab-svg">Use as tab</button>
                    <button type="button" class="btn-delete" data-filename="{src_name}">Delete</button>
                    <a href="{src_name}" download class="dl-svg">Download SVG</a>
                </div>
            </div>''')
        else:
            out16 = f"{base}-16x16.png"
            out32 = f"{base}-32x32.png"
            rows.append(f'''
            <div class="asset-row" data-asset-src="{src_name}">
                <span class="asset-name">{src_name}</span>
                <div class="sizes">
                    <div class="size-cell"><span class="label">16</span><img src="{out16}" alt="" width="16" height="16"></div>
                    <div class="size-cell"><span class="label">32</span><img src="{out32}" alt="" width="32" height="32"></div>
                    <div class="size-cell"><span class="label">48</span><img src="{out32}" alt="" width="48" height="48"></div>
                    <div class="size-cell"><span class="label">64</span><img src="{src_name}" alt="" width="64" height="64"></div>
                </div>
                <div class="actions">
                    <button type="button" class="use-tab">Use as tab</button>
                    <button type="button" class="btn-delete" data-filename="{src_name}">Delete</button>
                    <button type="button" class="dl dl-16">Download 16×16</button>
                    <button type="button" class="dl dl-32">Download 32×32</button>
                </div>
            </div>''')
    rows.append(add_row)

    html = (
        HTML_TEMPLATE.replace("__ASSET_ROWS__", "\n".join(rows))
        .replace("__FIRST_ICON_LINKS__", first_links)
        .replace("__FIRST_ICON_16__", first_16)
        .replace("__FIRST_ICON_32__", first_32)
    )
    if inject_serve:
        html = html.replace("<script>", "<script>window.__FAVICON_SERVE__=true;", 1)
    (SCRIPT_DIR / OUT_HTML).write_text(html, encoding="utf-8")
    print(f"Done. Open {SCRIPT_DIR / OUT_HTML} ({len(base_names)} assets).")
    return len(base_names)


def serve() -> None:
    import http.server
    import urllib.parse

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

        def do_POST(self):
            if self.path.startswith("/delete"):
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                files = qs.get("file", [])
                if not files or not files[0]:
                    self.send_error(400, "Missing file=")
                    return
                name = files[0].strip()
                if ".." in name or not name.startswith("favicon-"):
                    self.send_error(400, "Invalid filename")
                    return
                path = SCRIPT_DIR / name
                if not path.is_file():
                    self.send_error(404, "Not found")
                    return
                try:
                    do_delete(name)
                    generate(check=False, force=True, inject_serve=True)
                except Exception as e:
                    self.send_error(500, str(e))
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}\n')
                return
            self.send_error(404)

        def log_message(self, format, *args):
            pass

    with http.server.HTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Open: http://127.0.0.1:{PORT}/favicon-tester.html")
        print("Delete button will remove files from disk. Ctrl+C to stop.")
        httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Favicon tool: generate tester HTML and optionally serve it.")
    parser.add_argument("--check", action="store_true", help="Only regenerate if source newer")
    parser.add_argument("--force", action="store_true", help="Regenerate all")
    parser.add_argument("--clean", action="store_true", help="Remove only -16x16/-32x32")
    parser.add_argument("--clean-all", action="store_true", help="Remove all favicon-* assets")
    parser.add_argument("--delete", metavar="FILE", help="Delete one asset, then regenerate")
    parser.add_argument("--serve", action="store_true", help="Generate then serve (Delete removes files)")
    args = parser.parse_args()

    if args.delete:
        do_delete(args.delete)
    if args.clean_all:
        do_clean_all()
        return
    if args.clean:
        do_clean()
        return
    if args.serve:
        generate(check=args.check, force=args.force, inject_serve=True)
        serve()
        return
    generate(check=args.check, force=args.force)


if __name__ == "__main__":
    main()
