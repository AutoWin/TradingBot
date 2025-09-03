from __future__ import annotations

from typing import List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .triangles import Triangle


def plot_ohlc_with_triangles(
    df: pd.DataFrame,
    triangles: List[Triangle],
    title: str = "1-2-3 Triangles",
    show: bool = False,
    out_path: str | None = None,
):
    """
    Plot close price with 1-2-3 triangles overlaid. Assumes df newest is at index 0.
    """
    # Convert to plotting order: oldest -> newest
    dfp = df.iloc[::-1].reset_index(drop=True)
    closes = dfp["close"].to_numpy()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(closes, color="#333", lw=1.2, label="Close")
    ax.set_title(title)
    ax.grid(True, ls=":", alpha=0.4)

    # triangles indices were computed on buffers with newest at 0 -> convert
    n = len(dfp)
    def buf_to_plot_idx(buf_idx: int) -> int:
        # buffer 0 (newest) -> plot index n-1
        return n - 1 - buf_idx

    for t in triangles:
        x1, x2, x3 = map(buf_to_plot_idx, [t.bar1, t.bar2, t.bar3])
        y1, y2, y3 = t.price1, t.price2, t.price3
        color = "tab:blue" if t.dir == "buy" else "tab:red"
        ax.plot([x1, x2, x3, x1], [y1, y2, y3, y1], color=color, lw=1.5, alpha=0.9)
        ax.scatter([x1, x2, x3], [y1, y2, y3], color=color, s=20)

    ax.legend(loc="best")
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


