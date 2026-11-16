p = "tools/pixel/zoom_sheet.py"
s = open(p, encoding="utf-8").read()
s = s.replace('rows = [max(120, 44) * scale + lab, 128 * scale + lab, 28 * scale + lab, 64 * scale + lab]',
              'rows = [172 * scale + lab, 132 * scale + lab, 56 * scale + lab, 64 * scale + lab]')
s = s.replace('x += 56 * scale + pad', 'x += 58 * scale + pad')
open(p, "w", encoding="utf-8").write(s)
print("ok")
