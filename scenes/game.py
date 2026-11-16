"""The run itself: 180 seconds of tickets, woks and elbows."""
from __future__ import annotations

import random

import pygame

from core import assets, audio, config, text as textmod
from game import world as world_mod
from game.systems import cooking, hud, interaction, ordering, render, scoring
from game.systems import difficulty as diff
from game.systems import guide
from game.systems.tutorial import Tutorial
from game.systems import movement
from game.systems.camera import Camera

HINTS_IDLE = [("F", "交互"), ("Q", "抛出"), ("右键", "冲刺")]
CHOP_CUES = ("sfx_chop_1", "sfx_chop_2", "sfx_chop_3")
CHOP_STREAM = random.Random(4)
HINTS_LOADED = [("F", "交互"), ("Q", "抛出")]


class GameScene:
    def __init__(self, app, level=None):
        self.app = app
        self.level = level or getattr(app, "difficulty", diff.DEFAULT)
        diff.set_level(self.level)
        self.world = world_mod.World()
        cfg = config.TUNING["round"]
        self.duration = float(cfg["duration"])
        self.world.orders = ordering.OrderBoard(
            seed=7, cap=int(cfg["order_cap"]), duration=self.duration,
            patience_scale=diff.patience_scale(), interval_scale=diff.spawn_scale())
        self.world.score = scoring.ScoreBoard()
        self.player = self.world.player
        frames = assets.sheet("chef", config.TUNING["player"]["sprite_w"],
                             config.TUNING["player"]["sprite_h"])
        if len(frames) < 12:
            frames = assets.chef_placeholder((config.TUNING["player"]["sprite_w"],
                                              config.TUNING["player"]["sprite_h"]))
        self.player.frames = frames
        self.elapsed = 0.0
        self.fail_seen = 0
        self.target = None
        self.label = ""
        self.detail = ""
        self.label_ok = False
        self.suggest = []
        self.guide = None
        self.show_help = True
        self.tutorial = Tutorial() if diff.assist("tutorial") else None
        self.toast = ""
        self.toast_t = 0.0
        self.paused = False
        self.player.target_age = 0.0
        self.orders_seen = 0
        self.tick_second = -1
        self.phase_cache = {id(s): s.phase for s in self.world.stations}
        self.camera = Camera(zoom=2)
        self.camera.set_bounds(self.world.bounds)
        self.camera.center_on((self.player.foot.centerx, self.player.foot.bottom))
        # BGM sits ~10 dB under the effects: it is a backdrop, not the main event.
        audio.play_bgm("bgm_canteen_loop", 0.20)

    # -- loop -----------------------------------------------------------
    def update(self, dt, intent):
        if self.paused:
            if intent.menu:
                self.paused = False
            elif intent.confirm:
                self.app.switch(__import__("scenes.title", fromlist=["TitleScene"]).TitleScene(self.app))
            return
        if intent.menu:
            self.paused = True
            return

        self.elapsed += dt
        player = self.player

        movement.update_actor(player, intent, dt, self.world)
        self.target = interaction.find_target(self.world, player)
        label, ok = interaction.describe(player, self.target, self.world)
        self.label, self.label_ok = label, ok
        self.detail = interaction.explain(player, self.target, self.world)[1]
        if not diff.assist("reason"):
            self.detail = ""
        self.suggest = (interaction.suggestions(self.world, player)
                        if diff.assist("dots") else [])

        if intent.skip and self.tutorial is not None:
            self.tutorial.skip()
        if intent.help:
            self.show_help = not self.show_help

        clicked = self._station_at_screen(intent.click_pos) if intent.click_pos else None
        if clicked is not None:
            self.target = clicked
            self.label = ""
            event, detail = interaction.interact_with_detail(self.world, player, clicked)
            self._seen(event, detail)
            self._machine_sound(event)
        elif intent.interact:
            event, detail = interaction.interact_with_detail(self.world, player, self.target)
            self._seen(event, detail)
            self._machine_sound(event)
        if intent.throw:
            event = interaction.throw(self.world, player)
            self._seen(event, "")

        self.world.update(dt)
        cooking.tick_all(self.world, dt)
        self._ready_chimes()
        self.camera.center_on((player.foot.centerx, player.foot.bottom - 24))
        self.world.orders.update(dt, self.elapsed)
        self.guide = (guide.next_step(self.world, player)
                      if diff.assist("guide") and self.show_help else None)
        if self.world.orders.spawned > self.orders_seen:
            self.orders_seen = self.world.orders.spawned
            audio.play("sfx_order", 0.60)
        left = self.duration - self.elapsed
        if 0 < left <= 30.0 and int(left) != self.tick_second:
            self.tick_second = int(left)
            audio.play("sfx_tick", 0.50)
        if len(self.world.orders.failed) > self.fail_seen:
            for _ in range(len(self.world.orders.failed) - self.fail_seen):
                self.world.score.on_fail()
            self.fail_seen = len(self.world.orders.failed)
            self._toast("客人走了…", config.color("tomato"))
        if self.elapsed >= self.duration:
            self._finish()
        if self.toast_t > 0:
            self.toast_t -= dt

    def _station_at_screen(self, pos):
        """Click a machine to use it; the cursor does the walking.

        Easy-mode only (see difficulty.py): the moment it is always available it
        replaces the movement the whole game is about.
        """
        if not diff.assist("mouse"):
            return None
        cam = self.camera
        if pos[1] < config.BAR_TOP_H:
            return None
        wx = cam.x + (pos[0] - cam.ox) / float(cam.zoom)
        wy = cam.y + (pos[1] - cam.oy) / float(cam.zoom)
        best = None
        best_dist = 1 << 30
        for station in self.world.stations:
            if not station.reach.inflate(10, 10).collidepoint(wx, wy):
                continue
            dist = abs(station.foot.centerx - self.player.foot.centerx)
            if dist < best_dist:
                best, best_dist = station, dist
        return best

    def _coach(self):
        if not diff.assist("coach"):
            return ""
        if self.player.hand is not None:
            return "手上：%s — 走到设备前按 F 放进去，Q 可以抛出去" % self.player.hand.name
        for station in self.world.stations:
            if station.phase in ("cook", "add", "prep"):
                return "设备上还有活 — 记得回去按 F 取出来"
        return "空手 — 走到料箱前按 F 拿食材"

    def _seen(self, event, detail=""):
        """One funnel: sound, toast and tutorial progress all read the same event."""
        self._feedback(event, detail)
        if self.tutorial is not None:
            self.tutorial.on_event(event)

    def _feedback(self, event, detail=""):
        if event in ("take", "pickup"):
            audio.play("sfx_pickup", 0.85)
            self._toast(detail or "拿到了", config.color("cyan"))
        elif event in ("load", "add"):
            audio.play("sfx_place", 0.85)
            self._toast(detail or "放好了", config.color("cyan"))
        elif event == "swap":
            audio.play("sfx_pickup", 0.85)
            self._toast("换手了", config.color("cyan"))
        elif event == "drop":
            audio.play("sfx_place", 0.7)
            self._toast("放在脚边了", config.color("fog"))
        elif event == "throw":
            audio.play("sfx_place", 0.6)
            self._toast("扔出去了", config.color("fog"))
        elif event == "chop":
            audio.play(CHOP_STREAM.choice(CHOP_CUES), 0.75)
            self._toast("切切切", config.color("silver"))
        elif event == "chop_done":
            audio.play(CHOP_STREAM.choice(CHOP_CUES), 0.85)
            self._toast("切好了", config.color("lime"))
        elif event == "served":
            audio.play("sfx_bell", 0.90)
            self.toast = ""
        elif event == "no_order":
            audio.play("sfx_fail", 0.45)
            self._toast("没这张单", config.color("pink"))
        elif event == "reject":
            audio.play("sfx_fail", 0.5)
            self._toast(detail or "不对", config.color("tomato"))
        elif event == "trash":
            audio.play("sfx_trash", 0.75)
            self._toast("扔了", config.color("fog"))

    def _machine_sound(self, event):
        """Each station gets its own one-shot when work starts: a short cue, never
        a looping hiss (that is what made the kitchen sound like static)."""
        target = self.target
        if event not in ("load", "add") or target is None:
            return
        if getattr(target, "phase", None) != "cook":
            return
        if target.stype == "steamer":
            audio.play("sfx_steam", 0.65)
        elif target.stype == "wok":
            audio.play("sfx_sizzle", 0.65)
        elif target.stype == "oven":
            audio.play("sfx_oven", 0.65)

    def _ready_chimes(self):
        """A cooking timer that finishes silently is a timer you forget about."""
        for station in self.world.stations:
            key = id(station)
            before = self.phase_cache.get(key, station.phase)
            if station.phase == "ready" and before == "cook":
                audio.play("sfx_ready", 0.70)
            self.phase_cache[key] = station.phase

    def _toast(self, message, color=None):
        self.toast = message
        self.toast_t = 1.2
        self.toast_color = color or config.color("silver")

    def _finish(self):
        from scenes.results import ResultsScene
        self.app.switch(ResultsScene(self.app, self.world.score, self.level))

    # -- draw -----------------------------------------------------------
    def draw(self, surface):
        cam = self.camera
        show_aim = diff.assist("aim")
        render.render(surface, self.world, cam,
                      aim_ok=self.label_ok, aim=show_aim,
                      suggestions=self.suggest)
        render.draw_hand(surface, cam, self.world)
        render.draw_popups(surface, cam, self.world)

        hud.draw_top_bar(surface, self.world, self.elapsed, self.duration)
        hud.draw_tickets(surface, self.world)
        hud.draw_target_label(surface, cam, self.world, self.label, self.detail,
                              self.label_ok)
        if self.guide is not None and self.show_help:
            render.draw_pulse(surface, cam, self.guide.get("station"))
        if self.tutorial is not None and self.show_help:
            hud.draw_tutorial(surface, self.tutorial.text())
        if self.guide is not None and self.show_help:
            hud.draw_guide(surface, self.guide.get("label"))

        hints = HINTS_IDLE
        if self.label:
            hints = [("F", self.label), ("Q", "抛出"), ("右键", "冲刺")]
        hud.draw_hints(surface, hints)

        textmod.shadow_text(surface, "%s · 结算 x%.2f" % (diff.data()["name"],
                                                          diff.score_scale()),
                            (16, config.SCREEN_H - 20), size=12,
                            color=config.color("fog"), anchor="midleft")
        # Coach line lives in the bottom bar so it never sits on the kitchen floor.
        coach = self._coach()
        if coach:
            textmod.shadow_text(surface, coach, (config.SCREEN_W - 20,
                                                 config.SCREEN_H - 20),
                                size=13, color=config.color("fog"), anchor="midright")
        if self.toast_t > 0 and self.toast:
            textmod.shadow_text(surface, self.toast, (config.SCREEN_W // 2,
                                                      config.SCREEN_H - 78),
                                size=16, color=getattr(self, "toast_color", config.color("silver")),
                                bold=True, anchor="center")
        if self.paused:
            veil = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            veil.fill((11, 14, 20, 190))
            surface.blit(veil, (0, 0))
            cx = config.SCREEN_W // 2
            card = pygame.Rect(cx - 300, 120, 600, 430)
            pygame.draw.rect(surface, config.color("ink"), card, border_radius=10)
            pygame.draw.rect(surface, config.color("slate"), card, 2, border_radius=10)
            textmod.shadow_text(surface, "暂停", (cx, card.y + 42), size=38,
                                color=config.color("silver"), bold=True, anchor="center")
            textmod.shadow_text(surface, "三张单的做法", (cx, card.y + 88), size=16,
                                color=config.color("cyan"), anchor="center")
            for index, dish in enumerate(config.DISH_LIST):
                row = card.y + 128 + index * 62
                icon = assets.image("item_" + dish["id"], (30, 30))
                surface.blit(icon, icon.get_rect(midleft=(card.x + 42, row + 6)))
                textmod.shadow_text(surface, dish["name"], (card.x + 78, row),
                                    size=18, color=config.color("silver"), bold=True,
                                    anchor="midleft")
                textmod.shadow_text(surface, dish.get("hint", ""), (card.x + 78, row + 22),
                                    size=13, color=config.color("fog"), anchor="midleft")
                textmod.shadow_text(surface, "%d 币" % dish["price"], (card.right - 42, row),
                                    size=16, color=config.color("amber"), anchor="midright")
            textmod.shadow_text(surface, "%s · 结算 x%.2f" % (diff.data()["name"],
                                                              diff.score_scale()),
                                (cx, card.bottom - 78), size=13,
                                color=config.color("steel"), anchor="center")
            textmod.shadow_text(surface, "WASD 移动 · 右键/Shift 冲刺 · F 交互 · Q 抛出",
                                (cx, card.bottom - 54), size=14,
                                color=config.color("fog"), anchor="center")
            textmod.shadow_text(surface, "Esc 继续    Enter 回标题", (cx, card.bottom - 28),
                                size=14, color=config.color("fog"), anchor="center")
