# Notation rules with clause numbers (OMG UML 2.5.1, formal/17-12-05)

Use this to check a notation or justify it. The library already implements every rule.

## Class diagram

| Element | Rule | § |
|---|---|---|
| Class | solid rectangle; name centred, bold, capitalised; compartments: attributes, then operations | 9.2.4.1 |
| Suppressed vs empty compartment | a suppressed compartment says nothing; draw both compartments when members are shown | 9.2.4.1 |
| Interface | keyword `«interface»` above the name | 10.4.4 |
| Abstract class | name in italics (or `{abstract}` after/below the name); `«abstract»` is not a keyword | 9.2.4.1, Annex C |
| Abstract operation | italics (convention; 2.5.1 defines no notation) | 9.4 |
| Attribute | `[vis] [/] name [: Type] [[mult]] [= default] [{props}]` | 9.5.4 |
| Operation | `[vis] name([dir] p: Type, ...) [: ReturnType]`; no return type means none (no `void`) | 9.6.4 |
| Visibility | `+` public, `-` private, `#` protected, `~` package | 9.5.4 |
| Static | underlined | 9.4.4 |
| Generalization | solid line, hollow triangle at the general class; several may share one triangle | 9.2.4.2 |
| Interface realization | dashed line, hollow triangle at the interface | 7.7.4 |
| Association | solid line; open arrowhead = navigable end, x = not navigable, nothing = unspecified | 11.5.4 |
| Role / multiplicity | near the end they describe | 11.5.4 |
| Aggregation / composition | hollow / filled diamond at the whole; composite end multiplicity 1 or 0..1 | 11.5.4, 9.5.3 |
| Dependency | dashed line, open arrowhead at the supplier, keyword in guillemets (`«use»`, `«Instantiate»`) | 7.7.4 |
| Note | rectangle with a folded corner, dashed connector without arrowhead | 7.2.4 |
| Keywords | in guillemets `« »`; `<< >>` only where the character set lacks guillemets | Annex C |

## Sequence diagram

| Element | Rule | § |
|---|---|---|
| Frame | rectangle with a pentagon `sd name` in the top-left corner | 17.2.4.1 |
| Lifeline | rectangle head `name : Type` or `: Type` (not underlined), dashed line below | 17.3.4.1 |
| Activation | thin grey/white rectangle on the lifeline; nested ones overlap shifted right | 17.2.4.4 |
| Synchronous call | solid line, filled arrowhead | 17.4.4.1 |
| Asynchronous message | solid line, open arrowhead | 17.4.4.1 |
| Reply | dashed line (open head here); label `[x =] op(...) [: value]` or none when obvious | 17.4.4.1 |
| Create | dashed line, open arrowhead, ends at the head of the new lifeline drawn at that height | 17.4.4.1 |
| Found message | black dot at the start (sender not shown) | 17.4.4.1 |
| Destruction | X at the bottom of the lifeline | 17.4.4.2 |
| Request label | `op(args)`, exact case | 17.4.4.1 |
| Combined fragment | rectangle, lowercase operator in a pentagon, operands split by dashed lines | 17.6.4.3 |
| Guard | `[condition]` or `[else]` on the lifeline of the operand's first event | 17.6.4.2 |
| Loop bounds | `loop(min,max)`, `*` = unbounded | 17.6.4.9 |
| Message numbers | not sequence-diagram notation (communication diagrams only) | 17.9.1.3 |

## Conventions this skill fixes (spec is silent or allows several)

- Reply arrowhead open.
- Static call receiver: lifeline `«Metaclass» ClassName` (Larman).
- Guard placed right of the activation bar when the lifeline is active.
- `sd` frame always on sequence diagrams; no frame on class diagrams.
- Skin: diagram-design's palette (ink `#2d3142`, slate `#4f5d75`, paper `#f5f5f5`, white boxes) without its accent colours, Geist / Geist Mono / Instrument Serif, square corners. Colour never carries meaning.
