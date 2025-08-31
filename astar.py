import math
import heapq
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

NEIGHBORS_8 = [
    (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
    (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
    (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))
]

@dataclass(order=True)
class PQItem:
    f: float
    seq: int
    node: int

def rc_to_idx(r: int, c: int, W: int) -> int:
    return r * W + c

def idx_to_rc(idx: int, W: int) -> Tuple[int, int]:
    return divmod(idx, W)

def a_star(walk: np.ndarray, start_rc: Tuple[int, int], goal_rc: Tuple[int, int]):
    """Runs A* pathfinding and returns (path, expanded_nodes)."""
    H, W = walk.shape
    sr, sc = start_rc
    gr, gc = goal_rc

    if not (0 <= sr < H and 0 <= sc < W and 0 <= gr < H and 0 <= gc < W):
        return None, []
    if not walk[sr, sc] or not walk[gr, gc]:
        return None, []

    start = rc_to_idx(sr, sc, W)
    goal = rc_to_idx(gr, gc, W)
    g = np.full(H * W, np.inf, dtype=np.float32)
    came = np.full(H * W, -1, dtype=np.int32)
    closed = np.zeros(H * W, dtype=np.bool_)
    expanded_nodes = []

    def h_est(idx: int) -> float:
        r, c = idx_to_rc(idx, W)
        return math.hypot(r - gr, c - gc)

    g[start] = 0.0
    seq = 0
    open_heap: List[PQItem] = []
    heapq.heappush(open_heap, PQItem(h_est(start), seq, start))

    while open_heap:
        current = heapq.heappop(open_heap).node
        if closed[current]:
            continue
        closed[current] = True
        expanded_nodes.append(current)

        if current == goal:
            path_idx = []
            cur = current
            while cur != -1:
                path_idx.append(cur)
                cur = came[cur]
            path_idx.reverse()
            path_rc = [idx_to_rc(i, W) for i in path_idx]
            return path_rc, expanded_nodes

        cr, cc = idx_to_rc(current, W)
        for dr, dc, cost in NEIGHBORS_8:
            nr, nc = cr + dr, cc + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue
            if not walk[nr, nc]:
                continue
            nidx = rc_to_idx(nr, nc, W)
            if closed[nidx]:
                continue
            tentative_g = g[current] + cost
            if tentative_g < g[nidx]:
                g[nidx] = tentative_g
                came[nidx] = current
                seq += 1
                f = tentative_g + h_est(nidx)
                heapq.heappush(open_heap, PQItem(f, seq, nidx))

    return None, expanded_nodes
