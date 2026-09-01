#!/usr/bin/env python3
"""
Figify MCP — so the agent (you) can make better figures without opening the browser.

Tools:
  render_py(code, filename) -> svgs
  lint_py(code) -> issues
  fix_py(code, template) -> svgs (enforced)
  apply_template(svg, template) -> svg
  list_templates() -> templates
  save_svg(svg, path) -> path

Run:
  python mcp_server.py              # stdio (for opencode/claude)
  python mcp_server.py --help
  # opencode mcp.json:
  # {"mcpServers":{"figify":{"command":"python","args":["/home/touhid/figtweak/mcp_server.py"]}}}

Ponytail: thin wrapper over figtweak.py — no new rendering engine.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="figify",
    instructions="Render and fix matplotlib figures. Use lint_py to check for overlapping/small fonts, fix_py to enforce IEEE templates, render_py to get editable SVGs.",
)

import sys
sys.path.insert(0, __path__:=__import__("pathlib").Path(__file__).parent.as_posix())
import figtweak

@mcp.tool()
def list_templates() -> dict:
    """List IEEE templates. Returns {templates: [{id, width, height, font, label}]}"""
    return {"templates": [{"id": k, **v} for k, v in figtweak.TEMPLATES.items()]}

@mcp.tool()
def render_py(code: str, filename: str = "fig.py") -> dict:
    """Run Python code that creates matplotlib figures. Returns {svgs: [svg_str], logs: str, error: str|None, count: int}"""
    svgs, logs, err = figtweak.render_py_code(code, filename=filename)
    return {"svgs": svgs, "logs": logs, "error": err, "count": len(svgs)}

@mcp.tool()
def lint_py(code: str, filename: str = "fig.py") -> dict:
    """Lint figures in Python code for overlapping/too-small issues. Returns {issues: [str], count: int, logs: str}"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import traceback, io
    g = {"__name__": "__main__", "__file__": filename}
    plt.close("all")
    orig_show = plt.show
    plt.show = lambda *a, **k: None
    issues = []
    logs = ""
    try:
        old_out, old_err = __import__("sys").stdout, __import__("sys").stderr
        buf_out, buf_err = io.StringIO(), io.StringIO()
        __import__("sys").stdout, __import__("sys").stderr = buf_out, buf_err
        exec(compile(code, filename, "exec"), g)
        plt.show = orig_show
        fignums = plt.get_fignums()
        figs = [plt.figure(n) for n in fignums]
        if not figs:
            # try gcf
            try:
                fig = plt.gcf()
                if fig.axes:
                    figs = [fig]
            except: pass
        for fig in figs:
            issues.extend(figtweak.lint(fig))
        logs = buf_out.getvalue() + buf_err.getvalue()
        __import__("sys").stdout, __import__("sys").stderr = old_out, old_err
    except Exception:
        issues.append(traceback.format_exc())
        try: __import__("sys").stdout, __import__("sys").stderr = old_out, old_err
        except: pass
    finally:
        try: plt.close("all")
        except: pass
        plt.show = orig_show
    return {"issues": issues, "count": len(issues), "logs": logs}

@mcp.tool()
def fix_py(code: str, template: str = "ieee-access-single", filename: str = "fig.py") -> dict:
    """Enforce IEEE template on figures in Python code. Returns {svgs: [svg_str], logs: str, error: str|None} — svgs are already fixed."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import traceback, io
    g = {"__name__": "__main__", "__file__": filename}
    plt.close("all")
    orig_show = plt.show
    plt.show = lambda *a, **k: None
    svgs, logs, err = [], "", None
    try:
        old_out, old_err = __import__("sys").stdout, __import__("sys").stderr
        buf_out, buf_err = io.StringIO(), io.StringIO()
        __import__("sys").stdout, __import__("sys").stderr = buf_out, buf_err
        exec(compile(code, filename, "exec"), g)
        plt.show = orig_show
        fignums = plt.get_fignums()
        figs = [plt.figure(n) for n in fignums]
        if not figs:
            try:
                fig = plt.gcf()
                if fig.axes:
                    figs = [fig]
            except: pass
        for fig in figs:
            figtweak.fix(fig, template=template)
            svgs.append(figtweak.dumps(fig, template=template))
        logs = buf_out.getvalue() + buf_err.getvalue()
        __import__("sys").stdout, __import__("sys").stderr = old_out, old_err
    except Exception:
        err = traceback.format_exc()
        try: __import__("sys").stdout, __import__("sys").stderr = old_out, old_err
        except: pass
    finally:
        try: plt.close("all")
        except: pass
        plt.show = orig_show
    return {"svgs": svgs, "logs": logs, "error": err, "count": len(svgs), "template": template}

@mcp.tool()
def apply_template(svg: str, template: str = "ieee-access-single") -> dict:
    """Enforce IEEE template on an SVG string (width/fonts/stroke). Returns {svg: str}"""
    return {"svg": figtweak.apply_template(svg, template=template), "template": template}

@mcp.tool()
def save_svg(svg: str, path: str) -> dict:
    """Save SVG string to path. Returns {path: str}"""
    import pathlib
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(svg, encoding="utf-8")
    return {"path": str(p.resolve())}

if __name__ == "__main__":
    mcp.run()
