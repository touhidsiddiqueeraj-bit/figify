#!/usr/bin/env python3
"""
FigTweak server — serves editor + renders .py matplotlib files.
 Ponytail: stdlib only, no Flask needed.

Usage: python server.py [--port 8765] [--dir /path/to/figtweak]
Then open http://localhost:8765
"""
import http.server, json, urllib.parse, pathlib, sys, tempfile, subprocess, os, traceback

ROOT = pathlib.Path(__file__).parent.resolve()
PORT = 8765

# ponytail: one file, no deps
sys.path.insert(0, str(ROOT))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/render-py":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            ctype = self.headers.get("Content-Type","")
            code, filename = "", "upload.py"
            try:
                if "application/json" in ctype:
                    data = json.loads(body.decode("utf-8"))
                    code = data.get("code","") or data.get("source","")
                    filename = data.get("filename","upload.py")
                else:
                    # raw text fallback — also try json anyway
                    try:
                        data = json.loads(body.decode("utf-8"))
                        code = data.get("code","")
                        filename = data.get("filename","upload.py")
                    except:
                        code = body.decode("utf-8")
                if not code.strip():
                    raise ValueError("empty code")
                # run in subprocess for isolation + timeout
                svgs, logs, err = run_code_subprocess(code, filename)
                resp = {"svgs": svgs, "logs": logs, "error": err, "count": len(svgs)}
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            except Exception as e:
                tb = traceback.format_exc()
                self.send_response(500)
                self.send_header("Content-Type","application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e), "traceback": tb, "svgs":[], "logs":""}).encode())
            return
        self.send_error(404, "not found")

    def log_message(self, format, *args):
        sys.stdout.write(f"{self.log_date_time_string()} {format % args}\n")

def run_code_subprocess(code: str, filename: str, timeout=12):
    """Run code in fresh python process, return svgs, logs, error."""
    import textwrap, base64
    # write code to temp file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tf:
        tf.write(code)
        tmp_path = tf.name
    # runner script
    runner = textwrap.dedent(f"""
import sys, io, traceback
sys.path.insert(0, {str(ROOT)!r})
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import figtweak
code_path = {tmp_path!r}
logs_io = io.StringIO()
old_out, old_err = sys.stdout, sys.stderr
sys.stdout = sys.stderr = logs_io
svgs=[]
err=None
try:
    orig_show = plt.show
    plt.show = lambda *a, **k: None
    import pathlib
    src = pathlib.Path(code_path).read_text(encoding="utf-8")
    g = {{"__name__":"__main__", "__file__": code_path}}
    plt.close("all")
    exec(compile(src, {filename!r}, "exec"), g)
    # collect figs
    for n in plt.get_fignums():
        try:
            fig = plt.figure(n)
            svgs.append(figtweak.dumps(fig))
        except Exception as e:
            print(f"dump fig {{n}} failed: {{e}}", file=old_err)
    if not svgs:
        # try gcf or any Figure in globals
        try:
            fig = plt.gcf()
            if fig.axes:
                svgs.append(figtweak.dumps(fig))
        except: pass
        if not svgs:
            import matplotlib.figure as _mf
            for v in g.values():
                if isinstance(v, _mf.Figure):
                    try: svgs.append(figtweak.dumps(v))
                    except: pass
except SystemExit:
    pass
except Exception:
    err = traceback.format_exc()
finally:
    sys.stdout, sys.stderr = old_out, old_err
    # close all
    try: plt.close("all")
    except: pass
    import json as _j
    out = {{"svgs": svgs, "logs": logs_io.getvalue(), "error": err}}
    sys.stdout.write(_j.dumps(out))
    sys.stdout.flush()
""")
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as rf:
        rf.write(runner)
        runner_path = rf.name
    try:
        proc = subprocess.run([sys.executable, runner_path], capture_output=True, text=True, timeout=timeout, cwd=str(pathlib.Path(filename).parent) if "/" in filename else str(ROOT))
        if proc.returncode != 0 and not proc.stdout:
            # runner crashed
            return [], proc.stderr or proc.stdout, f"runner failed code {proc.returncode}"
        # runner prints json to stdout
        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}")
            return data.get("svgs",[]), data.get("logs","") + (proc.stderr or ""), data.get("error")
        except Exception as e:
            return [], proc.stdout + proc.stderr, f"parse runner output failed: {e}\\n{proc.stdout[:2000]}"
    except subprocess.TimeoutExpired:
        return [], "", f"timeout after {timeout}s — does script hang on input() or infinite loop?"
    finally:
        for p in (tmp_path, runner_path):
            try: os.unlink(p)
            except: pass

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--dir", type=str, default=str(ROOT))
    args = ap.parse_args()
    ROOT = pathlib.Path(args.dir).resolve()
    PORT = args.port
    addr = ("", PORT)
    with http.server.ThreadingHTTPServer(addr, Handler) as httpd:
        print(f"FigTweak server at http://localhost:{PORT}/  (root={ROOT})")
        print("  drag .py files onto canvas or use Import .py")
        print("  POST /api/render-py  {code, filename}")
        try: httpd.serve_forever()
        except KeyboardInterrupt: print("\nbye")
