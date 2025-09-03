from __future__ import annotations

from typing import Tuple
import numpy as np


def compute_zigzag_buffers(
    highs: np.ndarray,
    lows: np.ndarray,
    depth: int,
    deviation_points: int,
    backstep: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Port of CountZZ (MQL4) -> returns (low_buffer, high_buffer).

    - highs, lows: numpy arrays aligned newest at index 0? We mirror MQL4 where index 0 is current bar.
      This implementation expects the same: index 0 is the latest bar, increasing to the left.
    - depth, deviation_points, backstep: same semantics as MQL4 CountZZ(ExtDepth, ExtDeviation, ExtBackstep).
    """
    assert highs.shape == lows.shape
    n = highs.shape[0]
    low_buf = np.zeros(n, dtype=float)
    high_buf = np.zeros(n, dtype=float)

    limit = max(0, min(n - depth, n - 1))

    last_low_val = -1.0
    last_high_val = -1.0

    # main scan from limit down to 0 (right-to-left like MQL4)
    for shift in range(limit, -1, -1):
        # lows
        span = lows[shift : shift + depth]
        val = span.min()
        if val == last_low_val:
            val = 0.0
        else:
            last_low_val = val
            if (lows[shift] - val) > deviation_points:
                val = 0.0
            else:
                for back in range(1, backstep + 1):
                    if shift + back < n:
                        res = low_buf[shift + back]
                        if res != 0.0 and res > val:
                            low_buf[shift + back] = 0.0
        low_buf[shift] = val

        # highs
        span_h = highs[shift : shift + depth]
        v = span_h.max()
        if v == last_high_val:
            v = 0.0
        else:
            last_high_val = v
            if (v - highs[shift]) > deviation_points:
                v = 0.0
            else:
                for back in range(1, backstep + 1):
                    if shift + back < n:
                        res = high_buf[shift + back]
                        if res != 0.0 and res < v:
                            high_buf[shift + back] = 0.0
        high_buf[shift] = v

    # final cutting (resolve conflicts)
    last_high = -1.0
    last_high_pos = -1
    last_low = -1.0
    last_low_pos = -1
    for shift in range(limit, -1, -1):
        curlow = low_buf[shift]
        curhigh = high_buf[shift]
        if curlow == 0.0 and curhigh == 0.0:
            continue
        if curhigh != 0.0:
            if last_high > 0:
                if last_high < curhigh:
                    high_buf[last_high_pos] = 0.0
                else:
                    high_buf[shift] = 0.0
            if last_high < curhigh or last_high < 0:
                last_high = curhigh
                last_high_pos = shift
            last_low = -1.0
        if curlow != 0.0:
            if last_low > 0:
                if last_low > curlow:
                    low_buf[last_low_pos] = 0.0
                else:
                    low_buf[shift] = 0.0
            if curlow < last_low or last_low < 0:
                last_low = curlow
                last_low_pos = shift
            last_high = -1.0

    # tail alignment (match MQL4 behavior)
    for shift in range(limit, -1, -1):
        if shift >= limit:
            low_buf[shift] = 0.0
        else:
            if high_buf[shift] != 0.0:
                high_buf[shift] = high_buf[shift]

    return low_buf, high_buf


