p = "tools/pixel/chef_art.py"
s = open(p, encoding="utf-8").read()
old = s[s.index("def _hat("):s.index("def _head(")]
new = '''def _hat(a, bob, x0, w):
    a.ellipse(x0 - 1, bob - 3, w, 12, WHITE)
    a.ellipse(x0 + 1, bob - 1, 9, 8, WHITE)
    a.ellipse(x0 + w - 10, bob - 1, 9, 8, WHITE)
    a.ellipse(x0 + 5, bob - 4, 11, 8, WHITE)
    a.rect(x0 + 2, bob + 7, w - 4, 6, IVORY)
    a.hline(x0 + 2, x0 + w - 3, bob + 7, WHITE)
    a.hline(x0 + 2, x0 + w - 3, bob + 12, COAT_D)
    for px in range(x0 + 5, x0 + w - 4, 4):
        a.vline(px, bob + 8, bob + 11, mix(IVORY, SAND, 0.75))


'''
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("hat patched")
