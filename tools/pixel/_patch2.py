p = "tools/pixel/make_items.py"
s = open(p, encoding="utf-8").read()
s = s.replace('"stardust": new_item_stardust,', '"stardust": lambda a: new_item_stardust(),')
s = s.replace('"meat_cut": new_item_meat_cut,', '"meat_cut": lambda a: new_item_meat_cut(),')
s = s.replace('"veg": new_item_veg,', '"veg": lambda a: new_item_veg(),')
open(p, "w", encoding="utf-8").write(s)
print("ok")
