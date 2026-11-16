p = "tests/_audit.py"
s = open(p, encoding="utf-8").read()
s = s.replace('    path = os.path.join(config.ART_DIR, key + ".png")',
              '    exp = exp or (None, None)\n    path = os.path.join(config.ART_DIR, key + ".png")')
open(p, "w", encoding="utf-8").write(s)
print("ok")
