"""Every primitive of the library on one page; also the visual regression page.

    python3 notation_reference.py <output-dir>      # writes notation-reference.html
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from umlsvg import Attr, ClassDiagram, End, Figure, Op, SequenceDiagram, write_page  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def class_diagram():
    cd = ClassDiagram("ref-class", "Class diagram primitives",
                      "An abstract Account realizes Auditable and is specialised by Savings; a Customer owns "
                      "accounts; a Bank aggregates customers; Account uses the Currency enumeration.",
                      width=900, height=400)
    aud = cd.klass(40, 20, "Auditable", keywords=("interface",), attrs=[], ops=["+audit(): Boolean"], w=180)
    acct = cd.klass(360, 20, "Account", abstract=True,
                    attrs=["-number: String", Attr("-count: Integer", static=True)],
                    ops=[Op("+fee(): Real", abstract=True), "+deposit(amount: Real)"], w=220)
    cur = cd.klass(700, 20, "Currency", keywords=("enumeration",), literals=["EUR", "USD", "TRY"], w=140)
    sav = cd.klass(360, 220, "Savings", attrs=["-rate: Real"], ops=["+fee(): Real"], w=220)
    cust = cd.klass(40, 220, "Customer", attrs=["-name: String"], ops=[], w=180)
    bank = cd.klass(700, 220, "Bank", attrs=[], ops=["+open(c: Customer): Account"], w=180)
    cd.generalization([acct.w_(64), aud.e(64)], realization=True)
    cd.generalization([sav.n(), acct.s()])
    cd.dependency([acct.e(56), cur.w_(56)], "use")
    cd.association([cust.n(130), (130, 168), (400, 168), acct.s(400)],
                   End(mult="1", aggregation="composite"), End(role="-accounts", mult="1..*", navigable=True),
                   name="owns", name_at=(270, 162))
    cd.association([bank.s(790), (790, 350), (130, 350), cust.s(130)],
                   End(aggregation="shared"), End(role="-customers", mult="*", navigable=True))
    cd.note(600, 140, ["fee() depends on the", "account kind"], links=[[acct.e(101), (620, 101), (620, 140)]])
    return cd


def sequence_diagram():
    sd = SequenceDiagram("ref-seq", "Sequence diagram primitives",
                         "A user opens an account through the bank, which creates it; the bank checks the account "
                         "in a loop, notifies asynchronously and finally deletes a temporary object.",
                         width=860, height=520, name="openAccount")
    sd.lifeline("u", 90, ": User", actor=True)
    sd.lifeline("b", 300, "bank : Bank")
    sd.lifeline("a", 540, "a : Account", created_at=176)
    sd.lifeline("t", 760, "tmp : Validator")
    sd.execution("u", 120, 448)
    sd.execution("b", 120, 440)
    sd.message("sync", "u", "b", 120, "open(c)")
    sd.self_message("b", 136, "check(c)")
    sd.execution("b", 156, 168, level=1)
    sd.message("create", "b", "a", 176, "Account()")
    sd.fragment("alt", 40, 820, 216, 336, [
        {"top": 216, "guard": "[valid]", "on": "b"},
        {"top": 296, "guard": "[else]", "on": "b"}])
    sd.execution("t", 256, 284)
    sd.message("sync", "b", "t", 256, "validate(a)", label_x=650)
    sd.message("reply", "t", "b", 284, "validate(a): ok", label_x=650)
    sd.message("async", "b", "u", 324, "warn()")
    sd.fragment("loop(1,3)", 250, 620, 344, 416, [{"top": 344, "guard": "[pending]", "on": "a"}])
    sd.execution("a", 400, 412)
    sd.message("sync", "b", "a", 400, "verify()")
    sd.message("delete", "b", "t", 428, "destroy()", label_x=650)
    sd.message("reply", "b", "u", 440, "open(c): a")
    return sd


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write_page(OUT / "notation-reference.html", "UML notation reference",
               [Figure(class_diagram(), "Class diagram primitives."),
                Figure(sequence_diagram(), "Sequence diagram primitives.")],
               intro="Every primitive of create-uml-seq-diagram.")
    print(f"wrote {OUT / 'notation-reference.html'}")
