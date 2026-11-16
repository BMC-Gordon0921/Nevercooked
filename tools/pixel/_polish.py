h = "tools/pixel/chef_art.py"
t = open(h, encoding="utf-8").read()
old = '''def _arms(a, bob, dl, dr):
    for x0, dy in ((6, dl), (32, dr)):
        a.rect(x0, 33 + bob + dy, 6, 13, IVORY)
        a.vline(x0, 34 + bob + dy, 44 + bob + dy, COAT_D)
        a.hline(x0, x0 + 5, 45 + bob + dy, COAT_D)
        a.rect(x0, 46 + bob + dy, 6, 4, SKIN)
        a.hline(x0, x0 + 5, 49 + bob + dy, SKIN_D)'''
new = '''def _arms(a, bob, dl, dr):
    for x0, dy, inner in ((6, dl, 11), (32, dr, 32)):
        a.rect(x0, 33 + bob + dy, 6, 13, IVORY)
        a.vline(inner, 33 + bob + dy, 45 + bob + dy, mix(IVORY, SAND, 0.55))
        a.hline(x0, x0 + 5, 45 + bob + dy, COAT_D)
        a.rect(x0, 46 + bob + dy, 6, 4, SKIN)
        a.hline(x0, x0 + 5, 49 + bob + dy, SKIN_D)'''
assert old in t
t = t.replace(old, new)
open(h, "w", encoding="utf-8").write(t)

z = "tools/pixel/zoom_sheet.py"
s = open(z, encoding="utf-8").read()
s = s.replace("56 * scale + lab, 64 * scale + lab]", "64 * scale + lab, 70 * scale + lab]")
open(z, "w", encoding="utf-8").write(s)
print("ok")
