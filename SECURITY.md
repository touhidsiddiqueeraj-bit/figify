# Security Policy

## `.py` Execution

Figify can execute Python files that generate `matplotlib` figures in two modes:

| Mode | Where it runs | Security |
|------|---------------|----------|
| **Pyodide (default on GitHub Pages / Vercel)** | In your browser via WebAssembly sandbox | Safe — runs locally, no server, no network. First load downloads ~12MB `pyodide + matplotlib` from `cdn.jsdelivr.net`, then cached. |
| **`python server.py` (local dev)** | Local `subprocess` via `POST /api/render-py` | **Local only — do not expose to the internet.** The server does `exec(compile(code))` with a 12s timeout. Anyone with network access can run arbitrary Python. Use only on `localhost` behind a firewall. |

**Hosted deployments (`vercel.json`, GitHub Pages) are static-only** — `server.py` is never deployed. If you fork and add a Python backend, you are responsible for sandboxing.

## Reporting

Please report security issues via GitHub Issues or email `touhidsiddiqueeraj@gmail.com`. Do not open a public issue for RCE-type reports.

## Dependencies

- `matplotlib`, `numpy` via Pyodide or local install
- `imagetracerjs` for PNG → vector trace (loaded from CDN on demand)
