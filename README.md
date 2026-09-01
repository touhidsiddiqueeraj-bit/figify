# Figify — make matplotlib figures editable

> Drag a `.py` or `.svg` → move legends, nudge labels, add arrows, compose with images, export at 300 dpi. No Illustrator, no re-running Python to move text 2 px.

**Live demo:** `https://touhidsiddiqueeraj-bit.github.io/figify/` (static, Pyodide fallback) — or `python server.py` → `http://localhost:8765`


---

### Features

| Input | What happens |
|-------|--------------|
| **`fig.svg`** (`figtweak.save(fig, "fig.svg")`) | Every `axes`, `legend`, `text`, `line` becomes draggable. Text stays as `<text>` (edit the string). |
| **`.py` that calls `matplotlib`** | Runs in-browser via Pyodide (or fast `server.py` locally) — every `plt.figure()` appears as a gallery to pick and edit. |
| **`.csv`** | Pick `X/Y` → **Line / Bar / Scatter / Area** — renders as editable SVG, move labels after. |
| **Image `PNG/JPG/WebP`** | Drop as a layer, resize/rotate, **Trace to vector (beta)** via `imagetracerjs` → editable `<path>`s. |
| **IEEE template** | Header **Template: IEEE Access single** → **Fix** enforces `3.45"`, `Times 8pt`, `tight_layout`, moves overlapping legend outside, min `0.5 pt` stroke. Agent: `figtweak.fix(fig, template="ieee-access-single")`. |

**Editor:** Select (V), Text (T), Arrow (A), Rect (R), Line (L), Image (🖼) · **Shift+click** multi-select, **Ctrl+A** all, **Alt drag** moves all · **Align** left/center/right, top/middle/bottom, Distribute H/V · **Group** into `<g>` · **Bring front / Send back** · **Resize** via blue handles (`Shift` = uniform) · **Rotate** slider · **Fill / Stroke / Opacity / Font** · **Delete**, **Undo (Ctrl+Z)**, **arrow keys nudge** (`Shift` 10 px)

**Project:** **Save / Load `.figtweak.json`** (`Ctrl+S` / `Ctrl+O`) — keeps `W×H`, SVG `innerHTML`, and CSV table. Drag the JSON back to restore.

**Export:** **SVG** (vector), **PDF** (print dialog, vector), **PNG @ 300 dpi** (or 150 dpi) — `W×(dpi/96)` so `3.5" single` = 1050 px, `7" double` = 2100 px. Aspect lock 🔒 + presets.

---

### Quick start

#### 1. From Python (no server)

```python
import matplotlib.pyplot as plt
import figtweak

fig, ax = plt.subplots()
ax.plot([1,2,3], [1,4,9], label="my data")
ax.legend(); ax.set_title("editable")

figtweak.save(fig, "fig.svg")  # keeps <text>, tags groups as data-mpl-type
# or: svg = figtweak.dumps(fig)
```

Then drag `fig.svg` onto `https://figify.vercel.app` (or local).

#### 2. From a `.py` file — agent enforce (recommended)

```python
import figtweak
fig, ax = plt.subplots(figsize=figtweak.ieee_single()) # 3.45×2.6"
ax.plot(x, y, label="data")
ax.legend()
figtweak.fix(fig, template="ieee-access-single") # moves overlapping legend outside, tight_layout, Times 8pt
figtweak.save(fig, "fig.svg", template="ieee-access-single") # enforces at SVG level too
# lint before save:
print(figtweak.lint(fig)) # [] if ok, else ["legend overlaps", "font 5.8pt <7pt"]
```

```bash
# CLI (no browser)
python figtweak.py my_plot.py        # → my_plot.svg  (or _fig1.svg, _fig2.svg)
python figtweak.py examples/plot_example.py
python figtweak.py examples/ieee_demo.py  # shows bad vs good IEEE
```

Or drag `my_plot.py` onto the canvas — runs in browser (Pyodide, ~12 MB first time, cached) or via `server.py` if you run it locally (2 s vs 10 s). Pick **Template: IEEE Access single** in the header and click **Fix** to enforce (resize + Times + legend).

#### 3. From CSV

Drag `sample.csv` → right panel picks `X/Y` → `Line` → move the title, delete a series, add an arrow.

#### 4. Image composite

`Image` button or drop `microscopy.png` → resize/rotate → `Trace to vector (beta)` to get editable paths. Combine with a matplotlib panel.

---

### Run locally

```bash
git clone https://github.com/touhidsiddiqueeraj-bit/figify.git
cd figify

# fastest .py (subprocess, 12 s timeout)
python server.py --port 8765   # http://localhost:8765

# pure static (SVG/CSV + Pyodide fallback for .py)
python -m http.server 8000     # http://localhost:8000
```

`index.html` is the whole app — edit and refresh, no `npm`.

---

### Editing guide

- **Move:** click to select (blue dashed box), drag. Multi: `Shift+click` to add, drag moves all.
- **Resize:** blue handles at corners — drag, `Shift` keeps aspect. `Rect`/`Image` → `width/height`, `Text` → `font-size`, `Line` → `x1/y1/x2/y2`, `Group` → `scale` around pivot.
- **Props:** right panel → Fill, Stroke, Stroke width, Opacity, Text string/size/family, Image `W/H` + `Reset`, `X/Y`, `Rotation`.
- **Align:** with ≥2 selected → `⟸ ↔ ⟹` (H), `⤒ ↕ ⤓` (V), `Dist H/V`. `Group` wraps selection into a `<g>`.
- **Project:** `Save` → `figtweak.json`, `Load` or drop the JSON to restore. `Export ▾` → also `Save project`.

---

### Export at 300 dpi

Top bar: `W` / `H` + 🔒 lock + `3.5"` (1050×450) / `7"` (2100×900) / `reset`. Those map to journal columns at 300 dpi:

- `W×(300/96)` pixels, e.g. `800 px → 2500 px` at 300 dpi.
- **SVG** — `XMLSerializer`, vector, open in Inkscape/Illustrator.
- **PDF** — `window.print()` with `@page` sized to `W×H`, save as PDF (vector).
- **PNG** — offscreen `<canvas>` `W*scale × H*scale`, `drawImage(svg)` → `toBlob`.

`plt.rcParams["svg.fonttype"]="none"` is forced in `figtweak.py` so text stays `<text>`.

---

### `.py` execution — local vs hosted

| Host | How `.py` runs | Need |
|------|----------------|------|
| `python server.py` (localhost) | `POST /api/render-py` → `subprocess` (`Agg`, `plt.show` stubbed, `exec` + `get_fignums` → `figtweak.dumps`) | Fast, no download, 12 s timeout |
| GitHub Pages / Vercel (static) | Pyodide `cdn.jsdelivr.net/pyodide/v0.26.4` → `loadPackage(["matplotlib","numpy"])` → same `exec` in WASM | First `.py` downloads ~12 MB, then cached. Falls back automatically if `fetch /api/render-py` 404s in <2.5 s. |

Both collect every `plt.figure()` and show a gallery (`Figure 1/2`) if multi.

> **Security:** `server.py` does `exec` — **never expose it publicly**. Hosted deploys are static-only (`vercel.json` → `cleanUrls` only). See [SECURITY.md](SECURITY.md).

---

### Deploy your own

**GitHub Pages:** Push to `main` — workflow `.github/workflows/pages.yml` uploads `.` as artifact, no build.

**Vercel:** `vercel --prod` in repo or Import in dashboard — zero build, `vercel.json` is static. `index.html` + `examples/` are self-contained; Pyodide loads from CDN.

Any static host works: upload `index.html` (+ `examples/` optional).

---

### MCP for agents (so future figures are auto-fixed)

You are the agent — use `mcp_server.py` so every figure you generate is `lint`ed and `fix`ed before save.

**opencode / Claude config** (`mcp.json` or `~/.config/opencode/opencode.json`):

```json
{
  "mcpServers": {
    "figify": {
      "command": "python3",
      "args": ["/home/touhid/figtweak/mcp_server.py"]
    }
  }
}
```

Tools:

| Tool | What it does |
|------|--------------|
| `list_templates` | `ieee-access-single` (3.45") etc. |
| `render_py(code, filename)` | `exec` your `matplotlib` code → `{svgs, logs, error}` (uses `figtweak.render_py_code`) |
| `lint_py(code)` | `figtweak.lint` on each fig → `["legend overlaps", "font 5.8pt <7pt"]` |
| `fix_py(code, template="ieee-access-single")` | `figtweak.fix` + `dumps(template)` → `{svgs}` already 3.45" Times 8pt, legend outside |
| `apply_template(svg, template)` | Rewrite existing SVG `width` + `//text/@font-family` |
| `save_svg(svg, path)` | Write to disk |

Agent prompt:

```
After you write matplotlib code, call figify.lint_py — if issues, call figify.fix_py with template="ieee-access-single" and use the returned SVG.
Or in Python: import figtweak; figtweak.fix(fig); figtweak.save(fig, "fig.svg", template="ieee-access-single")
```

Run: `python mcp_server.py` (stdio) — thin wrapper over `figtweak.py`, no new engine.

### Files

```
figtweak/
  index.html            # single-file app (~70 KB, no build)
  figtweak.py           # save/dumps + fix/lint/apply_template + render_py_code() + CLI
  mcp_server.py         # MCP wrapper (FastMCP) — 5 tools above
  mcp.json              # example config for opencode/claude
  server.py             # optional local static + /api/render-py (stdlib only)
  examples/
    demo.py             # → line.svg / bar.svg / scatter.svg + sample.csv
    plot_example.py     # multi-fig demo (drag me)
    ieee_demo.py        # bad vs good IEEE (lint → fix → save)
    sample.csv
  vercel.json           # static
  .github/workflows/pages.yml
```

---

### Limitations (ponytail)

- PNG is pixels — `Trace` is best-effort posterization, not semantic `axes`/`legend` extraction. Use `.py`/`.svg` for true objects.
- Axis re-scaling is visual (move the tick `<text>`), not data. Re-plot in Python if you need new limits.
- No layers panel, no snap guides yet — `Undo` stack is linear (40 steps). `Group` is the layer.

See `## Roadmap` in Issues: snap guides, z-drag, inline text edit.

---

### License

MIT — [LICENSE](LICENSE). Copyright (c) 2026 Figify.

### Citation

If you use Figify for a paper, cite the repo URL. `figtweak.py` keeps `<text>` as text so the exported SVG/PDF is searchable and accessible.
