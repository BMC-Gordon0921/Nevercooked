import re
p = "tools/pixel/chef_art.py"
s = open(p, encoding="utf-8").read()
def rep(m):
    x, y, w, h, r, c = (g.strip() for g in m.groups())
    return "a.rrect(%s, %s, %s, %s, %s, %s)" % (x, y, w, h, c, r)
s = re.sub(r"a\.rrect\(([^()]+?), ([^()]+?), ([^()]+?), ([^()]+?), ([^()]+?), ([^()]+?)\)", rep, s)
open(p, "w", encoding="utf-8").write(s)
print([l for l in s.splitlines() if "rrect" in l])
