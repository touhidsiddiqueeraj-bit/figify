# Contributing

Thanks for helping Figify — the lazy, paper-ready figure editor.

## Quick dev

```bash
git clone https://github.com/touhidsiddiqueeraj-bit/figify.git
cd figify
python server.py --port 8765   # http://localhost:8765 (fast .py via subprocess)
# or: python -m http.server 8000  # SVG/CSV only, no server needed
```

`index.html` is the entire app — no build, no npm. Edit and refresh.

## Good first issues

- Save/Load already done — next: snap guides, z-order drag, inline text edit
- `seaborn`/`pandas` auto-install in Pyodide fallback
- Journal presets (Nature 89mm, Science 180mm) as export buttons

## Style

- Ponytail: shortest diff that works. Reuse stdlib/browser native before deps.
- One file with toggles over many scattered files.
- Add a `// ponytail: ...` comment when you leave a deliberate ceiling (e.g., `// ponytail: single undo stack`).

## Before PR

```bash
python -m py_compile figtweak.py server.py
# open index.html, drop examples/plot_example.py, resize an object, export SVG/PNG
```

No test framework required for trivial one-liners. Non-trivial logic leaves one runnable check (`examples/demo.py`).

## Commit

We use Conventional Commits: `feat:`, `fix:`, `docs:`.
