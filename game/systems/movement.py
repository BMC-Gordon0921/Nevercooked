"""Foot-box movement with axis-separated collision and wall sliding."""
from __future__ import annotations

import math

from core import config

_DIAGONAL = math.sqrt(0.5)


def _blocked(rect, solids):
    for solid in solids:
        if rect.colliderect(solid.foot):
            return solid
    return None


def move(actor, dx, dy, solids):
    """Move on x, then y, stopping against solids. Returns the distance moved."""
    moved = 0.0
    if dx:
        actor.foot.x += int(round(dx))
        hit = _blocked(actor.foot, solids)
        if hit is not None:
            if dx > 0:
                actor.foot.right = hit.foot.left
            else:
                actor.foot.left = hit.foot.right
        moved += abs(dx)
    if dy:
        actor.foot.y += int(round(dy))
        hit = _blocked(actor.foot, solids)
        if hit is not None:
            if dy > 0:
                actor.foot.bottom = hit.foot.top
            else:
                actor.foot.top = hit.foot.bottom
        moved += abs(dy)
    return moved


def update_actor(actor, intent, dt, world, params=None):
    """Consume an intent, move the actor, update sprint and facing."""
    tuning = params or config.TUNING["player"]
    mx, my = intent.mx, intent.my
    if mx and my:
        mx *= _DIAGONAL
        my *= _DIAGONAL

    actor.moving = bool(mx or my)
    if actor.moving and actor.busy > 0:
        cancel_busy(actor)

    speed = tuning["speed"]
    if actor.sprint_t > 0:
        speed = tuning["sprint_speed"]
        actor.sprint_t = max(0.0, actor.sprint_t - dt)
    elif intent.sprint and actor.moving and actor.sprint_cd <= 0:
        actor.sprint_t = tuning["sprint_duration"]
        actor.sprint_cd = tuning["sprint_cooldown"]

    if not actor.moving:
        return 0.0

    actor.face(intent.mx, intent.my)
    solids = world.solids()
    step_x = mx * speed * dt
    step_y = my * speed * dt * 1.0
    if actor.busy > 0:
        step_x *= 0.0
        step_y *= 0.0
    moved = move(actor, step_x, step_y, solids)
    actor.walked += moved
    return moved


def cancel_busy(actor):
    if actor.busy > 0:
        actor.busy = 0.0
        actor.pending_action = None
