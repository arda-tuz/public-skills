---
name: create-uml-seq-diagram
description: Draw UML class diagrams and UML sequence diagrams in correct, exam-level UML 2.5.1 notation as self-contained HTML/SVG (PNG/SVG export on request). Use for class/structure diagrams (classes, interfaces, abstract classes, attributes, operations, static members, generalization, realization, association with roles/multiplicity/navigability, aggregation, composition, enumerations, dependencies, notes), sequence/interaction diagrams (sd frame, lifelines, actors, activations, sync/async/reply/create/found/delete messages, self-calls, alt/opt/loop/par/break fragments), and design-pattern diagrams such as GoF structure and collaboration.
license: MIT
metadata:
  version: "2.0"
  forked-from: diagram-design 2.6.78 (Cathryn Lavery, MIT)
  standard: OMG UML 2.5.1
---

# Create UML class and sequence diagrams

Goal: diagrams a strict examiner gives full marks: every symbol standard, **nothing optional added**. A Python library (`scripts/umlsvg.py`) draws the notation in a fixed look (diagram-design's palette and Geist type); you only model and place boxes.

## Workflow (4 steps)

1. **Model in text first.** Class diagram: classes with keyword/abstractness, `-attr: Type`, `+op(p: Type): Type`, then relationships with kind, role, multiplicity, navigability. Sequence diagram: lifelines `name : Type`, then messages in time order with their kind. Every message must name an operation of the receiver's class.
2. **Build.** Copy `assets/template.py`, replace `<skill-dir>` with this directory's absolute path, fill in the model, run `python3 build.py out.html`. For GoF patterns start from `assets/examples/gof_patterns.py`.
3. **Check and look:**
   ```bash
   python3 <skill-dir>/scripts/check_uml.py --render --shot shots out.html
   ```
   It must print `OK`. Then Read `shots/out.png` and fix anything crowded, overlapping or touching (move boxes, add space, use `label_x`), and rerun.
4. **Deliver** the HTML. Export only on request: `python3 <skill-dir>/scripts/export.py out.html [--format svg|png]`.

## API

Coordinates are px. A box returns attach points `n(x)`, `s(x)`, `w_(y)`, `e(y)` on its edges (absolute coordinates; omit for the centre). Connectors are lists of points with horizontal/vertical segments only.

| Need | Call |
|---|---|
| Class diagram | `cd = ClassDiagram(slug, title, desc, width, height)` |
| Class | `cd.klass(x, y, "Name", attrs=[...], ops=[...], w=None)`; `attrs=None, ops=None` gives a name-only box |
| Interface / abstract / enum | `keywords=("interface",)` / `abstract=True` (italic name) / `keywords=("enumeration",), literals=["RED", "GREEN"]` |
| Static / abstract member | `Attr("-x: T", static=True)`, `Op("+m(): T", static=True)`, `Op("+m(): T", abstract=True)` |
| Inheritance | `cd.generalization([child.n(), parent.s()])`; several children: `cd.generalization_tree([c1.n(), c2.n()], parent.s(), bus_y)` |
| Interface realization | same calls with `realization=True` |
| Association | `cd.association(pts, End(...), End(...))`; `End(role="-items", mult="*", navigable=True)`; optional `name="owns", name_at=(x, y)` |
| Aggregation / composition | `End(aggregation="shared")` / `End(aggregation="composite", mult="1")` on the **whole's** end |
| Dependency | `cd.dependency(pts, "use")`; creation: `"Instantiate"` |
| Note | `cd.note(x, y, ["line", ...], links=[pts])` |
| Sequence diagram | `sd = SequenceDiagram(slug, title, desc, width, height, name="operationName")` |
| Lifeline | `sd.lifeline(key, x, "name : Type")`; created later: `created_at=y`; actor: `actor=True`; static calls: `sd.lifeline(key, x, "Cls", keyword="Metaclass")` |
| Activation | `sd.execution(key, y1, y2, level=0)` (level 1 for a self-call) |
| Message | `sd.message(kind, src, dst, y, "op()")`; kind `sync`, `async`, `reply`, `create`, `delete` (X ends the target); `found` with `src` = an x coordinate; reply label optional; `label_x=` moves a label off other lifelines |
| Self call | `sd.self_message(key, y, "op()")` |
| Fragment | `sd.fragment("opt", x1, x2, y1, y2, [{"top": y1, "guard": "[cond]", "on": key}])`; `alt`: add `{"top": y_div, "guard": "[else]", "on": key}`; also `loop`, `loop(1,3)`, `par`, `break`; the frame must span every lifeline its messages touch |
| Page | `write_page("out.html", "Title", [Figure(cd, "caption"), Figure(sd, "caption")])` |

Nothing beyond this table is supported on purpose: it is what an exam asks for.

## Exam checklist

**Class diagram**
- Box: bold centred name; interface `«interface»` above it; abstract class name in *italics*; abstract operations in *italics*.
- Members: `-name: Type`, `+op(p: Type): Type`; no `: void` (omit the return type); UML types `Integer`, `Boolean`, `String`, `Real`; static members underlined.
- Both compartments drawn when members are shown (an empty one means "none").
- Inheritance: solid line, hollow triangle at the parent. Realization: dashed line, hollow triangle at the interface.
- Association: plain solid line; open arrowhead only to show navigability; role name and multiplicity at the end they describe.
- Aggregation hollow, composition filled diamond, at the whole.
- Dependency: dashed open arrow with a keyword (`«use»`, `«Instantiate»`).
- Notes: folded-corner box, dashed line without arrowhead.

**Sequence diagram**
- Everything inside an `sd name` frame; heads read `name : Type` (not underlined).
- Sync call: solid line, filled head. Async: solid line, open head. Reply: dashed line, open head. Create: dashed line, open head, pointing at the new object's box drawn at that height.
- Activation bars for every call; self-calls nested.
- Fragments: `opt`/`alt`/`loop` in a corner tab, guards `[cond]`, `alt` operands separated by a dashed line.
- Messages carry operation calls `op(args)`; replies `op(): value` or no label; no message numbers.

**Never add:** your own colours (the library applies one fixed palette), legends, rounded boxes, ALL-CAPS labels, `<<` `>>` instead of `«` `»`, `«abstract»`, multiplicities you cannot justify from the model, a frame around class diagrams, members the question does not need.

## Files

| File | Read when |
|---|---|
| `assets/template.py` | always: the starting point |
| `assets/examples/gof_patterns.py` | drawing a GoF pattern |
| `references/notation.md` | unsure whether a notation is standard; clause numbers for a justification |
| `references/rationale.md` | asked why this skill differs from diagram-design or from a tool's output |
| `assets/examples/notation_reference.py` | you want to see every primitive drawn |

The library and the checker refuse non-standard input (diagonal lines, `«abstract»`, guards without brackets, request labels without `()`, `<< >>`, numbered messages, symbols outside the frame); read the error, fix the input.
