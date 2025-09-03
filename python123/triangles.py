from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict
import numpy as np


@dataclass
class Triangle:
    dir: str  # "buy" or "sell"
    bar1: int
    price1: float
    bar2: int
    price2: float
    bar3: int
    price3: float


def detect_123_triangles(
    semafor_levels: Dict[int, Tuple[np.ndarray, np.ndarray]],
    big_level: int,
    small_level: int,
    max_distance_points: int,
    max_bars_scan: int,
) -> List[Triangle]:
    """
    Port of Triangels() core to Python, scanning right-to-left (index 0 is current bar).
    - semafor_levels: {level: (low_buf, high_buf)}
    - big_level: level used for the anchor (point 1)
    - small_level: level used for points 2 and 3
    - max_distance_points: limit for |p2-p1|
    - max_bars_scan: maximum bars to scan back
    """
    results: List[Triangle] = []

    low_big, high_big = semafor_levels[big_level]
    low_small, high_small = semafor_levels[small_level]

    n = low_big.shape[0]
    max_bars = min(max_bars_scan, n - 1)

    for zz in range(max_bars, 0, -1):
        time_idx1 = zz
        p1_low = low_big[zz]
        p1_high = high_big[zz]

        # BUY pattern: point1 is a big-level low
        if p1_low > 0:
            price1 = p1_low
            found2 = False
            price2 = 0.0
            bar2 = -1
            price3 = 0.0
            bar3 = -1
            for lv in range(zz - 1, 0, -1):
                # stop if another big-level appears
                if high_big[lv] > 0 or low_big[lv] > 0:
                    break
                if not found2:
                    up = high_small[lv]
                    if up > 0:
                        if up >= price1:
                            price2 = up
                            bar2 = lv
                            found2 = True
                else:
                    if lv + 1 < n:
                        lo = low_small[lv + 1]
                        if lo > 0 and lo >= price1:
                            price3 = lo
                            bar3 = lv + 1
                if price1 > 0 and price2 > 0 and price3 > 0:
                    if abs(price2 - price1) < max_distance_points:
                        results.append(
                            Triangle(
                                dir="buy",
                                bar1=time_idx1,
                                price1=price1,
                                bar2=bar2,
                                price2=price2,
                                bar3=bar3,
                                price3=price3,
                            )
                        )
                    break

        # SELL pattern: point1 is a big-level high
        if p1_high > 0:
            price1 = p1_high
            found2 = False
            price2 = 0.0
            bar2 = -1
            price3 = 0.0
            bar3 = -1
            for lv in range(zz - 1, 0, -1):
                if high_big[lv] > 0 or low_big[lv] > 0:
                    break
                if not found2:
                    lo = low_small[lv]
                    if lo > 0:
                        if lo <= price1:
                            price2 = lo
                            bar2 = lv
                            found2 = True
                else:
                    if lv + 1 < n:
                        up = high_small[lv + 1]
                        if up > 0 and up <= price1:
                            price3 = up
                            bar3 = lv + 1
                if price1 > 0 and price2 > 0 and price3 > 0:
                    if abs(price1 - price2) < max_distance_points:
                        results.append(
                            Triangle(
                                dir="sell",
                                bar1=time_idx1,
                                price1=price1,
                                bar2=bar2,
                                price2=price2,
                                bar3=bar3,
                                price3=price3,
                            )
                        )
                    break

    return results


