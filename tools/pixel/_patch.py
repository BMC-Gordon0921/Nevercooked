p = "tools/pixel/make_art.py"
s = open(p, encoding="utf-8").read()
reps = [
 ("a.line(sx, sy, sx + 1, sy + 6, mix(CREAM, SAND, 0.45))", "a.line((sx, sy), (sx + 1, sy + 6), mix(CREAM, SAND, 0.45))"),
 ("a.line(14, 10, 14, 17, mix(CREAM, SAND, 0.55))", "a.line((14, 10), (14, 17), mix(CREAM, SAND, 0.55))"),
 ("a.line(14, 8, 14, 22, dk(LEAF, 0.25))", "a.line((14, 8), (14, 22), dk(LEAF, 0.25))"),
 ("a.line(8, 13, 20, 11, mix(LEAF, LIME, 0.6))", "a.line((8, 13), (20, 11), mix(LEAF, LIME, 0.6))"),
 ("a.line(9, 18, 19, 17, mix(LEAF, LIME, 0.6))", "a.line((9, 18), (19, 17), mix(LEAF, LIME, 0.6))"),
]
for a, b in reps:
    if a not in s:
        print("MISS:", a)
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("done")
