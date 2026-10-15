"""Worked example: GoF Decorator, Proxy, Factory Method and Singleton, each as a UML class diagram
(structure) and a sequence diagram (collaboration), at exam level: standard notation, nothing optional.

    python3 gof_patterns.py <output-dir>

Writes decorator.html, proxy.html, factory-method.html, singleton.html.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from umlsvg import Attr, ClassDiagram, End, Figure, Op, SequenceDiagram, write_page  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
NAV = [("decorator.html", "Decorator"), ("proxy.html", "Proxy"),
       ("factory-method.html", "Factory Method"), ("singleton.html", "Singleton")]
NB = " "  # indentation inside notes


def page(slug, title, intro, figs):
    write_page(OUT / f"{slug}.html", title, figs, intro=intro, nav=NAV, current=f"{slug}.html")


def decorator():
    cd = ClassDiagram("decorator-class", "Decorator pattern, class diagram",
                      "ConcreteComponent and the abstract Decorator realize the Component interface; Decorator "
                      "aggregates the Component it wraps; ConcreteDecoratorA and B specialize Decorator.",
                      width=920, height=420)
    client = cd.klass(20, 36, "Client")
    comp = cd.klass(340, 20, "Component", keywords=("interface",), attrs=[], ops=["+operation()"], w=180)
    cc = cd.klass(130, 180, "ConcreteComponent", attrs=[], ops=["+operation()"], w=180)
    dec = cd.klass(480, 180, "Decorator", abstract=True, attrs=[], ops=["+operation()"], w=180)
    da = cd.klass(340, 320, "ConcreteDecoratorA", attrs=["-addedState: String"], ops=["+operation()"], w=180)
    db = cd.klass(580, 320, "ConcreteDecoratorB", attrs=[], ops=["+operation()", "-addedBehavior()"], w=200)
    cd.dependency([client.e(52), comp.w_(52)], "use")
    cd.generalization_tree([cc.n(), dec.n()], comp.s(), 140, realization=True)
    cd.association([dec.e(200), (720, 200), (720, 60), comp.e(60)],
                   End(aggregation="shared"), End(role="-component", mult="1", navigable=True))
    cd.generalization_tree([da.n(), db.n()], dec.s(), 284)
    cd.note(760, 150, ["component.operation()"], links=[[(820, 178), (820, 232), dec.e(232)]])
    cd.note(792, 340, ["super.operation()", "addedBehavior()"], links=[[(792, 373), db.e(373)]])

    sd = SequenceDiagram("decorator-seq", "Decorator pattern, sequence diagram",
                         "A client calls operation on decorator b, which forwards to decorator a, which forwards "
                         "to the concrete component; on the way back b runs its added behaviour.",
                         width=900, height=400, name="operation")
    sd.lifeline("cl", 100, ": Client")
    sd.lifeline("b", 330, "b : ConcreteDecoratorB")
    sd.lifeline("a", 570, "a : ConcreteDecoratorA")
    sd.lifeline("c", 790, "c : ConcreteComponent")
    sd.execution("cl", 104, 360)
    sd.execution("b", 112, 352)
    sd.execution("a", 152, 248)
    sd.execution("c", 192, 224)
    sd.execution("b", 300, 324, level=1)
    sd.message("sync", "cl", "b", 112, "operation()")
    sd.message("sync", "b", "a", 152, "operation()")
    sd.message("sync", "a", "c", 192, "operation()")
    sd.message("reply", "c", "a", 224)
    sd.message("reply", "a", "b", 248)
    sd.self_message("b", 280, "addedBehavior()")
    sd.message("reply", "b", "cl", 352)

    page("decorator", "Decorator",
         "Attach additional responsibilities to an object dynamically. Decorators provide a flexible "
         "alternative to subclassing for extending functionality. (GoF)",
         [Figure(cd, "Decorator, UML class diagram."), Figure(sd, "Decorator, UML sequence diagram.")])


def proxy():
    cd = ClassDiagram("proxy-class", "Proxy pattern, class diagram",
                      "RealSubject and Proxy realize the Subject interface; Proxy holds a reference to the "
                      "RealSubject it stands in for and creates it on first use.",
                      width=920, height=280)
    client = cd.klass(20, 36, "Client")
    subj = cd.klass(340, 20, "Subject", keywords=("interface",), attrs=[], ops=["+request()"], w=180)
    real = cd.klass(130, 180, "RealSubject", attrs=[], ops=["+request()"], w=180)
    prx = cd.klass(480, 180, "Proxy", attrs=[], ops=["+request()"], w=180)
    cd.dependency([client.e(52), subj.w_(52)], "use")
    cd.generalization_tree([real.n(), prx.n()], subj.s(), 140, realization=True)
    cd.association([prx.w_(212), real.e(212)], End(),
                   End(role="-realSubject", mult="0..1", navigable=True))
    cd.note(678, 205, ["if (realSubject == null)", f"{NB * 4}realSubject = new RealSubject();",
                       "realSubject.request();"], links=[[prx.e(233), (678, 233)]])

    sd = SequenceDiagram("proxy-seq", "Proxy pattern, sequence diagram",
                         "The client calls request on the proxy, which creates the real subject on first use and "
                         "forwards the request to it.", width=760, height=400, name="request")
    sd.lifeline("cl", 110, ": Client")
    sd.lifeline("p", 340, "proxy : Proxy")
    sd.lifeline("r", 600, "realSubject : RealSubject", created_at=200)
    sd.fragment("opt", 290, 720, 140, 240, [{"top": 140, "guard": "[realSubject == null]", "on": "p"}])
    sd.execution("cl", 104, 312)
    sd.execution("p", 112, 304)
    sd.execution("r", 256, 280)
    sd.message("sync", "cl", "p", 112, "request()")
    sd.message("create", "p", "r", 200, "RealSubject()")
    sd.message("sync", "p", "r", 256, "request()")
    sd.message("reply", "r", "p", 280)
    sd.message("reply", "p", "cl", 304)

    page("proxy", "Proxy",
         "Provide a surrogate or placeholder for another object to control access to it. (GoF)",
         [Figure(cd, "Proxy, UML class diagram."), Figure(sd, "Proxy, UML sequence diagram.")])


def factory_method():
    cd = ClassDiagram("factory-method-class", "Factory Method pattern, class diagram",
                      "The abstract Creator declares factoryMethod and calls it in anOperation; ConcreteCreator "
                      "overrides it to instantiate ConcreteProduct, which realizes the Product interface.",
                      width=760, height=340)
    creator = cd.klass(60, 20, "Creator", abstract=True, attrs=[],
                       ops=[Op("+factoryMethod(): Product", abstract=True), "+anOperation()"], w=220)
    product = cd.klass(540, 20, "Product", keywords=("interface",), attrs=[], ops=["+operation()"], w=180)
    ccreator = cd.klass(60, 204, "ConcreteCreator", attrs=[], ops=["+factoryMethod(): Product"], w=220)
    cproduct = cd.klass(540, 204, "ConcreteProduct", attrs=[], ops=["+operation()"], w=180)
    cd.generalization([ccreator.n(170), creator.s(170)])
    cd.generalization([cproduct.n(630), product.s(630)], realization=True)
    cd.dependency([ccreator.e(238), cproduct.w_(238)], "Instantiate")
    cd.note(320, 75, ["product = factoryMethod()"], links=[[creator.e(89), (320, 89)]])
    cd.note(76, 300, ["return new ConcreteProduct()"], links=[[(140, 300), ccreator.s(140)]])

    sd = SequenceDiagram("factory-method-seq", "Factory Method pattern, sequence diagram",
                         "The client calls anOperation on a concrete creator, which calls its own factoryMethod; "
                         "that creates a concrete product, which anOperation then uses.",
                         width=780, height=380, name="anOperation")
    sd.lifeline("cl", 110, ": Client")
    sd.lifeline("cr", 350, "creator : ConcreteCreator")
    sd.lifeline("pr", 620, "product : ConcreteProduct", created_at=196)
    sd.execution("cl", 104, 328)
    sd.execution("cr", 112, 320)
    sd.execution("cr", 164, 236, level=1)
    sd.execution("pr", 212, 228)
    sd.execution("pr", 268, 292)
    sd.message("sync", "cl", "cr", 112, "anOperation()")
    sd.self_message("cr", 144, "factoryMethod()")
    sd.message("create", "cr", "pr", 196, "ConcreteProduct()", src_level=1)
    sd.message("reply", "pr", "cr", 228, dst_level=1)
    sd.message("sync", "cr", "pr", 268, "operation()")
    sd.message("reply", "pr", "cr", 292)
    sd.message("reply", "cr", "cl", 320)

    page("factory-method", "Factory Method",
         "Define an interface for creating an object, but let subclasses decide which class to "
         "instantiate. (GoF)",
         [Figure(cd, "Factory Method, UML class diagram."), Figure(sd, "Factory Method, UML sequence diagram.")])


def singleton():
    cd = ClassDiagram("singleton-class", "Singleton pattern, class diagram",
                      "Singleton keeps its only instance in a static attribute, hides its constructor and offers "
                      "the static getInstance operation that Client uses.", width=700, height=150)
    client = cd.klass(20, 60, "Client")
    sgl = cd.klass(220, 20, "Singleton", attrs=[Attr("-instance: Singleton", static=True)],
                   ops=["-Singleton()", Op("+getInstance(): Singleton", static=True)], w=220)
    cd.dependency([client.e(76), sgl.w_(76)], "use")
    cd.note(480, 74, ["if (instance == null)", f"{NB * 4}instance = new Singleton();", "return instance;"],
            links=[[sgl.e(101), (480, 101)]])

    sd = SequenceDiagram("singleton-seq", "Singleton pattern, sequence diagram",
                         "The first getInstance call creates the only instance; a later call by another client "
                         "returns the same instance.", width=760, height=380, name="getInstance")
    sd.lifeline("c1", 100, "c1 : Client")
    sd.lifeline("c2", 300, "c2 : Client")
    sd.lifeline("s", 500, "Singleton", keyword="Metaclass")
    sd.lifeline("i", 680, ": Singleton", created_at=208)
    sd.fragment("opt", 448, 740, 148, 240, [{"top": 148, "guard": "[instance == null]", "on": "s"}])
    sd.execution("c1", 120, 264)
    sd.execution("s", 128, 256)
    sd.execution("c2", 288, 336)
    sd.execution("s", 296, 328)
    sd.message("sync", "c1", "s", 128, "getInstance()", label_x=200)
    sd.message("create", "s", "i", 208, "Singleton()")
    sd.message("reply", "s", "c1", 256, "getInstance(): instance", label_x=200)
    sd.message("sync", "c2", "s", 296, "getInstance()")
    sd.message("reply", "s", "c2", 328, "getInstance(): instance")

    page("singleton", "Singleton",
         "Ensure a class only has one instance, and provide a global point of access to it. (GoF)",
         [Figure(cd, "Singleton, UML class diagram."), Figure(sd, "Singleton, UML sequence diagram.")])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    decorator()
    proxy()
    factory_method()
    singleton()
    print(f"wrote 4 pages to {OUT}")
