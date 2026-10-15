# Why this skill looks the way it does

## Target

Exam-level UML 2.5.1: everything a strict examiner checks is standard, nothing optional is added. "Allowed by the spec" is not a reason to draw something; "needed by the model or the question" is.

## What the parent skill (diagram-design) got wrong for UML

| Parent behaviour | Correct notation | § |
|---|---|---|
| colour-coded focal nodes and links, legends, rounded boxes, tag chips | one neutral palette with no colour meaning, square corners, no legend | 9.2.4.1, 17.3.4.1 |
| ALL-CAPS labels, 14-char limit | exact identifiers: `factoryMethod()` | 17.4.4.1 |
| async drawn dashed | async solid with open head (dashed open = create) | 17.4.4.1 |
| reply labels like `RESULT` | `op(): value` or no label | 17.4.4.1 |
| no `sd` frame | `sd name` frame | 17.2.4.1 |
| `OPT` in a rounded tab | `opt` in a pentagon | 17.6.4.3 |
| creation drawn as a plain call | dashed create arrow to a head drawn at that height | 17.4.4.1 |
| `«abstract»`, `: void`, `bool` | italic name; no return type; `Boolean` | Annex C, 9.6.4 |
| association drawn with an arrow by default | arrowhead only for navigability | 11.5.4 |
| attribute and association for the same property | show it once | 11.5.4 |
| italic serif callouts | UML note symbol | 7.2.4 |

## Choices that are conventions, not rules

| Choice | Why |
|---|---|
| Abstract operations in italics only | textbook norm; 2.5.1 defines no notation |
| `«Metaclass»` lifeline for static calls | Larman, *Applying UML and Patterns* §15.4 |
| Reply arrowhead open | spec allows open or filled; open differs from a call |
| Empty attributes compartment shown | an empty compartment means "none"; a missing one means "unknown" |
| Constructors as `-Name()` | exam norm; §11.4.4's `«Create» Name(): Name` is legal but unusual |
| Keywords lower case (`«use»`), profile stereotypes capitalised (`«Instantiate»`) | StandardProfile names; OMG issues UML25-457/494 |
| No frame on class diagrams, `sd` frame on sequence diagrams | Annex A makes frames optional; the interaction frame is the expected UML 2 form |

## Tool and textbook notations not adopted

`<<keyword>>` (use guillemets), numbered messages on sequence diagrams, filled realization triangles, language types (`void`, `int`, pointers), Larman's filled head on create messages (spec: open).

## Sources

OMG UML 2.5.1 specification (formal/17-12-05); GoF *Design Patterns* (1994); Fowler *UML Distilled* 3e; Larman *Applying UML and Patterns* 3e; uml-diagrams.org; IBM, Sparx and Visual Paradigm guides (checked against the spec).

## Deliberately not supported

Packages, constraints (`{xor}`, `{ordered}`), stereotype property values, ball-and-socket interfaces, `ref`, gates, lost messages, state invariants and the rarer fragment operators are standard UML but beyond exam level; leaving them out keeps agents from adding them.
