"""Short leases so two cooks can split one kitchen without stepping on each other.

The player claims the station under the crosshair every frame (a 0.7s lease that
is refreshed, so letting go frees it).  Each AI mission claims the order it is
cooking and the station it is walking to.  A lease is a soft lock: the normal
path releases it explicitly; the TTL only covers a mission that died mid-flight
(stuck, cooldown, scene change) so a stale claim can never wedge the kitchen.

Owners are opaque: the player is the string PLAYER (or another string), a Brain
mission is the Mission object itself.  Nothing here knows about AI internals.
"""
from __future__ import annotations

PLAYER = "player"


class TaskBoard:
    def __init__(self):
        self._stations = {}   # id(station) -> [station, owner, ttl]
        self._orders = {}     # id(order) -> [order, owner, ttl]
        self._player_station = None
        self._player_order = None

    # -- generic ---------------------------------------------------------
    @staticmethod
    def _live(entry):
        return entry is not None and entry[2] > 0.0

    @staticmethod
    def _claim(table, key, obj, owner, ttl):
        entry = table.get(key)
        if entry is not None and entry[2] > 0.0 and entry[1] is not owner:
            return False
        table[key] = [obj, owner, max(0.0, float(ttl))]
        return True

    @staticmethod
    def _owner(table, key):
        entry = table.get(key)
        if entry is None or entry[2] <= 0.0:
            return None
        return entry[1]

    # -- stations --------------------------------------------------------
    def claim_station(self, station, owner, ttl=30.0):
        """True when the owner now holds this station (False while someone else does)."""
        if station is None or owner is None:
            return False
        return self._claim(self._stations, id(station), station, owner, ttl)

    def release_station(self, station, owner=None):
        if station is None:
            return
        entry = self._stations.get(id(station))
        if entry is not None and (owner is None or entry[1] is owner):
            self._stations.pop(id(station), None)

    def station_owner(self, station):
        if station is None:
            return None
        return self._owner(self._stations, id(station))

    def station_free(self, station, owner=None):
        """True when nobody else holds this station."""
        held = self.station_owner(station)
        return held is None or held is owner

    # -- orders ----------------------------------------------------------
    def claim_order(self, order, owner, ttl=30.0):
        if order is None or owner is None:
            return False
        return self._claim(self._orders, id(order), order, owner, ttl)

    def release_order(self, order, owner=None):
        if order is None:
            return
        entry = self._orders.get(id(order))
        if entry is not None and (owner is None or entry[1] is owner):
            self._orders.pop(id(order), None)

    def order_owner(self, order):
        if order is None:
            return None
        return self._owner(self._orders, id(order))

    def order_owners(self):
        """Live owners of orders (missions or the PLAYER string)."""
        return [entry[1] for entry in self._orders.values() if entry[2] > 0.0]

    def order_free(self, order, owner=None):
        held = self.order_owner(order)
        return held is None or held is owner

    # -- the player ------------------------------------------------------
    def note_player(self, station=None, order=None, ttl=0.7):
        """Refresh the player's priority claim.  The player always wins a contest.

        A station is only claimed while the player keeps aiming at it: pass None
        when the crosshair is empty and the old claim is dropped, so the helper
        can take the oven the moment the player looks away.
        """
        if station is not None:
            if self._player_station is not None and self._player_station is not station:
                self._drop_player_station()
            self._stations[id(station)] = [station, PLAYER, max(0.0, float(ttl))]
            self._player_station = station
        else:
            self._drop_player_station()
        if order is not None:
            self._orders[id(order)] = [order, PLAYER, max(0.0, float(ttl))]
            self._player_order = order

    def _drop_player_station(self):
        if self._player_station is not None:
            entry = self._stations.get(id(self._player_station))
            if entry is not None and entry[1] == PLAYER:
                self._stations.pop(id(self._player_station), None)
            self._player_station = None

    def player_station(self):
        if self._player_station is None:
            return None
        if not self._live(self._stations.get(id(self._player_station))):
            self._player_station = None
            return None
        return self._player_station

    def player_order(self):
        if self._player_order is None:
            return None
        if not self._live(self._orders.get(id(self._player_order))):
            self._player_order = None
            return None
        return self._player_order

    # -- lifetime --------------------------------------------------------
    def release_owner(self, owner):
        """Drop every lease a mission holds (mission finished, stuck or dropped)."""
        if owner is None:
            return
        for key, entry in list(self._stations.items()):
            if entry[1] is owner:
                self._stations.pop(key, None)
        for key, entry in list(self._orders.items()):
            if entry[1] is owner:
                self._orders.pop(key, None)
        if owner is PLAYER:
            self._player_station = None
            self._player_order = None

    def touch(self, owner, ttl=30.0):
        """Heartbeat: keep every lease this owner holds alive."""
        for table in (self._stations, self._orders):
            for entry in table.values():
                if entry[1] is owner:
                    entry[2] = max(entry[2], float(ttl))

    def tick(self, dt):
        """Age every lease, the player's included: the crosshair claim is
        refreshed each frame while aimed, so it lapses on its own the moment the
        player looks away -- otherwise the helper is shut out of every station
        the player has ever pointed at."""
        for table in (self._stations, self._orders):
            for key, entry in list(table.items()):
                entry[2] -= dt
                if entry[2] <= 0.0:
                    table.pop(key, None)
        if self._player_station is not None and not self._live(self._stations.get(id(self._player_station))):
            self._player_station = None
        if self._player_order is not None and not self._live(self._orders.get(id(self._player_order))):
            self._player_order = None

    def clear(self):
        self._stations.clear()
        self._orders.clear()
        self._player_station = None
        self._player_order = None

    # -- inspection ------------------------------------------------------
    @staticmethod
    def _label(owner):
        if isinstance(owner, str):
            return owner
        return "mission"

    def snapshot(self):
        return {
            "stations": {key: self._label(entry[1]) for key, entry in self._stations.items() if entry[2] > 0.0},
            "orders": {key: self._label(entry[1]) for key, entry in self._orders.items() if entry[2] > 0.0},
            "player_station": None if self.player_station() is None else id(self._player_station),
            "player_order": None if self.player_order() is None else id(self._player_order),
        }

    def station_refs(self):
        return [entry[0] for entry in self._stations.values()]

    def order_refs(self):
        return [entry[0] for entry in self._orders.values()]
