#!/usr/bin/env python3
"""Check UML class / sequence diagram pages for standard conformance and render defects.

    python3 check_uml.py page.html [more.html ...]            # static checks
    python3 check_uml.py --render page.html [more.html ...]   # + measured layout checks in headless Chrome
    python3 check_uml.py --render --shot DIR page.html       # + a screenshot DIR/page.png to look at

Static checks (no dependencies):
  * single-file safety: no scripts, no event-handler attributes, no remote assets except the
    Google Fonts stylesheet
  * accessible SVG: role="img", aria-labelledby -> <title> (first child) and <desc>, unique ids
  * UML 2.5.1 notation: monochrome only, square-cornered rectangles, `sd` frame on every sequence
    diagram, message line style / arrowhead consistent with the message sort, no «abstract»
    keyword, no `void` / `bool` types, no legends, keywords in guillemets, guards in brackets,
    lifeline labels in <name> : <Type> form, no ALL-CAPS message or relationship labels

Render checks (--render, needs google-chrome or chromium on PATH):
  * every text stays inside the rectangle it belongs to (class box, lifeline head, note, tag)
  * no two texts overlap; no free label overlaps a node it does not belong to
  * every text lies inside the viewBox; the page does not scroll sideways at the narrowest
    viewport headless Chrome allows (about 500px; the diagrams scroll inside their own wrapper)

Exit status 1 when any ERROR is found. WARN lines do not fail the run.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"
ALLOWED_REMOTE = ("https://fonts.googleapis.com/", "https://fonts.gstatic.com/")
GRAY_OK = {"none", "transparent", "currentcolor"}
MESSAGE_RULES = {            # kind -> (head, dashed)   §17.4.4.1
    "sync": ({"filled"}, False),
    "async": ({"open"}, False),
    "reply": ({"open", "filled"}, True),
    "create": ({"open"}, True),
    "delete": ({"filled"}, False),
    "found": ({"filled", "open"}, False),
    "lost": ({"filled", "open"}, False),
}
# UML 2.5.1 StandardProfile stereotype names (StandardProfile.xmi, Table 22.1); lower-case application is
# "stylistically obsolete" (§12.3.4) and OMG issues UML25-457 / UML25-494 settled on «Create» / «Instantiate».
STANDARD_STEREOTYPES = {"Auxiliary", "Call", "Create", "Derive", "Destroy", "Document", "Entity", "Executable",
                        "File", "Focus", "Framework", "Implement", "ImplementationClass", "Instantiate",
                        "Library", "Metaclass", "ModelLibrary", "Process", "Realization", "Refine",
                        "Responsibility", "Script", "Send", "Service", "Source", "Specification", "Subsystem",
                        "SystemModel", "Trace", "Type", "Utility", "BuildComponent", "Metamodel"}

class Report:
    def __init__(self, path):
        self.path = path
        self.errors: list[str] = []
        self.warns: list[str] = []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def print(self):
        status = "OK" if not self.errors else "FAIL"
        print(f"{status} {self.path}")
        for tag, items in (("ERROR", self.errors), ("WARN ", self.warns)):
            seen: dict[str, int] = {}
            for m in items:
                seen[m] = seen.get(m, 0) + 1
            for m, n in seen.items():
                print(f"  {tag} {m}" + (f"  [x{n}]" if n > 1 else ""))


# --------------------------------------------------------------------------- page safety

class _Scan(HTMLParser):
    def __init__(self, rep: Report):
        super().__init__(convert_charrefs=True)
        self.rep = rep
        self.ids: dict[str, int] = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            self.rep.err("<script> is not allowed; diagrams are static")
        for k, v in attrs:
            if k.lower().startswith("on"):
                self.rep.err(f"event handler attribute {k} on <{tag}>")
            if k in ("src", "href", "xlink:href") and v and re.match(r"^(https?:)?//", v):
                if not (tag == "link" and v.startswith(ALLOWED_REMOTE)):
                    self.rep.err(f"remote reference {v} on <{tag}>")
        if "id" in a:
            self.ids[a["id"]] = self.ids.get(a["id"], 0) + 1


# --------------------------------------------------------------------------- svg checks

# The skin palette (diagram-design defaults without its accent and link colours): colour has no meaning.
PALETTE = {"#2d3142", "#4f5d75", "#5a6580", "#f5f5f5", "#ffffff", "#e9e9eb"}


def _is_gray(value: str) -> bool:
    v = value.strip().lower().replace(" ", "")
    if v in GRAY_OK or v.startswith("url(") or v in PALETTE or v.startswith("rgba(45,49,66,"):
        return True
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return h[0:2] == h[2:4] == h[4:6]
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)", v)
    if m:
        return m.group(1) == m.group(2) == m.group(3)
    return v in {"black", "white", "gray", "grey", "silver", "lightgray", "lightgrey", "darkgray",
                 "darkgrey", "gainsboro", "whitesmoke", "dimgray", "dimgrey"}


def _text(el) -> str:
    return "".join(el.itertext())


def check_svg(rep: Report, idx: int, src: str):
    try:
        root = ET.fromstring(src)
    except ET.ParseError as exc:
        rep.err(f"svg #{idx}: not well-formed XML ({exc})")
        return
    kind = root.get("data-uml-diagram")
    where = f"svg #{idx} ({kind or 'unknown'})"
    if kind not in ("class", "sequence"):
        rep.err(f"{where}: <svg> must declare data-uml-diagram=\"class\" or \"sequence\" so every rule runs")
    if root.get("role") != "img":
        rep.err(f"{where}: missing role=\"img\"")
    children = list(root)
    if not children or children[0].tag != SVG_NS + "title":
        rep.err(f"{where}: <title> must be the first child of <svg>")
    ids = (root.get("aria-labelledby") or "").split()
    tid = {c.get("id") for c in root if c.tag in (SVG_NS + "title", SVG_NS + "desc")}
    if len(ids) != 2 or not set(ids) <= tid:
        rep.err(f"{where}: aria-labelledby must name its <title> and <desc> ids")
    for c in root:
        if c.tag in (SVG_NS + "title", SVG_NS + "desc") and not _text(c).strip():
            rep.err(f"{where}: empty <{c.tag[len(SVG_NS):]}>")
    vb = (root.get("viewBox") or "").split()
    style_attr = (root.get("style") or "").replace(" ", "")
    if len(vb) == 4 and not (f"min-width:{vb[2]}px" in style_attr and f"max-width:{vb[2]}px" in style_attr):
        rep.warn(f"{where}: svg style should pin min-width and max-width to the viewBox width ({vb[2]}px) "
                 f"so every figure renders at the same 1:1 type size")

    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        for attr in ("fill", "stroke"):
            v = el.get(attr)
            if v and not _is_gray(v):
                rep.err(f"{where}: colour {v} on <{tag}> is outside the skin palette - colour carries no meaning in UML")
        style = el.get("style") or ""
        for m in re.finditer(r"(?:fill|stroke)\s*:\s*([^;]+)", style):
            if not _is_gray(m.group(1)):
                rep.err(f"{where}: colour {m.group(1)} in style is outside the skin palette")
        if tag == "rect" and (float(el.get("rx", 0) or 0) > 0 or float(el.get("ry", 0) or 0) > 0):
            rep.err(f"{where}: rounded <rect> (rx/ry) - UML rectangles have square corners (§9.2.4.1)")
        uml = (el.get("data-uml") or "").lower()
        if "legend" in uml:
            rep.err(f"{where}: legend group - UML notation needs no legend")
        if tag == "g" and uml == "message":
            k = el.get("data-kind")
            head = el.get("data-head")
            dashed = el.get("data-dashed") == "true"
            if k not in MESSAGE_RULES:
                rep.err(f"{where}: message with unknown kind {k!r}")
            else:
                heads, must_dash = MESSAGE_RULES[k]
                if head not in heads:
                    rep.err(f"{where}: {k} message drawn with {head} arrowhead (§17.4.4.1)")
                if dashed != must_dash:
                    rep.err(f"{where}: {k} message drawn {'dashed' if dashed else 'solid'} (§17.4.4.1)")
                lines = [c for c in el.iter() if c.tag in (SVG_NS + "line", SVG_NS + "path")]
                actually_dashed = any(c.get("stroke-dasharray") for c in lines)
                if actually_dashed != must_dash:
                    rep.err(f"{where}: {k} message stroke does not match data-dashed")

    _transit_check(rep, where, root)
    _frame_check(rep, where, root)

    texts = [(t.get("data-role") or "", _text(t)) for t in root.iter(SVG_NS + "text")]
    all_text = "\n".join(s for _, s in texts)
    if "«abstract»" in all_text.lower() or "<<abstract>>" in all_text.lower():
        rep.err(f"{where}: «abstract» is not a UML keyword; use an italic name or {{abstract}} (Annex C)")
    if re.search(r"\)\s*:\s*void\b", all_text):
        rep.err(f"{where}: ': void' - UML has no void type; omit the return type (§9.6.4)")
    if re.search(r":\s*bool\b", all_text):
        rep.err(f"{where}: 'bool' is not a UML primitive; use Boolean (§9.6.4)")
    if re.search(r"\blegend\b", all_text, re.IGNORECASE):
        rep.err(f"{where}: legend text found")
    if re.search(r"<<[^<>]+>>", all_text):
        rep.err(f"{where}: keyword or stereotype written with '<<' '>>' - UML uses guillemets « » "
                f"(Annex C allows the ASCII form only where the character set lacks guillemets)")
    if "\u2014" in all_text:
        rep.err(f"{where}: em dash in diagram text")

    lower_std = {n.lower(): n for n in STANDARD_STEREOTYPES}
    for _, s in texts:
        for m in re.findall(r"\u00ab([^\u00ab\u00bb]+)\u00bb", s):
            for name in (x.strip() for x in m.split(",")):
                if name in lower_std and name != lower_std[name]:
                    rep.warn(f"{where}: «{name}» is the StandardProfile stereotype «{lower_std[name]}»; "
                             f"lower-case application is stylistically obsolete (§12.3.4, UML25-457/494)")

    for role, s in texts:
        letters = re.sub(r"[^A-Za-z]", "", s)
        if role in ("message-label", "assoc-name", "guard", "end-label") and len(letters) >= 4 \
                and letters.isupper():
            rep.err(f"{where}: ALL-CAPS label {s!r} - identifiers keep their case (§17.4.4.1)")
        if role == "keyword" and not re.fullmatch(r"«[^«»]+»", s):
            rep.err(f"{where}: keyword {s!r} must be in guillemets")
        if role == "class-name" and s and not s[0].isupper():
            rep.warn(f"{where}: classifier name {s!r} should start with an upper-case letter (§9.2.4.1)")
        if role == "message-label" and kind == "sequence" and re.match(r"^\s*\d+(\.\d+)*\s*:", s):
            rep.err(f"{where}: message label {s!r} carries a sequence number - sequence expressions are "
                    f"communication-diagram notation (§17.9.1.3); time order is the vertical position")
        if role == "guard" and not (s.startswith("[") and s.endswith("]")):
            rep.err(f"{where}: guard {s!r} must be in square brackets (§17.6.4.2)")
        if role == "message-label" and "(" not in s and "=" not in s and ":" not in s:
            rep.warn(f"{where}: message label {s!r} has no operation call syntax; fine only for a signal")
        if role == "dep-label" and s.startswith("«") is False and not re.match(r"^[a-z]", s):
            rep.warn(f"{where}: dependency label {s!r}: keyword expected in guillemets (§7.7.4)")

    if kind == "sequence":
        heads = [t for t in root.iter(SVG_NS + "text") if t.get("data-role") == "heading"]
        if not any(_text(h).strip().startswith("sd ") for h in heads):
            rep.err(f"{where}: sequence diagram needs an 'sd <name>' frame heading (§17.2.4.1)")
        frames = [e for e in root.iter() if e.get("data-uml") == "frame"]
        if not frames:
            rep.err(f"{where}: sequence diagram has no frame rectangle (§17.2.4.1)")
        # lifeline labels
        by_box: dict[str, list[tuple[str, str]]] = {}
        for t in root.iter(SVG_NS + "text"):
            if t.get("data-in"):
                by_box.setdefault(t.get("data-in"), []).append((t.get("data-role") or "", _text(t)))
        for box, items in by_box.items():
            names = [s for r, s in items if r == "lifeline-name"]
            has_kw = any(r == "keyword" for r, _ in items)
            for s in names:
                if ":" not in s and s != "self" and not has_kw:
                    rep.err(f"{where}: lifeline {s!r} must read '<name> : <Type>' or ': <Type>' (§17.3.4.1)")
        if any(e.get("data-uml") == "fragment" for e in root.iter()):
            ops = [e.get("data-operator") for e in root.iter() if e.get("data-uml") == "fragment"]
            for o in ops:
                if o and o != o.lower():
                    rep.err(f"{where}: interaction operator {o!r} must be lower case (§17.6.3)")


def _segments(el):
    """Axis-aligned segments of a <line> or an M/L/H/V <path> (arcs of line jumps are skipped)."""
    tag = el.tag.replace(SVG_NS, "")
    if tag == "line":
        return [((float(el.get("x1")), float(el.get("y1"))), (float(el.get("x2")), float(el.get("y2"))))]
    if tag != "path":
        return []
    segs, cur = [], None
    for cmd, args in re.findall(r"([MLHVA])\s*([^MLHVAZz]*)", el.get("d") or ""):
        nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", args)]
        if cmd == "M":
            cur = (nums[0], nums[1])
        elif cmd == "L" and cur:
            nxt = (nums[0], nums[1]); segs.append((cur, nxt)); cur = nxt
        elif cmd == "H" and cur:
            nxt = (nums[0], cur[1]); segs.append((cur, nxt)); cur = nxt
        elif cmd == "V" and cur:
            nxt = (cur[0], nums[0]); segs.append((cur, nxt)); cur = nxt
        elif cmd == "A" and cur:
            cur = (nums[-2], nums[-1])
    return segs


def _frame_check(rep, where, root):
    """Every symbol lies inside the diagram frame (Annex A: the frame encloses the contents area)."""
    frames = [r for r in root.iter(SVG_NS + "rect") if r.get("data-uml") == "frame"]
    if not frames:
        return
    f = frames[0]
    fx, fy = float(f.get("x")), float(f.get("y"))
    fx2, fy2 = fx + float(f.get("width")), fy + float(f.get("height"))
    for r in root.iter(SVG_NS + "rect"):
        if r.get("data-uml") in ("class", "lifeline-head", "fragment"):
            x, y = float(r.get("x")), float(r.get("y"))
            x2, y2 = x + float(r.get("width")), y + float(r.get("height"))
            if x < fx or y < fy or x2 > fx2 or y2 > fy2:
                rep.err(f"{where}: {r.get('data-name') or r.get('data-uml')} extends outside the diagram frame "
                        f"- enlarge the diagram or move the symbol")


def _transit_check(rep, where, root):
    """A connector must not pass through a symbol that is not one of its ends (layout rule 4)."""
    boxes = []
    for r in root.iter(SVG_NS + "rect"):
        if r.get("data-uml") in ("class", "lifeline-head"):
            x, y = float(r.get("x")), float(r.get("y"))
            boxes.append((x, y, x + float(r.get("width")), y + float(r.get("height")), r.get("data-name") or r.get("data-uml")))
    for g in root.iter(SVG_NS + "g"):
        kind = g.get("data-uml")
        if kind not in ("association", "generalization", "realization", "dependency", "note-link", "message"):
            continue
        for el in g:
            for (x1, y1), (x2, y2) in _segments(el):
                for bx1, by1, bx2, by2, name in boxes:
                    sx1, sx2, sy1, sy2 = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
                    if sx2 > bx1 + 1 and sx1 < bx2 - 1 and sy2 > by1 + 1 and sy1 < by2 - 1:
                        rep.err(f"{where}: {kind} segment ({x1:g},{y1:g})-({x2:g},{y2:g}) passes through "
                                f"{name!s} - reroute (layout rule 4)")


# --------------------------------------------------------------------------- render checks

PROBE = r"""
<script>
(function(){
  function run(){
    var res={texts:[],boxes:[],svgs:[],scrollWidth:document.documentElement.scrollWidth,vw:window.innerWidth};
    var svgs=document.querySelectorAll('svg[data-uml-diagram]');
    for(var si=0;si<svgs.length;si++){
      var svg=svgs[si], vb=svg.viewBox.baseVal;
      res.svgs.push({w:vb.width,h:vb.height});
      var ts=svg.querySelectorAll('text');
      for(var i=0;i<ts.length;i++){var b=ts[i].getBBox();
        res.texts.push({svg:si,s:ts[i].textContent,x:b.x,y:b.y,w:b.width,h:b.height,
          inside:ts[i].getAttribute('data-in'),role:ts[i].getAttribute('data-role')});}
      var ls=svg.querySelectorAll('[data-uml="lifeline-line"]');
      for(var k=0;k<ls.length;k++){res.lifelines=res.lifelines||[];
        res.lifelines.push({svg:si,x:+ls[k].getAttribute('x1'),y1:+ls[k].getAttribute('y1'),y2:+ls[k].getAttribute('y2')});}
      var sh=svg.querySelectorAll('[data-uml]');
      for(var q=0;q<sh.length;q++){var g=sh[q].getBBox();res.shapes=res.shapes||[];
        res.shapes.push({svg:si,uml:sh[q].getAttribute('data-uml'),x:g.x,y:g.y,w:g.width,h:g.height});}
      var bs=svg.querySelectorAll('[data-box]');
      for(var j=0;j<bs.length;j++){var c=bs[j].getBBox();
        res.boxes.push({svg:si,id:bs[j].id,uml:bs[j].getAttribute('data-uml'),x:c.x,y:c.y,w:c.width,h:c.height});}
    }
    var pre=document.createElement('pre');pre.id='__uml_probe';pre.textContent=JSON.stringify(res);
    document.body.appendChild(pre);
  }
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(run);}else{run();}
})();
</script>
"""


def _chrome():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _overlap(a, b, tol=0.5):
    return (a["x"] + tol < b["x"] + b["w"] and b["x"] + tol < a["x"] + a["w"]
            and a["y"] + tol < b["y"] + b["h"] and b["y"] + tol < a["y"] + a["h"])


def _inside(t, box, tol=1.0):
    return (t["x"] >= box["x"] - tol and t["y"] >= box["y"] - tol
            and t["x"] + t["w"] <= box["x"] + box["w"] + tol and t["y"] + t["h"] <= box["y"] + box["h"] + tol)


def render_check(rep: Report, path: Path):
    chrome = _chrome()
    if not chrome:
        rep.err("--render needs google-chrome or chromium on PATH")
        return
    html = path.read_text(encoding="utf-8")
    probe = html.replace("</body>", PROBE + "</body>") if "</body>" in html else html + PROBE
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "probe.html"
        tmp.write_text(probe, encoding="utf-8")
        out = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                              "--window-size=390,900", "--virtual-time-budget=8000", "--dump-dom",
                              tmp.as_uri()], capture_output=True, text=True, timeout=120)
    m = re.search(r'<pre id="__uml_probe">(.*?)</pre>', out.stdout, re.DOTALL)
    if not m:
        rep.err("render probe produced no result (Chrome failed?)")
        return
    data = json.loads(m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
                      .replace("&amp;", "&"))
    if data["scrollWidth"] > data["vw"] + 1:
        rep.err(f"page scrolls sideways at a {data['vw']}px viewport (scrollWidth {data['scrollWidth']})")
    boxes = {b["id"]: b for b in data["boxes"]}
    for si, sv in enumerate(data["svgs"]):
        texts = [t for t in data["texts"] if t["svg"] == si and t["w"] > 0]
        bxs = [b for b in data["boxes"] if b["svg"] == si]
        for t in texts:
            label = f"svg #{si} text {t['s']!r}"
            if t["x"] < 0 or t["y"] < 0 or t["x"] + t["w"] > sv["w"] or t["y"] + t["h"] > sv["h"]:
                rep.err(f"{label} leaves the viewBox")
            if t["inside"]:
                box = boxes.get(t["inside"])
                if box and not _inside(t, box):
                    rep.err(f"{label} overflows its {box['uml']} box by "
                            f"{max(box['x'] - t['x'], t['x'] + t['w'] - box['x'] - box['w'], box['y'] - t['y'], t['y'] + t['h'] - box['y'] - box['h']):.1f}px")
            own = boxes.get(t["inside"]) if t["inside"] else None
            for b in bxs:
                if b["id"] == t["inside"]:
                    continue
                if own and _inside(own, b):      # a text whose own box sits inside another box
                    continue
                if _overlap(t, b, tol=1.0):
                    rep.err(f"{label} overlaps a {b['uml']} it does not belong to")
        for g in data.get("shapes", []):
            if g["svg"] == si and g["w"] > 0 and (g["x"] < -1 or g["y"] < -1 or g["x"] + g["w"] > sv["w"] + 1
                                                    or g["y"] + g["h"] > sv["h"] + 1):
                rep.err(f"svg #{si}: a {g['uml']} shape is cut off by the diagram edge - move it or enlarge the diagram")
        for t in texts:
            if t["role"] != "message-label":       # guards deliberately cover their lifeline (§17.6.4.2)
                continue
            for ll in data.get("lifelines", []):
                if ll["svg"] == si and t["x"] + 2 < ll["x"] < t["x"] + t["w"] - 2 and ll["y1"] < t["y"] + t["h"] \
                        and t["y"] < ll["y2"]:
                    rep.warn(f"svg #{si} label {t['s']!r} sits on a lifeline at x={ll['x']:g}; "
                             f"move it with label_x so it reads between its own lifelines")
        for i, a in enumerate(texts):
            for b in texts[i + 1:]:
                if _overlap(a, b, tol=1.0):
                    rep.err(f"svg #{si} texts overlap: {a['s']!r} / {b['s']!r}")


def screenshot(page: Path, out_dir: Path):
    chrome = _chrome()
    if not chrome:
        return None
    html = page.read_text(encoding="utf-8")
    heights = [float(h) for h in re.findall(r'<svg viewBox="0 0 [\d.]+ ([\d.]+)"', html)]
    height = int(sum(heights) + 140 * len(heights) + 260)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = (out_dir / (page.stem + ".png")).resolve()
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    f"--window-size=1100,{height}", "--virtual-time-budget=5000", f"--screenshot={out}",
                    page.resolve().as_uri()], capture_output=True, timeout=120)
    return out if out.exists() else None


# --------------------------------------------------------------------------- main

def check_file(path: Path, render: bool) -> Report:
    rep = Report(path)
    html = path.read_text(encoding="utf-8")
    scan = _Scan(rep)
    scan.feed(html)
    for i, n in scan.ids.items():
        if n > 1:
            rep.err(f"duplicate id {i!r} ({n}x) - prefix ids per diagram")
    svgs = re.findall(r"<svg\b.*?</svg>", html, re.DOTALL)
    if not svgs:
        rep.err("no <svg> found")
    for i, s in enumerate(svgs):
        check_svg(rep, i, s)
    if render:
        render_check(rep, path)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--render", action="store_true", help="also run measured layout checks in headless Chrome")
    ap.add_argument("--shot", type=Path, metavar="DIR",
                    help="also save a full-page screenshot <DIR>/<page>.png of every page, to look at")
    args = ap.parse_args(argv)
    failed = False
    for f in args.files:
        rep = check_file(f, args.render)
        rep.print()
        if args.shot:
            shot = screenshot(f, args.shot)
            print(f"  shot  {shot}" if shot else "  shot  FAILED (google-chrome or chromium needed)")
        failed |= bool(rep.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
