"""Copy this file, fill in the model, run it, then run the checker.

    python3 build.py out.html
    python3 <skill-dir>/scripts/check_uml.py --render --shot shots out.html
"""

import sys

sys.path.insert(0, "<skill-dir>/scripts")  # replace <skill-dir> with the skill's absolute path
from umlsvg import Attr, ClassDiagram, End, Figure, Op, SequenceDiagram, write_page  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "out.html"

# ---- class diagram ----------------------------------------------------------------------------
cd = ClassDiagram("shop-class", "Shop, class diagram",
                  "One sentence saying what the diagram shows.", width=760, height=260)
shape = cd.klass(40, 20, "Shape", abstract=True, attrs=["#name: String"],
                 ops=[Op("+area(): Real", abstract=True)], w=200)
circle = cd.klass(40, 160, "Circle", attrs=["-radius: Real"], ops=["+area(): Real"], w=200)
canvas = cd.klass(460, 20, "Canvas", attrs=[], ops=["+draw()"], w=160)
cd.generalization([circle.n(140), shape.s(140)])
cd.association([canvas.w_(60), shape.e(60)],
               End(mult="1", aggregation="composite"), End(role="-shapes", mult="*", navigable=True))

# ---- sequence diagram -------------------------------------------------------------------------
sd = SequenceDiagram("shop-seq", "Shop, drawing", "One sentence saying what happens.",
                     width=620, height=260, name="draw")
sd.lifeline("cv", 120, ": Canvas")
sd.lifeline("c", 420, "c : Circle")
sd.execution("cv", 104, 176)
sd.execution("c", 112, 144)
sd.message("found", 40, "cv", 104, "draw()", label_x=80)
sd.message("sync", "cv", "c", 112, "area()")
sd.message("reply", "c", "cv", 144, "area(): a")

write_page(out, "Shop", [Figure(cd, "Shop, UML class diagram."),
                         Figure(sd, "Shop, UML sequence diagram.")])
print("wrote", out)
