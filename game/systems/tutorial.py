"""First shift coaching: four lines, tied to what the cook actually does.

Deliberately event driven, not timer driven: the prompt moves on when the action
lands, so a slow reader is never rushed and a fast one is never held back.
"""
from __future__ import annotations

STEPS = (
    "走到料箱前按 F 拿食材：星米先上蒸笼",
    "站到蒸笼前按 F 放进去，等它蒸熟（好了会响一声）",
    "回到蒸笼按 F 取出蒸饭，再拿去灶台按 F 开火",
    "灶台按 F 加蛋和星尘；起锅后拿去出餐口按 F 出餐",
)


class Tutorial:
    def __init__(self):
        self.step = 0
        self.done = False
        self.visible = True

    # -- state ----------------------------------------------------------
    def text(self):
        if self.done or not self.visible:
            return ""
        return STEPS[min(self.step, len(STEPS) - 1)]

    def on_event(self, event):
        if self.done:
            return
        if event in ("take", "pickup") and self.step == 0:
            self.step = 1
        elif event in ("load",) and self.step == 1:
            self.step = 2
        elif event in ("take_slot", "take", "swap") and self.step == 2:
            self.step = 3
        elif event == "served":
            self.done = True
        elif event in ("chop_done", "add") and self.step < 3:
            self.step = 3

    def skip(self):
        """Space: hide it. The guide line stays, so nothing is lost forever."""
        self.done = True

    def toggle(self):
        self.visible = not self.visible
        return self.visible
