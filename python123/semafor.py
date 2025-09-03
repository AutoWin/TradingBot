from __future__ import annotations

from typing import Dict, Tuple, List
import numpy as np

from .zigzag import compute_zigzag_buffers


def compute_semafor_levels(
    highs: np.ndarray,
    lows: np.ndarray,
    periods: List[int],
    deviation_points: int,
    backstep: int,
) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
    """
    Compute 8 (or N) semafor levels using ZigZag-like buffers.

    Returns a dict: level_index -> (low_buffer, high_buffer), where level_index starts at 1.
    """
    results: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}
    for i, depth in enumerate(periods, start=1):
        low_buf, high_buf = compute_zigzag_buffers(
            highs=highs,
            lows=lows,
            depth=depth,
            deviation_points=deviation_points,
            backstep=backstep,
        )
        results[i] = (low_buf, high_buf)
    return results


