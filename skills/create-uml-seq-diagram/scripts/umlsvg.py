"""umlsvg - UML 2.5.1 class and sequence diagram primitives that emit standard notation as SVG.

Layout (coordinates) is chosen by the author; notation is decided here, so a diagram built
with these primitives cannot use a non-standard arrowhead, a rounded class box, a legend or
colour semantics. See references/notation.md for the rules
and the clauses of the specification behind each primitive.

Usage from a build script:

    import sys; sys.path.insert(0, "<skill-dir>/scripts")
    from umlsvg import *

    cd = ClassDiagram("shop-class", "Shop class diagram", "One sentence about the content.",
                      width=720, height=360, frame=("pkg", "Shop"))
    order = cd.klass(60, 80, "Order", attrs=["-id: String"], ops=["+total(): Money"])
    ...
    write_page("shop.html", "Shop", [Figure(cd, "Shop, class diagram")])

Every coordinate is in SVG user units (px). Text widths are computed from Helvetica AFM
metrics, which Arial, Liberation Sans and Arimo share, so boxes fit their text exactly when
one of those faces renders the page.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from html import escape

# --------------------------------------------------------------------------- style

# Skin: the default palette and typefaces of the diagram-design skill (no accent colour: colour carries
# no meaning in UML). Layout never depends on the skin; only drawing does.
FONT = "'Geist', Arial, 'Liberation Sans', sans-serif"
MONO = "'Geist Mono', 'Liberation Mono', 'DejaVu Sans Mono', monospace"
INK = "#2d3142"                       # classifier outlines, names, generalization, diamonds
MUTED = "#4f5d75"                     # associations, dependencies, messages, labels
PAPER = "#f5f5f5"                     # page and diagram background, hollow arrowheads
WHITE = "#ffffff"                     # class boxes, lifeline heads, notes
SEP = "rgba(45,49,66,0.22)"           # compartment separators
FRAME = "rgba(45,49,66,0.45)"         # sd frame, fragments, name tags
FRAG_FILL = "rgba(45,49,66,0.02)"
LIFELINE = "rgba(45,49,66,0.40)"
EXEC_FILL = "#e9e9eb"                 # ExecutionSpecification (paper with 6% ink, opaque): "thin rectangles (gray or white)" §17.2.4.4
STROKE = 1

SIZE_NAME = 13          # classifier / lifeline name
SIZE_TEXT = 12          # features, keywords, labels, notes
SIZE_SMALL = 11         # association-end adornments, guards
# The SIZE_* values drive layout (box widths, line positions). Text is drawn at the skin's sizes:
RENDER_SIZE = {SIZE_NAME: 12, SIZE_TEXT: 10, SIZE_SMALL: 10}
MONO_ROLES = {"attrs", "ops", "literals", "keyword", "end-label", "dep-label", "assoc-name",
              "message-label", "guard", "note"}
MUTED_ROLES = {"end-label", "dep-label", "assoc-name", "message-label", "guard", "keyword"}

# Helvetica AFM advance widths (1/1000 em), ASCII 32..126. Arial and Liberation Sans match.
_REG = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
        556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
        1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
        667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
        333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
        556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]
_BOLD = [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
         556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
         975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
         667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
         333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
         611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584]
_EXTRA = {"\u00a0": 278, "«": 556, "»": 556, "·": 278, "…": 1000, "×": 584,
          "≤": 549, "≥": 549, "≠": 549, "→": 1000}


def text_width(s: str, size: float, bold: bool = False, mono: bool = False) -> float:
    if mono:
        return len(s) * 0.6 * size
    table = _BOLD if bold else _REG
    total = 0
    for ch in s:
        o = ord(ch)
        total += table[o - 32] if 32 <= o <= 126 else _EXTRA.get(ch, 600)
    return total * size / 1000.0


def drawn_width(s: str, size: float, bold: bool = False) -> float:
    """Width budget for a text drawn in the skin: the larger of the layout metric (Arial at the layout size)
    and Geist Mono at its drawn size, so a box fits its text in either face."""
    return max(text_width(s, size, bold), text_width(s, RENDER_SIZE.get(size, size), mono=True))


def up4(v: float) -> int:
    return int(math.ceil(v / 4.0) * 4)


def _f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------- svg core

class _Canvas:
    """Ordered SVG layers shared by both diagram kinds."""

    LAYERS = ("frame", "under", "edges", "nodes", "over", "labels")

    def __init__(self, slug: str, title: str, desc: str, width: int, height: int, kind: str):
        if not slug or any(c for c in slug if not (c.isalnum() or c == "-")):
            raise ValueError("slug must be [a-zA-Z0-9-]+")
        self.slug, self.title, self.desc = slug, title, desc
        self.width, self.height, self.kind = width, height, kind
        self.layers = {k: [] for k in self.LAYERS}
        self._ids = 0

    def uid(self, prefix: str) -> str:
        self._ids += 1
        return f"{self.slug}-{prefix}{self._ids}"

    def add(self, layer: str, s: str) -> None:
        self.layers[layer].append(s)

    # text -----------------------------------------------------------------
    def text(self, x, y, s, size=SIZE_TEXT, *, anchor="start", bold=False, italic=False,
             underline=False, mono=False, halo=False, layer="labels", inside=None, role="label"):
        mono = mono or role in MONO_ROLES
        weight = "600" if bold else ("500" if role == "lifeline-name" else None)
        attrs = [f'x="{_f(x)}"', f'y="{_f(y)}"', f'font-size="{_f(RENDER_SIZE.get(size, size))}"',
                 f'font-family="{MONO if mono else FONT}"', f'fill="{MUTED if role in MUTED_ROLES else INK}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if italic:
            attrs.append('font-style="italic"')
        if underline:
            attrs.append('text-decoration="underline"')
        if halo:
            attrs.append(f'stroke="{PAPER}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"')
        if inside:
            attrs.append(f'data-in="{inside}"')
        attrs.append(f'data-role="{role}"')
        self.add(layer, f'<text {" ".join(attrs)}>{escape(s)}</text>')

    def rich_text(self, x, y, parts, size=SIZE_TEXT, *, anchor="start", layer="labels",
                  inside=None, role="label", halo=False):
        """parts: list of (text, bold) rendered as one <text> with tspans."""
        attrs = [f'x="{_f(x)}"', f'y="{_f(y)}"', f'font-size="{_f(RENDER_SIZE.get(size, size) + 1)}"',
                 f'font-family="{FONT}"', f'fill="{INK}"', f'data-role="{role}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if inside:
            attrs.append(f'data-in="{inside}"')
        if halo:
            attrs.append(f'stroke="{PAPER}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"')
        bold = ' font-weight="600"'
        spans = "".join(f'<tspan{bold if b else ""}>{escape(t)}</tspan>' for t, b in parts)
        self.add(layer, f'<text {" ".join(attrs)}>{spans}</text>')

    # shapes ---------------------------------------------------------------
    def rect(self, x, y, w, h, *, fill=WHITE, stroke=INK, layer="nodes", uml="", rid=None, dash=None, box=True,
             extra=""):
        rid = rid or self.uid("r")
        d = f' stroke-dasharray="{dash}"' if dash else ""
        b = ' data-box="1"' if box else ""
        self.add(layer, f'<rect id="{rid}" x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" '
                        f'fill="{fill}" stroke="{stroke}" stroke-width="{STROKE}"{d} data-uml="{uml}"{b}{extra}/>')
        return rid

    def line(self, x1, y1, x2, y2, *, dash=None, layer="edges", width=STROKE, color=INK, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(layer, f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
                        f'stroke="{color}" stroke-width="{width}"{d}{extra}/>')

    def polyline(self, pts, *, dash=None, layer="edges", color=INK, extra=""):
        d = _path(pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(layer, f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{STROKE}"{da}{extra}/>')

    def polygon(self, pts, *, fill, layer="edges", stroke=INK, extra=""):
        p = " ".join(f"{_f(x)},{_f(y)}" for x, y in pts)
        self.add(layer, f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{STROKE}" '
                        f'stroke-linejoin="miter"{extra}/>')

    def name_tag(self, x, y, parts, *, layer="over", uml="frame-heading", min_w=0):
        """Cut-corner name tag (Annex A heading; §17.6.4.3 operator pentagon)."""
        w = max(min_w, up4(sum(text_width(t, SIZE_TEXT, b) for t, b in parts) + 20))
        h = 20
        rid = self.uid("tag")
        self.add(layer, f'<path id="{rid}" d="M {_f(x)},{_f(y)} H {_f(x + w)} V {_f(y + h - 7)} '
                        f'L {_f(x + w - 7)},{_f(y + h)} H {_f(x)} Z" fill="{PAPER}" stroke="{FRAME}" '
                        f'stroke-width="{STROKE}" data-uml="{uml}" data-box="1"/>')
        self.rich_text(x + 7, y + 14, parts, layer=layer, inside=rid, role="heading")
        return w, h

    # output ---------------------------------------------------------------
    def svg(self) -> str:
        body = "\n".join("\n".join(self.layers[k]) for k in self.LAYERS if self.layers[k])
        return (f'<svg viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" '
                f'role="img" aria-labelledby="{self.slug}-title {self.slug}-desc" '
                f'data-uml-diagram="{self.kind}" style="min-width:{self.width}px;max-width:{self.width}px">\n'
                f'<title id="{self.slug}-title">{escape(self.title)}</title>\n'
                f'<desc id="{self.slug}-desc">{escape(self.desc)}</desc>\n'
                f'<rect width="100%" height="100%" fill="{PAPER}"/>\n{body}\n</svg>')


def _path(pts):
    """Rectilinear path through the points."""
    _check_rectilinear(pts)
    return " ".join([f"M {_f(pts[0][0])},{_f(pts[0][1])}"] + [f"L {_f(x)},{_f(y)}" for x, y in pts[1:]])


def _check_rectilinear(pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x1 != x2 and y1 != y2:
            raise ValueError(f"connector segment not rectilinear: {(x1, y1)} -> {(x2, y2)}; "
                             f"pass explicit attach coordinates, e.g. box.n(x) / box.s(x)")


def _unit(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _arrow_open(c: _Canvas, tip, u, layer="edges", length=10, half=5, color=MUTED):
    """Open (stick) arrowhead at `tip`, pointing along unit vector u."""
    nx, ny = -u[1], u[0]
    bx, by = tip[0] - u[0] * length, tip[1] - u[1] * length
    c.add(layer, f'<path d="M {_f(bx + nx * half)},{_f(by + ny * half)} L {_f(tip[0])},{_f(tip[1])} '
                 f'L {_f(bx - nx * half)},{_f(by - ny * half)}" fill="none" stroke="{color}" '
                 f'stroke-width="{STROKE}" stroke-linejoin="miter"/>')


def _arrow_filled(c: _Canvas, tip, u, layer="edges", length=10, half=4, color=MUTED):
    nx, ny = -u[1], u[0]
    bx, by = tip[0] - u[0] * length, tip[1] - u[1] * length
    c.polygon([(bx + nx * half, by + ny * half), tip, (bx - nx * half, by - ny * half)], fill=color,
              stroke=color, layer=layer)


# --------------------------------------------------------------------------- frame

def _frame(c: _Canvas, kind: str, name: str, inset=8):
    x, y, w, h = inset, inset, c.width - 2 * inset, c.height - 2 * inset
    rid = c.rect(x, y, w, h, fill="none", stroke=FRAME, layer="frame", uml="frame", box=False)
    c.name_tag(x, y, [(kind, True), (" " + name, False)], layer="over")
    return x, y, w, h


# =========================================================================== CLASS DIAGRAM

@dataclass
class Attr:
    """An attribute string per §9.5.4, e.g. "-count: Integer[0..1] = 0 {readOnly}"."""
    text: str
    static: bool = False


@dataclass
class Op:
    """An operation string per §9.6.4, e.g. "+createWindow(c: Container): Window"."""
    text: str
    static: bool = False
    abstract: bool = False


def _feat(f, kind):
    if isinstance(f, str):
        return kind(f)
    return f


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    name: str = ""

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    # attachment points on each side; argument is the absolute coordinate along that side
    def n(self, x=None):
        return (self.cx if x is None else x, self.y)

    def s(self, x=None):
        return (self.cx if x is None else x, self.bottom)

    def w_(self, y=None):
        return (self.x, self.cy if y is None else y)

    def e(self, y=None):
        return (self.right, self.cy if y is None else y)


@dataclass
class End:
    """An association end (§11.5.4).

    role: end name incl. optional visibility, e.g. "-wrappee"
    mult: multiplicity string, e.g. "1", "0..1", "*"
    navigable: True -> open arrowhead (navigable end), None -> nothing drawn
    aggregation: None | "shared" (hollow diamond) | "composite" (filled diamond); put it on the WHOLE's end
    side: +1 / -1 picks which side of the line the role name sits on; the multiplicity takes the other
    static: underline the role name (static property)
    """
    role: str | None = None
    mult: str | None = None
    navigable: bool | None = None
    aggregation: str | None = None
    side: int = 1
    static: bool = False


class ClassDiagram(_Canvas):
    PAD_X = 10
    LINE = 16

    def __init__(self, slug, title, desc, width, height):
        super().__init__(slug, title, desc, width, height, "class")

    # ---------------------------------------------------------------- classifier
    def klass(self, x, y, name, *, keywords=(), abstract=False, attrs=None, ops=None, literals=None,
              w=None, min_w=96) -> Box:
        """Classifier symbol (§9.2.4.1).

        keywords: e.g. ("interface",), ("enumeration",), ("Metaclass",) - shown «...» above the name.
        abstract: italic name (§9.2.4.1).
        attrs/ops: lists of str | Attr | Op. Both None -> compartments suppressed (name-only box).
                   If either is given, both compartments are drawn so an empty one means "none".
        literals: enumeration literals compartment (for «enumeration»), drawn before attrs/ops.
        """
        if any(k.lower() == "abstract" for k in keywords):
            raise ValueError("«abstract» is not a UML keyword; use abstract=True (italic name)")
        show = attrs is not None or ops is not None
        attrs = [_feat(a, Attr) for a in (attrs or [])]
        ops = [_feat(o, Op) for o in (ops or [])]
        kw_lines = [f"«{k}»" for k in keywords]

        widths = [text_width(k, SIZE_TEXT) for k in kw_lines]
        widths.append(text_width(name, SIZE_NAME, bold=True))
        for f in attrs + ops + [Attr(t) for t in (literals or [])]:
            widths.append(drawn_width(f.text, SIZE_TEXT))
        bw = w or max(min_w, up4(max(widths) + 2 * self.PAD_X + 4))

        # name compartment
        cur = y + 7
        name_parts = []
        for k in kw_lines:
            name_parts.append(("kw", k, cur + 11))
            cur += 15
        name_parts.append(("name", name, cur + 12))
        cur += 16
        cur += 6
        compartments = []
        if literals is not None:
            compartments.append(("literals", [Attr(t) for t in literals]))
        if show:
            compartments.append(("attrs", attrs))
            compartments.append(("ops", ops))
        total_h = cur - y
        for _, feats in compartments:
            total_h += (8 + self.LINE * len(feats)) if feats else 12
        total_h = up4(total_h)
        rid = self.rect(x, y, bw, total_h, uml="class", extra=f' data-name="{escape(name)}"')
        cx = x + bw / 2
        for kind, s, by in name_parts:
            if kind == "name":
                self.text(cx, by, s, SIZE_NAME, anchor="middle", bold=True, italic=abstract,
                          layer="nodes", inside=rid, role="class-name")
            else:
                self.text(cx, by, s, SIZE_TEXT, anchor="middle", layer="nodes", inside=rid, role="keyword")
        top = cur
        for kind, feats in compartments:
            self.line(x, top, x + bw, top, layer="nodes", color=SEP)
            hgt = (8 + self.LINE * len(feats)) if feats else 12
            for i, f in enumerate(feats):
                self.text(x + self.PAD_X, top + 4 + 12 + self.LINE * i, f.text, SIZE_TEXT,
                          underline=getattr(f, "static", False), italic=getattr(f, "abstract", False),
                          layer="nodes", inside=rid, role=kind)
            top += hgt
        return Box(x, y, bw, total_h, name)

    # ---------------------------------------------------------------- relationships
    def _end_labels(self, p, u, end: End, adorn_len: float):
        """Place role name and multiplicity near end point p (u = direction INTO the box)."""
        along = adorn_len + 5
        bx, by = p[0] - u[0] * along, p[1] - u[1] * along
        items = []
        if end.role:
            items.append((end.role, end.side, end.static))
        if end.mult:
            items.append((end.mult, -end.side, False))
        for s, side, static in items:
            if abs(u[1]) > 0.5:                       # vertical segment: text left/right of the line
                tx = bx + 6 if side > 0 else bx - 6
                anchor = "start" if side > 0 else "end"
                ty = by - 3 if u[1] > 0 else by + 12
            else:                                      # horizontal segment: text above/below
                ty = by - 5 if side > 0 else by + 14
                tx = bx
                anchor = "end" if u[0] > 0 else "start"
            self.text(tx, ty, s, SIZE_SMALL, anchor=anchor, underline=static, halo=True, role="end-label")

    def _adorn(self, pts, end: End | None, at_start: bool):
        """Draw end adornments; returns trimmed point list and the adornment length used."""
        if end is None:
            return pts, 0
        if at_start:
            p, q = pts[0], pts[1]
        else:
            p, q = pts[-1], pts[-2]
        u = _unit(q, p)                       # direction pointing into the classifier at p
        nx, ny = -u[1], u[0]
        length = 0
        if end.aggregation in ("shared", "composite"):
            off = 0
            tip = p
            back = (tip[0] - u[0] * 16, tip[1] - u[1] * 16)
            mid = (tip[0] - u[0] * 8, tip[1] - u[1] * 8)
            self.polygon([tip, (mid[0] + nx * 5, mid[1] + ny * 5), back, (mid[0] - nx * 5, mid[1] - ny * 5)],
                         fill=INK if end.aggregation == "composite" else PAPER, layer="over")
            new = back
            length = 16 + off
            pts = ([new] + pts[1:]) if at_start else (pts[:-1] + [new])
        elif end.aggregation is not None:
            raise ValueError("aggregation must be None, 'shared' or 'composite'")
        if end.navigable is True:
            _arrow_open(self, p, u)
            length = max(length, 10)
        elif end.navigable is not None:
            raise ValueError("navigable must be True (open arrowhead) or None")
        if end.aggregation == "composite" and end.mult and end.mult not in ("1", "0..1"):
            raise ValueError("composite end multiplicity must be 1 or 0..1 (§9.5.3)")
        self._end_labels(p, u, end, length)
        return pts, length

    def association(self, pts, a: End | None = None, b: End | None = None, *, name=None, name_at=None):
        """Binary association (§11.5.4). pts runs from end a to end b (both on classifier edges).
        name / name_at=(x, y): optional association name near the middle of the line."""
        pts = list(pts)
        _check_rectilinear(pts)
        self.add("edges", '<g data-uml="association">')
        pts, _ = self._adorn(pts, a, at_start=True)
        pts, _ = self._adorn(pts, b, at_start=False)
        self.polyline(pts, color=MUTED)
        self.add("edges", "</g>")
        if name:
            x, y = name_at
            self.text(x, y, name, SIZE_TEXT, anchor="middle", halo=True, role="assoc-name")

    def generalization(self, pts, *, realization=False):
        """Generalization (§9.2.4.2) or InterfaceRealization (realization=True, dashed §7.7.4).
        pts runs from the specific classifier to the general one."""
        pts = list(pts)
        _check_rectilinear(pts)
        u = _unit(pts[-2], pts[-1])
        tip = pts[-1]
        base = (tip[0] - u[0] * 14, tip[1] - u[1] * 14)
        nx, ny = -u[1], u[0]
        kind = "realization" if realization else "generalization"
        self.add("edges", f'<g data-uml="{kind}">')
        self.polyline(pts[:-1] + [base], dash="5,4" if realization else None)
        self.polygon([tip, (base[0] + nx * 7, base[1] + ny * 7), (base[0] - nx * 7, base[1] - ny * 7)],
                     fill=PAPER)
        self.add("edges", "</g>")

    def generalization_tree(self, sources, target, bus_y, *, realization=False):
        """Shared-target style (§9.2.4.2): every source point (on a child's top edge) rises to bus_y,
        the bus joins them, one trunk with one triangle reaches `target` (on the parent's bottom edge)."""
        dash = "5,4" if realization else None
        kind = "realization" if realization else "generalization"
        self.add("edges", f'<g data-uml="{kind}">')
        xs = [s[0] for s in sources] + [target[0]]
        for sx, sy in sources:
            self.polyline([(sx, sy), (sx, bus_y)], dash=dash)
        self.polyline([(min(xs), bus_y), (max(xs), bus_y)], dash=dash)
        tip = target
        base = (tip[0], tip[1] + 14 if bus_y > tip[1] else tip[1] - 14)
        self.polyline([(target[0], bus_y), base], dash=dash)
        u = _unit((target[0], bus_y), tip)
        nx, ny = -u[1], u[0]
        self.polygon([tip, (base[0] + nx * 7, base[1] + ny * 7), (base[0] - nx * 7, base[1] - ny * 7)],
                     fill=PAPER)
        self.add("edges", "</g>")

    def dependency(self, pts, keyword="use", *, name=None, label_at=None, anchor="middle"):
        """Dependency (§7.7.4): dashed, open arrowhead at the supplier; «keyword» and optional name.
        keyword: "use" (usage) or "Instantiate" (the client creates instances of the supplier)."""
        pts = list(pts)
        _check_rectilinear(pts)
        self.add("edges", '<g data-uml="dependency">')
        self.polyline(pts, dash="5,4", color=MUTED)
        _arrow_open(self, pts[-1], _unit(pts[-2], pts[-1]))
        self.add("edges", "</g>")
        lines = []
        if keyword:
            lines.append(f"«{keyword}»")
        if name:
            lines.append(name)
        if lines:
            if label_at is None:
                seg = max(zip(pts, pts[1:]), key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
                (x1, y1), (x2, y2) = seg
                if y1 == y2:
                    label_at = ((x1 + x2) / 2, y1 - 6 - 14 * (len(lines) - 1))
                else:
                    label_at = (x1 + 8, (y1 + y2) / 2)
                    anchor = "start"
            x, y = label_at
            for i, s in enumerate(lines):
                self.text(x, y + 14 * i, s, SIZE_TEXT, anchor=anchor, halo=True, role="dep-label")

    def note(self, x, y, lines, *, links=(), w=None, mono=False) -> Box:
        """Comment (§7.2.4): dog-eared rectangle; links are point lists from the note to the annotated
        element, drawn dashed without arrowheads."""
        return _note(self, x, y, lines, links=links, w=w, mono=mono)


def _note(c: _Canvas, x, y, lines, *, links=(), w=None, mono=False):
    for pts in links:
        c.add("under", f'<g data-uml="note-link">')
        c.polyline(list(pts), dash="4,3", layer="under", color=MUTED)
        c.add("under", "</g>")
    tw = max(text_width(s, RENDER_SIZE[SIZE_TEXT], mono=True) for s in lines)   # notes are drawn in mono
    bw = w or up4(tw + 22)
    bh = up4(10 + 15 * len(lines))
    fold = 10
    rid = c.uid("note")
    c.add("nodes", f'<path id="{rid}" d="M {_f(x)},{_f(y)} H {_f(x + bw - fold)} L {_f(x + bw)},{_f(y + fold)} '
                   f'V {_f(y + bh)} H {_f(x)} Z" fill="{WHITE}" stroke="{MUTED}" stroke-width="{STROKE}" '
                   f'data-uml="note" data-box="1"/>')
    c.add("nodes", f'<path d="M {_f(x + bw - fold)},{_f(y)} V {_f(y + fold)} H {_f(x + bw)}" fill="none" '
                   f'stroke="{MUTED}" stroke-width="{STROKE}"/>')
    for i, s in enumerate(lines):
        c.text(x + 9, y + 18 + 15 * i, s, SIZE_TEXT, mono=mono, layer="nodes", inside=rid, role="note")
    return Box(x, y, bw, bh)


# =========================================================================== SEQUENCE DIAGRAM

@dataclass
class Lifeline:
    key: str
    x: float
    label: str
    keyword: str | None
    head_top: float
    head_w: float
    head_h: float
    end_y: float
    actor: bool = False
    destroyed_at: float | None = None
    created: bool = False


class SequenceDiagram(_Canvas):
    """Interaction shown as a sequence diagram inside its `sd` frame (§17.2.4.1)."""

    EXEC_W = 10
    NEST = 5

    def __init__(self, slug, title, desc, width, height, name, *, head_top=48, bottom=None):
        super().__init__(slug, title, desc, width, height, "sequence")
        self.frame = _frame(self, "sd", name)
        self.head_top = head_top
        self.bottom = bottom if bottom is not None else height - 24
        self.lifelines: dict[str, Lifeline] = {}
        self._execs: list[tuple[str, float, float, int]] = []
        self._guards: list[tuple[str, float, str, str, int]] = []

    # ---------------------------------------------------------------- lifelines
    def lifeline(self, key, x, label, *, keyword=None, actor=False, created_at=None, end_y=None):
        """Lifeline (§17.3.4.1). label is <lifelineident>: "name : Type", ": Type", "self".
        keyword: e.g. "Metaclass" for class-scope (static) calls (convention, see references/rationale.md).
        created_at: y of the creating message; the head is drawn centred on it (§17.4.4.1)."""
        if ":" not in label and label != "self" and keyword is None:
            raise ValueError("lifeline label must be '<name> : <Type>', ': <Type>' or 'self' (§17.3.4.1)")
        w = max(80, up4(max(text_width(label, SIZE_NAME),
                            text_width(f"«{keyword}»", SIZE_TEXT) if keyword else 0) + 24))
        h = 56 if actor else (46 if keyword else 32)
        top = (created_at - h / 2) if created_at is not None else self.head_top
        ll = Lifeline(key, x, label, keyword, top, w, h, end_y if end_y is not None else self.bottom,
                      actor=actor, created=created_at is not None)
        self.lifelines[key] = ll
        return ll

    def _draw_lifelines(self):
        for ll in self.lifelines.values():
            end = ll.destroyed_at if ll.destroyed_at is not None else ll.end_y
            self.add("under", f'<line x1="{_f(ll.x)}" y1="{_f(ll.head_top + ll.head_h)}" x2="{_f(ll.x)}" '
                              f'y2="{_f(end)}" stroke="{LIFELINE}" stroke-width="{STROKE}" stroke-dasharray="3,3" '
                              f'data-uml="lifeline-line"/>')
            if ll.actor:
                self._actor(ll)
                continue
            x = ll.x - ll.head_w / 2
            rid = self.rect(x, ll.head_top, ll.head_w, ll.head_h, uml="lifeline-head")
            if ll.keyword:
                self.text(ll.x, ll.head_top + 17, f"«{ll.keyword}»", SIZE_TEXT, anchor="middle",
                          layer="nodes", inside=rid, role="keyword")
                self.text(ll.x, ll.head_top + 35, ll.label, SIZE_NAME, anchor="middle", layer="nodes",
                          inside=rid, role="lifeline-name")
            else:
                self.text(ll.x, ll.head_top + 21, ll.label, SIZE_NAME, anchor="middle", layer="nodes",
                          inside=rid, role="lifeline-name")
            if ll.destroyed_at is not None:
                y = ll.destroyed_at
                self.line(ll.x - 8, y - 8, ll.x + 8, y + 8, layer="nodes", width=1.5)
                self.line(ll.x - 8, y + 8, ll.x + 8, y - 8, layer="nodes", width=1.5)

    def _actor(self, ll):
        x, t = ll.x, ll.head_top
        s = (f'<g data-uml="actor"><circle cx="{_f(x)}" cy="{_f(t + 6)}" r="6" fill="{WHITE}" stroke="{INK}"/>'
             f'<path d="M {_f(x)},{_f(t + 12)} V {_f(t + 26)} M {_f(x - 9)},{_f(t + 17)} H {_f(x + 9)} '
             f'M {_f(x)},{_f(t + 26)} L {_f(x - 8)},{_f(t + 36)} M {_f(x)},{_f(t + 26)} L {_f(x + 8)},{_f(t + 36)}" '
             f'fill="none" stroke="{INK}"/></g>')
        self.add("nodes", s)
        self.text(x, t + 50, ll.label, SIZE_TEXT, anchor="middle", layer="nodes", role="lifeline-name")

    def destroy(self, key, y):
        """DestructionOccurrenceSpecification: X at the bottom of the lifeline (§17.4.4.2)."""
        self.lifelines[key].destroyed_at = y

    # ---------------------------------------------------------------- execution
    def _edge(self, key, level, side):
        """x of an execution's left/right edge at nesting level (None -> the lifeline line itself)."""
        ll = self.lifelines[key]
        if level is None:
            return ll.x
        left = ll.x - self.EXEC_W / 2 + self.NEST * level
        return left + self.EXEC_W if side > 0 else left

    def execution(self, key, y1, y2, level=0):
        """ExecutionSpecification (§17.2.4.4): thin rectangle; nested levels overlap (Figure 17.2)."""
        x = self._edge(key, level, -1)
        self._execs.append((key, y1, y2, level))
        self.add("nodes", f'<rect x="{_f(x)}" y="{_f(y1)}" width="{self.EXEC_W}" height="{_f(y2 - y1)}" '
                          f'fill="{EXEC_FILL}" stroke="{MUTED}" stroke-width="0.8" data-uml="execution"/>')

    # ---------------------------------------------------------------- messages
    def message(self, kind, src, dst, y, label=None, *, src_level=0, dst_level=0, label_x=None,
                label_dx=0):
        """Message (§17.4.4.1).

        kind: 'sync'  solid line, filled head      request label "op(args)"
              'async' solid line, open head        request label "op(args)" / "signal"
              'reply' dashed line, open head       "[target =] op(args) [: value]" or None if obvious
              'create' dashed line, open head, ends at dst's head (dst must be created_at=y)
              'delete' solid line, filled head, dst gets an X at y
              'found' src is an x: a black dot marks the unknown sender; filled head for 'op(...)'
        src/dst: lifeline keys (found: src is an x coordinate).
        """
        if kind not in ("sync", "async", "reply", "create", "delete", "found"):
            raise ValueError(f"unknown message kind {kind}")
        if kind in ("sync", "create", "delete") and label and "(" not in label:
            raise ValueError(f"request label must be an operation call 'name(args)' (§17.4.4.1): {label!r}")
        x1 = self._x_of(src, dst, src_level, is_src=True)
        x2 = self._x_of(dst, src, dst_level, is_src=False, create=(kind == "create"))
        if kind == "delete":
            self.destroy(dst, y)
            x2 = self.lifelines[dst].x
        dashed = kind in ("reply", "create")
        if kind == "found":
            head = "filled" if label and "(" in label else "open"   # operation call vs signal
        else:
            head = "filled" if kind in ("sync", "delete") else "open"
        u = (1.0 if x2 > x1 else -1.0, 0.0)
        self.add("edges", f'<g data-uml="message" data-kind="{kind}" data-head="{head}" '
                          f'data-dashed="{str(dashed).lower()}">')
        end_x = x2 - u[0] * (10 if head == "filled" else 0)
        start_x = x1
        if kind == "found":
            self.add("edges", f'<circle cx="{_f(x1)}" cy="{_f(y)}" r="4" fill="{MUTED}"/>')
        self.line(start_x, y, end_x, y, dash="5,4" if dashed else None, color=MUTED, width=1.2)
        if head == "filled":
            _arrow_filled(self, (x2, y), u)
        else:
            _arrow_open(self, (x2, y), u)
        self.add("edges", "</g>")
        if label:
            lx = label_x if label_x is not None else (x1 + x2) / 2 + label_dx
            self.text(lx, y - 6, label, SIZE_TEXT, anchor="middle", halo=True, role="message-label")

    def _x_of(self, key, other, level, *, is_src, create=False):
        if isinstance(key, (int, float)):
            return float(key)
        ll = self.lifelines[key]
        ox = self._x_ref(other)
        side = 1 if ox > ll.x else -1
        if create:
            return ll.x + side * ll.head_w / 2          # the head edge facing the sender
        return self._edge(key, level, side)

    def _x_ref(self, key):
        if isinstance(key, (int, float)):
            return float(key)
        return self.lifelines[key].x

    def self_message(self, key, y, label, *, kind="sync", from_level=0, to_level=1, dy=20, dx=32):
        """Message to self: leaves the execution at from_level, returns into a nested execution."""
        x1 = self._edge(key, from_level, 1)
        x2 = self._edge(key, to_level, 1)
        xo = max(x1, x2) + dx
        head = "filled" if kind == "sync" else "open"
        self.add("edges", f'<g data-uml="message" data-kind="{kind}" data-head="{head}" data-dashed="false">')
        endx = x2 + (10 if head == "filled" else 0)
        self.add("edges", f'<path d="M {_f(x1)},{_f(y)} H {_f(xo)} V {_f(y + dy)} H {_f(endx)}" fill="none" '
                          f'stroke="{MUTED}" stroke-width="1.2"/>')
        if head == "filled":
            _arrow_filled(self, (x2, y + dy), (-1.0, 0.0))
        else:
            _arrow_open(self, (x2, y + dy), (-1.0, 0.0))
        self.add("edges", "</g>")
        self.text(xo + 6, y + dy / 2 + 4, label, SIZE_TEXT, halo=True, role="message-label")

    # ---------------------------------------------------------------- fragments
    def fragment(self, operator, x1, x2, y1, y2, operands):
        """CombinedFragment (§17.6.4.3): rectangle, operator in a pentagon, operands split by dashed lines.

        operator: alt | opt | loop | loop(min,max) | par | break
        operands: list of dicts {"top": y where the operand starts (first = y1; later = divider y),
                                 "guard": "[cond]" or None, "on": lifeline key the first event happens on}
        """
        base = operator.split("(")[0].split(" ")[0]
        if base not in ("alt", "opt", "loop", "par", "break"):
            raise ValueError(f"unknown interaction operator {operator}")
        self.add("under", f'<rect x="{_f(x1)}" y="{_f(y1)}" width="{_f(x2 - x1)}" height="{_f(y2 - y1)}" '
                          f'fill="{FRAG_FILL}" stroke="{FRAME}" stroke-width="{STROKE}" data-uml="fragment" '
                          f'data-operator="{escape(base)}"/>')
        tag_w, tag_h = self.name_tag(x1, y1, [(operator, True)], layer="over", uml="fragment-operator",
                                     min_w=40)
        for i, op in enumerate(operands):
            top = op["top"]
            if i > 0:
                self.add("under", f'<line x1="{_f(x1)}" y1="{_f(top)}" x2="{_f(x2)}" y2="{_f(top)}" '
                                  f'stroke="{FRAME}" stroke-width="{STROKE}" stroke-dasharray="5,4" '
                                  f'data-uml="operand-divider"/>')
            g = op.get("guard")
            if g:
                if not (g.startswith("[") and g.endswith("]")):
                    raise ValueError("guard must be written in square brackets (§17.6.4.2)")
                gy = op.get("guard_y", top + (tag_h + 14 if i == 0 else 16))
                self._guards.append((op["on"], gy, g))

    def note(self, x, y, lines, *, links=(), w=None, mono=False):
        return _note(self, x, y, lines, links=links, w=w, mono=mono)

    def _draw_guards(self):
        """Guards (§17.6.4.2) on the lifeline of the operand's first event, drawn once every execution is
        known: covering the lifeline where it is idle, beside its activation bar where it is active."""
        for key, gy, g in self._guards:
            ll = self.lifelines[key]
            busy = [e for e in self._execs if e[0] == key and e[1] - 2 <= gy <= e[2] + 12]
            if not busy:
                gx = ll.x - 6
                w = text_width(g, SIZE_SMALL) + 6
                self.add("labels", f'<rect x="{_f(gx - 3)}" y="{_f(gy - 11)}" width="{_f(w)}" height="15" '
                                   f'fill="{PAPER}" stroke="none"/>')
                self.text(gx, gy, g, SIZE_SMALL, role="guard")
            else:
                lvl = max(e[3] for e in busy)
                self.text(self._edge(key, lvl, 1) + 3, gy, g, SIZE_SMALL, halo=True, role="guard")

    def svg(self):
        if not getattr(self, "_drawn", False):
            self._draw_lifelines()
            self._draw_guards()
            self._drawn = True
        return super().svg()


# =========================================================================== page

@dataclass
class Figure:
    diagram: _Canvas
    caption: str


PAGE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#2d3142;--muted:#4f5d75;--paper:#f5f5f5;--rule:rgba(45,49,66,0.12)}
body{background:var(--paper);color:var(--ink);font-family:'Geist',Arial,'Liberation Sans',sans-serif;
  line-height:1.5;padding:48px 16px}
main{max-width:1000px;margin:0 auto;min-width:0}
nav{font-family:'Geist Mono','Liberation Mono',monospace;font-size:12px;letter-spacing:.04em;margin-bottom:32px}
nav a{color:var(--muted);margin-right:16px;text-decoration:none;border-bottom:1px solid transparent}
nav a:hover{border-bottom-color:var(--muted)}
nav a[aria-current]{color:var(--ink);border-bottom-color:var(--ink)}
.eyebrow{font-family:'Geist Mono','Liberation Mono',monospace;font-size:11px;font-weight:500;letter-spacing:.18em;
  text-transform:uppercase;color:var(--muted);margin-bottom:6px}
h1{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:clamp(28px,4vw,40px);
  letter-spacing:-.02em;line-height:1.1;margin-bottom:10px}
.intent{font-size:15px;color:var(--muted);max-width:44rem;margin-bottom:36px}
figure{margin:0 0 44px}
.scroll{width:100%;overflow-x:auto}
svg{display:block;width:100%;height:auto;margin:0 auto}
figcaption{font-size:13px;color:var(--muted);text-align:center;margin-top:12px}
figcaption b{color:var(--ink);font-weight:600}
@media print{.scroll{overflow-x:visible}svg{min-width:0!important;max-width:100%!important}nav{display:none}figure{break-inside:avoid}}
"""


def page_html(title, figures, *, intro=None, nav=None, current=None, lang="en", first_number=1):
    """Self-contained page: h1, optional intro, numbered figures with captions below (academic style).
    nav: list of (href, label); current: href of this page."""
    navs = ""
    if nav:
        here = ' aria-current="page"'
        links = "".join(f'<a href="{escape(h)}"{here if h == current else ""}>{escape(t)}</a>'
                        for h, t in nav)
        navs = f'<nav aria-label="Diagrams">{links}</nav>'
    figs = []
    for i, f in enumerate(figures, first_number):
        figs.append(f'<figure>\n<div class="scroll">\n{f.diagram.svg()}\n</div>\n'
                    f'<figcaption><b>Figure {i}.</b> {escape(f.caption)}</figcaption>\n</figure>')
    intro_html = f'<p class="intent">{escape(intro)}</p>' if intro else ""
    return (f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>{escape(title)}</title>\n'
            f'<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1'
            f'&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">\n'
            f'<style>{PAGE_CSS}</style>\n</head>\n<body>\n<main>\n{navs}\n'
            f'<p class="eyebrow">UML 2.5.1</p>\n<h1>{escape(title)}</h1>\n'
            f'{intro_html}\n' + "\n".join(figs) + "\n</main>\n</body>\n</html>\n")


def write_page(path, title, figures, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page_html(title, figures, **kw))


__all__ = ["ClassDiagram", "SequenceDiagram", "Attr", "Op", "End", "Box", "Figure", "page_html",
           "write_page", "text_width", "up4"]
