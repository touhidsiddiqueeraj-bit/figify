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

# ponytail: keep helper small, no deps beyond stdlib+matplotlib
TEMPLATES = {
    "ieee-access-single": {"width": 3.45, "height": 2.6, "font": 8, "label": "IEEE Access single 3.5\""},
    "ieee-access-double": {"width": 7.16, "height": 3.5, "font": 9, "label": "IEEE Access double 7.2\""},
    "ieee-conf-single":  {"width": 3.5,  "height": 2.6, "font": 8, "label": "IEEE Conf single 3.5\""},
    "ieee-conf-double":  {"width": 7.16, "height": 3.5, "font": 9, "label": "IEEE Conf double 7.2\""},
    "generic-single":    {"width": 3.5,  "height": 2.6, "font": 8, "label": "Generic 3.5\""},
    "generic-double":    {"width": 7.0,  "height": 3.5, "font": 8, "label": "Generic 7\""},
}
# ieee single is the enforce default — agent: fig, ax = plt.subplots(figsize=figtweak.ieee_single())
def ieee_single(): return (TEMPLATES["ieee-access-single"]["width"], TEMPLATES["ieee-access-single"]["height"])
def ieee_double(): return (TEMPLATES["ieee-access-double"]["width"], TEMPLATES["ieee-access-double"]["height"])

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

def lint(fig):
    """Return list of issues for overlapping/too-small figures."""
    issues=[]
    try:
        w,h = fig.get_size_inches()
        if w > 4.0 and w < 6.5:
            # 6.4" default scaled to 3.5" -> fonts too small
            issues.append(f"width {w:.1f}\" is default 6.4\", use ieee_single() 3.45\" for single column or fix() will scale down fonts to ~5.8pt")
        # check tight_layout
        # check legend overlap via renderer
        try:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            for ax in fig.axes:
                leg=ax.get_legend()
                if leg:
                    # legend bbox vs axes bbox
                    try:
                        lb=leg.get_window_extent(renderer)
                        ab=ax.get_window_extent(renderer)
                        # if legend inside axes and overlapping data area
                        if ab.contains(lb.x0, lb.y0) or ab.contains(lb.x1, lb.y1):
                            # check if legend covers >5% of axes
                            inter_w=min(ab.x1, lb.x1)-max(ab.x0, lb.x0)
                            inter_h=min(ab.y1, lb.y1)-max(ab.y0, lb.y0)
                            if inter_w>0 and inter_h>0 and (inter_w*inter_h)/(ab.width*ab.height) > 0.05:
                                issues.append("legend overlaps axes >5% — fix() will move legend outside")
                    except: pass
                # check font sizes after scaling to single column
                # effective font size at 3.45" = current * 3.45/w
                if w>0:
                    eff = 10 * 3.45 / w  # default 10pt
                    if eff < 7:
                        issues.append(f"font ~{eff:.1f}pt when scaled to 3.45\" <7pt — fix() enforces 8pt Times")
        except: pass
    except: pass
    return issues

def fix(fig, template="ieee-access-single", enforce=True):
    """Enforce IEEE template: resize, fonts, legend, tight_layout. Returns fig."""
    tpl = TEMPLATES.get(template, TEMPLATES["ieee-access-single"])
    # enforce figsize
    if enforce:
        fig.set_size_inches(tpl["width"], tpl["height"])
        # fonts — IEEE requires Times
        import matplotlib as mpl
        mpl.rcParams["font.family"] = "serif"
        mpl.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]
        for ax in fig.axes:
            ax.title.set_fontfamily("serif")
            ax.title.set_fontsize(tpl["font"]+2)
            ax.xaxis.label.set_fontsize(tpl["font"])
            ax.yaxis.label.set_fontsize(tpl["font"])
            for l in ax.get_xticklabels()+ax.get_yticklabels():
                l.set_fontsize(tpl["font"]-1)
                l.set_fontfamily("serif")
            leg=ax.get_legend()
            if leg:
                for t in leg.get_texts():
                    t.set_fontsize(tpl["font"]-1)
                    t.set_fontfamily("serif")
                # move overlapping legend outside
                try:
                    fig.canvas.draw()
                    renderer=fig.canvas.get_renderer()
                    ab=ax.get_window_extent(renderer)
                    lb=leg.get_window_extent(renderer)
                    if ab.contains(lb.x0, lb.y0) or ab.contains(lb.x1, lb.y1):
                        leg.set_bbox_to_anchor((1.02, 1))
                        leg.set_loc("upper left")
                except: 
                    # fallback: always move legend outside for ieee
                    try: leg.set_bbox_to_anchor((1.02, 1)); leg.set_loc("upper left")
                    except: pass
        # tight layout — enforce, not warn
        try: fig.tight_layout(pad=0.6)
        except: 
            try: fig.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.15)
            except: pass
    return fig

def apply_template(svg_text, template="ieee-access-single"):
    """Rewrite SVG width/font to IEEE template (enforce). Used by editor and fix()."""
    tpl = TEMPLATES.get(template, TEMPLATES["ieee-access-single"])
    try:
        root=ET.fromstring(svg_text.encode("utf-8"))
        # width/height in inches -> pt (1in=72pt) but SVG uses pt/px, keep as in
        root.set("width", f"{tpl['width']}in")
        root.set("height", f"{tpl['height']}in")
        root.set("viewBox", f"0 0 {tpl['width']*72:.0f} {tpl['height']*72:.0f}")
        # fonts: walk all <text>
        for el in root.iter():
            if el.tag.endswith("text") or el.tag==f"{{{SVG_NS}}}text":
                # enforce Times, size
                # tspan handling: set on text, tspans inherit
                el.set("font-family", "Times New Roman, Times, serif")
                # keep relative size but clamp to template font
                try:
                    cur=float(el.get("font-size","10").replace("px","").replace("pt",""))
                    # cur is at original fig size; enforce to template font for labels, 9 for title
                    # simple: set to tpl font for most, +2 for title-like (larger)
                    is_title = cur > 11
                    el.set("font-size", str(tpl["font"]+ (2 if is_title else 0)))
                except: el.set("font-size", str(tpl["font"]))
                # stroke-width for text? no
            elif el.tag.endswith("path") or el.tag.endswith("line"):
                # ensure minimum stroke 0.5pt
                try:
                    w=float(el.get("stroke-width","1").replace("pt",""))
                    if w < 0.5: el.set("stroke-width", "0.5")
                except: pass
        return ET.tostring(root, encoding="unicode")
    except:
        return svg_text

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

def dumps(fig, template=None, **save_kwargs):
    """Return editable SVG string from a matplotlib figure. template='ieee-access-single' enforces."""
    if template:
        # enforce before savefig so fig size/fonts are correct
        try: fix(fig, template=template)
        except: pass
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
        if template:
            root.set("data-template", template)
        svg = ET.tostring(root, encoding="unicode")
        if template:
            # also enforce at SVG level (width/viewBox/fonts)
            svg = apply_template(svg, template=template)
        return svg
    except Exception:
        # fallback: return raw if parsing fails
        return raw

def save(fig, path, template=None, **save_kwargs):
    svg = dumps(fig, template=template, **save_kwargs)
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
