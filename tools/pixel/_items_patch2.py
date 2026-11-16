import re
p = "tools/pixel/_items_patch.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''    if not pat.search(src):
        raise SystemExit("not found: " + name)
    return pat.sub(body, src, count=1)''', '''    if not pat.search(src):
        return src.replace("\\nITEMS = {", "\\n" + body + "\\nITEMS = {", 1)
    return pat.sub(body, src, count=1)''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
