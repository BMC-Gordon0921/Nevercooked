import re
import sys
sys.path.insert(0, ".")
from tools.pixel import _blocks as B
import inspect

TARGETS = {
    "chef_frame": "chef_frame",
    "station_board": "new_station_board",
    "station_steamer": "new_station_steamer",
    "station_serve": "new_station_serve",
    "item_stardust": "new_item_stardust",
    "item_meat_cut": "new_item_meat_cut",
    "item_veg": "new_item_veg",
}
p = "tools/pixel/make_art.py"
src = open(p, encoding="utf-8").read()


def spans(text, name):
    m = re.search(r"^def %s\(" % name, text, re.M)
    if not m:
        raise SystemExit("not found: " + name)
    start = m.start()
    nxt = re.search(r"^(def |# -{3,})", text[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(text)
    return start, end


for old, new in TARGETS.items():
    code = inspect.getsource(getattr(B, new))
    code = code.replace("def " + new + "(", "def " + old + "(", 1).rstrip() + "\n\n"
    s, e = spans(src, old)
    src = src[:s] + code + src[e:]
    print("replaced", old, "with", len(code), "chars")
open(p, "w", encoding="utf-8").write(src)
