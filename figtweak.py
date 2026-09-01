"""
figtweak — make matplotlib SVGs editable in FigTweak editor.
Usage:
    import matplotlib.pyplot as plt
    import figtweak
    fig, ax = plt.subplots()
    ax.plot([1,2,3], [1,4,9])
    figtweak.save(fig, "fig.svg")
    # or: svg_string = figtweak.dumps(fig)
"""
import io
import xml.etree.ElementTree as ET

# ponytail: keep helper <80 lines, no deps beyond stdlib+matplotlib
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

def _ensure_viewbox(root, width_pt, height_pt):
    if root.get("viewBox"):
        return
    # matplotlib already writes viewBox; fallback uses pt → px
    w = root.get("width", f"{width_pt}pt")
    h = root.get("height", f"{height_pt}pt")
    # strip unit
    def _num(s):
        for u in ("pt","px","in","mm","cm"):
            if s.endswith(u): return float(s[:-len(u)])
        return float(s)
    try:
        vw, vh = _num(w), _num(h)
        root.set("viewBox", f"0 0 {vw} {vh}")
    except: pass

def _tag_groups(root):
    """Tag top-level <g> groups so editor can select them."""
    # matplotlib svg groups are <g id="figure_1">, <g id="axes_1"> etc.
    count = 0
    for g in root.iter(f"{{{SVG_NS}}}g"):
        gid = g.get("id", "")
        if gid.startswith("figure") or gid.startswith("axes") or gid.startswith("legend") or gid.startswith("text"):
            kind = gid.split("_")[0]  # figure, axes, legend
            g.set("data-mpl-type", kind)
            g.set("data-mpl-id", gid)
            count += 1
        elif g.get("id"):
            # generic group — make selectable too
            if not g.get("data-mpl-type"):
                g.set("data-mpl-type", "group")
                g.set("data-mpl-id", g.get("id"))
                count += 1
    # also tag lone <text>, <path>, <line> outside groups
    for el in root.iter():
        if el.tag in (f"{{{SVG_NS}}}text", f"{{{SVG_NS}}}path", f"{{{SVG_NS}}}line", f"{{{SVG_NS}}}rect", f"{{{SVG_NS}}}polyline", f"{{{SVG_NS}}}circle"):
            # if ancestor already tagged, skip
            pass
    return count

def dumps(fig, **save_kwargs):
    """Return editable SVG string from a matplotlib figure."""
    buf = io.BytesIO()
    # force text as <text> not paths — critical for editing
    save_kwargs.setdefault("format", "svg")
    # ensure fonts stay editable
    import matplotlib as mpl
    orig = mpl.rcParams["svg.fonttype"]
    mpl.rcParams["svg.fonttype"] = "none"
    try:
        fig.savefig(buf, **save_kwargs)
    finally:
        mpl.rcParams["svg.fonttype"] = orig
    buf.seek(0)
    raw = buf.getvalue().decode("utf-8")
    # parse and enrich
    try:
        root = ET.fromstring(raw.encode("utf-8"))
        # figure size in points for viewBox fallback
        w_pt, h_pt = fig.get_size_inches() * fig.dpi
        _ensure_viewbox(root, w_pt, h_pt)
        _tag_groups(root)
        # add meta for editor
        root.set("data-figtweak", "1")
        root.set("data-fig-width", str(fig.get_size_inches()[0]))
        root.set("data-fig-height", str(fig.get_size_inches()[1]))
        root.set("data-fig-dpi", str(fig.dpi))
        return ET.tostring(root, encoding="unicode")
    except Exception:
        # fallback: return raw if parsing fails
        return raw

def save(fig, path, **save_kwargs):
    svg = dumps(fig, **save_kwargs)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path

def render_py_code(code: str, filename="<string>"):
    """Exec code that creates matplotlib figures, return list of SVG strings."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import traceback, sys, io as _io
    # isolated globals — but give it plt, numpy etc.
    g = {"__name__": "__main__", "__file__": filename}
    plt.close("all")
    # capture stdout/stderr
    out_buf, err_buf = _io.StringIO(), _io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    svgs, logs, err = [], "", None
    try:
        sys.stdout, sys.stderr = out_buf, err_buf
        # block plt.show() from hanging
        orig_show = plt.show
        plt.show = lambda *a, **k: None
        exec(compile(code, filename, "exec"), g)
        plt.show = orig_show
        # collect figures — any that were created
        fignums = plt.get_fignums()
        if not fignums:
            # maybe user kept fig reference in globals?
            for v in g.values():
                try:
                    import matplotlib.figure as _mf
                    if isinstance(v, _mf.Figure):
                        if v not in [plt.figure(n) for n in fignums]:
                            svgs.append(dumps(v))
                except: pass
        for n in fignums:
            try:
                fig = plt.figure(n)
                svgs.append(dumps(fig))
            except: pass
        # also if script saved to file via savefig, we ignore — figures still open
        if not svgs:
            # fallback: try gcf if it has axes
            try:
                fig = plt.gcf()
                if fig.axes:
                    svgs.append(dumps(fig))
            except: pass
        logs = out_buf.getvalue() + err_buf.getvalue()
    except Exception as e:
        err = traceback.format_exc()
        logs = out_buf.getvalue() + err_buf.getvalue()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        try: plt.close("all")
        except: pass
    return svgs, logs, err

def render_py_file(path: str):
    with open(path, encoding="utf-8") as f:
        code = f.read()
    return render_py_code(code, filename=path)

# quick demo + CLI
if __name__ == "__main__":
    import sys, pathlib
    if len(sys.argv) > 1 and sys.argv[1].endswith(".py"):
        p = pathlib.Path(sys.argv[1])
        print(f"rendering {p} ...")
        svgs, logs, err = render_py_file(str(p))
        if err:
            print("ERROR:\n", err)
            if logs: print("LOGS:\n", logs)
            sys.exit(1)
        if logs: print(logs)
        if not svgs:
            print("no figures detected (did script call plt.show() or plt.close()?)")
            sys.exit(0)
        for i, svg in enumerate(svgs):
            out = p.with_name(f"{p.stem}_fig{i+1}.svg" if len(svgs)>1 else f"{p.stem}.svg")
            out.write_text(svg, encoding="utf-8")
            print(f"wrote {out} ({len(svg)//1024}KB)")
    else:
        import matplotlib.pyplot as plt
        import numpy as np
        plt.rcParams["svg.fonttype"] = "none"
        fig, ax = plt.subplots(figsize=(6,4))
        x = np.linspace(0, 6, 100)
        ax.plot(x, np.sin(x), label="sin")
        ax.plot(x, np.cos(x), label="cos")
        ax.set_title("FigTweak demo — editable SVG")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
        save(fig, "/tmp/figtweak_demo.svg")
        print("wrote /tmp/figtweak_demo.svg")
