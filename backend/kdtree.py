"""
KD-Tree implementation — mirrors the C++ core/kd_tree.cpp logic.
Alternates split axis: depth%2 == 0 → latitude, 1 → longitude.
"""

import math
from models import Civilization


class _Node:
    __slots__ = ("civ", "left", "right")

    def __init__(self, civ: Civilization):
        self.civ = civ
        self.left = None
        self.right = None


class KDTree:
    def __init__(self):
        self.root = None
        self.node_count = 0

    # ── Build (balanced, median-split) ────────────────────────
    def build(self, civs: list[Civilization], depth: int = 0) -> "_Node | None":
        if not civs:
            return None
        axis = depth % 2
        civs = sorted(civs, key=lambda c: c.latitude if axis == 0 else c.longitude)
        mid = len(civs) // 2
        node = _Node(civs[mid])
        self.node_count += 1
        node.left = self.build(civs[:mid], depth + 1)
        node.right = self.build(civs[mid + 1:], depth + 1)
        if depth == 0:
            self.root = node
        return node

    # ── Nearest neighbor ──────────────────────────────────────
    def nearest(self, lat: float, lon: float) -> tuple[Civilization, float] | None:
        if self.root is None:
            return None
        best = [None, math.inf]  # [civ, dist]
        self._nn(self.root, lat, lon, best, 0)
        return best[0], best[1]

    def _nn(self, node, lat, lon, best, depth):
        if node is None:
            return
        d = math.sqrt((lat - node.civ.latitude) ** 2 + (lon - node.civ.longitude) ** 2)
        if d < best[1]:
            best[0] = node.civ
            best[1] = d

        axis = depth % 2
        node_val = node.civ.latitude if axis == 0 else node.civ.longitude
        query_val = lat if axis == 0 else lon

        first, second = (node.left, node.right) if query_val < node_val else (node.right, node.left)
        self._nn(first, lat, lon, best, depth + 1)

        # Prune: only visit other branch if the splitting plane is closer than best
        if abs(query_val - node_val) < best[1]:
            self._nn(second, lat, lon, best, depth + 1)

    # ── Range query ───────────────────────────────────────────
    def range_query(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float
    ) -> list[Civilization]:
        results: list[Civilization] = []
        self._range(self.root, lat_min, lat_max, lon_min, lon_max, results, 0)
        return results

    def _range(self, node, lat_min, lat_max, lon_min, lon_max, results, depth):
        if node is None:
            return
        c = node.civ
        if lat_min <= c.latitude <= lat_max and lon_min <= c.longitude <= lon_max:
            results.append(c)

        axis = depth % 2
        node_val = c.latitude if axis == 0 else c.longitude
        min_v = lat_min if axis == 0 else lon_min
        max_v = lat_max if axis == 0 else lon_max

        if min_v <= node_val:
            self._range(node.left, lat_min, lat_max, lon_min, lon_max, results, depth + 1)
        if max_v >= node_val:
            self._range(node.right, lat_min, lat_max, lon_min, lon_max, results, depth + 1)

    # ── Epsilon-neighborhood (used by DBSCAN) ─────────────────
    def neighbors_within(self, lat: float, lon: float, eps: float) -> list[Civilization]:
        """Return all points within eps degrees of (lat, lon)."""
        return self.range_query(lat - eps, lat + eps, lon - eps, lon + eps)
