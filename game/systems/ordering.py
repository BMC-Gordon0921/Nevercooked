"""Order tickets: spawn cadence, patience and queue overflow."""
from __future__ import annotations

import random

from core import config

DISHES = config.DISHES
DISH_LIST = config.DISH_LIST


class Order:
    def __init__(self, dish_id):
        dish = DISHES[dish_id]
        self.dish_id = dish_id
        self.name = dish["name"]
        self.hint = dish.get("hint", "")
        self.price = int(dish["price"])
        self.patience = float(dish["patience"])
        self.time_left = self.patience
        self.state = "active"
        self.age = 0.0

    @property
    def overdue(self):
        return max(0.0, -self.time_left)

    @property
    def patience_ratio(self):
        return max(0.0, min(1.0, self.time_left / self.patience))


class OrderBoard:
    """Deterministic cadence: calm, busy, batch, rush."""

    def __init__(self, seed=7, cap=5, duration=180.0):
        self.rng = random.Random(seed)
        self.cap = cap
        self.duration = duration
        self.active = []
        self.queue = []
        self.served = []
        self.failed = []
        self.next_spawn = 3.0
        self.spawned = 0

    def _interval(self, elapsed):
        # Cadence is tuned to a 64px kitchen: about one order every 15s early,
        # tightening to one every 8s in the final rush (12-14 per round).
        if elapsed < 90:
            return self.rng.uniform(14.0, 18.0)
        if elapsed < 135:
            return self.rng.uniform(12.0, 14.0)
        if elapsed < 165:
            return self.rng.uniform(9.0, 11.0)
        return self.rng.uniform(7.0, 8.5)

    def _pick_dish(self, elapsed):
        if self.spawned == 0:
            return "fried_rice"
        pool = []
        for dish in DISH_LIST:
            weight = int(dish.get("weight", 1)) * 3
            pool.append((dish["id"], max(1, weight)))
        total = sum(w for _, w in pool)
        roll = self.rng.randrange(total)
        for dish_id, weight in pool:
            roll -= weight
            if roll < 0:
                return dish_id
        return pool[0][0]

    def update(self, dt, elapsed):
        if elapsed < self.duration and elapsed >= self.next_spawn:
            order = Order(self._pick_dish(elapsed))
            self.spawned += 1
            if len(self.active) < self.cap:
                self.active.append(order)
            else:
                self.queue.append(order)
            self.next_spawn = elapsed + self._interval(elapsed)
        while self.queue and len(self.active) < self.cap:
            self.active.append(self.queue.pop(0))
        for order in self.active:
            order.age += dt
            order.time_left -= dt
        expired = [o for o in self.active if o.overdue > o.patience * 0.5]
        for order in expired:
            self.active.remove(order)
            order.state = "failed"
            self.failed.append(order)

    def match(self, item_id):
        for order in self.active:
            if order.dish_id == item_id:
                return order
        return None

    def deliver(self, order):
        if order in self.active:
            self.active.remove(order)
        order.state = "served"
        self.served.append(order)
        return order
