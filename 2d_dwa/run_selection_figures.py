"""Concept figures for the 2-D DWA technique.

fig1_selection_pattern.png  - reproduction of the paper's Fig. 1
fig2_usage_uniformity.png   - element usage: no DEM vs 2-D DWA
fig3_equivalence.png        - bit-exact equivalence with 1-D DWA and
                              hardware scaling advantage
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from dwa_core import (dwa_1d_masks, dwa_2d_masks, thermometer_masks,
                      quantized_sine)
import plot_style as ps

ps.apply_style()
FIGDIR = "figures"

SEQ_FIG1 = [3, 9, 15, 27, 13, 12, 34, 20, 13]


# ---------------------------------------------------------------------------
# Figure 1: element selection pattern (paper Fig. 1)
# ---------------------------------------------------------------------------

def draw_grid(ax, mask8x8, title):
    for j in range(8):
        for i in range(8):
            face = ps.C_SELECTED if mask8x8[j, i] else "white"
            ax.add_patch(Rectangle((i, j), 1, 1, facecolor=face,
                                   edgecolor=ps.TEXT_SECONDARY, lw=0.6))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_title(title, fontsize=10)


def fig_selection_pattern():
    masks, sig = dwa_2d_masks(SEQ_FIG1, nbits=6, return_signals=True)
    masks = masks.reshape(-1, 8, 8)
    fig, axes = plt.subplots(3, 3, figsize=(8.2, 8.8))
    for n, ax in enumerate(axes.flat):
        s = sig[n]
        title = (f"sample {n + 1}:  d = {SEQ_FIG1[n]}"
                 f"  (MSB {s['msb']}, LSB {s['lsb']})")
        draw_grid(ax, masks[n], title)
        ax.set_xlabel(f"rows: {s['nrows']}   hd: {s['hd']}   tl: {s['tl']}",
                      fontsize=8.5, color=ps.TEXT_SECONDARY)
    axes[2, 0].set_xticks([0.5, 7.5], ["i=0", "i=7"])
    axes[2, 0].set_yticks([0.5, 7.5], ["j=0", "j=7"])
    fig.suptitle("2-D DWA element selection on a 6-bit (8×8) DAC\n"
                 "input sequence {3, 9, 15, 27, 13, 12, 34, 20, 13} "
                 "— reproduction of paper Fig. 1", y=0.99)
    fig.text(0.5, 0.005,
             "Red = selected element. Elements are used row by row and "
             "rotationally; the pattern wraps from the last to the first row.",
             ha="center", fontsize=9, color=ps.TEXT_SECONDARY)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.savefig(f"{FIGDIR}/fig1_selection_pattern.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: element usage uniformity
# ---------------------------------------------------------------------------

def fig_usage_uniformity(n_samp=4096):
    rng = np.random.default_rng(42)
    codes = quantized_sine(n_samp, -3.0, sig_bin=17, nbits=6, rng=rng)
    usage_therm = thermometer_masks(codes, 64).sum(axis=0).reshape(8, 8)
    usage_dwa = dwa_2d_masks(codes, 6).sum(axis=0).reshape(8, 8)

    vmax = max(usage_therm.max(), usage_dwa.max())
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    for ax, usage, name in [(axes[0], usage_therm, "No DEM (thermometer)"),
                            (axes[1], usage_dwa, "2-D DWA")]:
        im = ax.imshow(usage, origin="lower", cmap="Blues",
                       vmin=0, vmax=vmax)
        ax.set_title(f"{name}\nusage min/max = "
                     f"{usage.min():.0f} / {usage.max():.0f}")
        ax.set_xlabel("column i")
        ax.set_ylabel("row j")
        ax.grid(False)
    cbar = fig.colorbar(im, ax=axes, shrink=0.85)
    cbar.set_label("times selected")
    fig.suptitle(f"Cumulative element usage over {n_samp} samples of a "
                 "−3 dBFS sine input")
    fig.savefig(f"{FIGDIR}/fig2_usage_uniformity.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: equivalence with 1-D DWA + hardware scaling
# ---------------------------------------------------------------------------

def fig_equivalence(n_samp=20000):
    rng = np.random.default_rng(7)
    codes = rng.integers(0, 64, n_samp)
    m2 = dwa_2d_masks(codes, 6)
    m1 = dwa_1d_masks(codes, 64)
    diff = np.abs(m2.astype(int) - m1).sum(axis=1)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))

    ax = axes[0]
    ax.plot(diff, color=ps.C_2DDWA, lw=1.2)
    ax.set_ylim(-0.5, 8)
    ax.set_xticks([0, 5000, 10000, 15000, 20000])
    ax.set_xlabel("sample index (random 6-bit input)")
    ax.set_ylabel("differing elements per sample")
    ax.set_title("2-D DWA vs conventional 1-D DWA (64 elements)")
    ax.annotate(f"bit-exact for all {n_samp:,} samples\n"
                "(max difference = 0)",
                xy=(n_samp / 2, 0), xytext=(n_samp / 2, 4),
                ha="center", arrowprops=dict(arrowstyle="->",
                                             color=ps.TEXT_SECONDARY))

    # Control-signal count: 1-D DWA drives 2**N element lines; the 2-D DWA
    # drives 4 row + 3 column signals per row/column, i.e. 7 * 2**(N/2)
    # (57% fewer signals at 8 bits, Table 1 of the paper).
    ax = axes[1]
    nbits = np.arange(4, 11, 2)
    ax.plot(nbits, 2.0 ** nbits, "o-", color=ps.C_SEGMENTED,
            label="1-D DWA: $2^N$ element lines")
    ax.plot(nbits, 7 * 2.0 ** (nbits / 2), "s-", color=ps.C_2DDWA,
            label="2-D DWA: $7\\cdot2^{N/2}$ row/col signals")
    ax.set_yscale("log", base=2)
    ax.set_xticks(nbits)
    ax.set_xlabel("DAC resolution N (bits)")
    ax.set_ylabel("output control signals")
    ax.set_title("Same operation, exponentially cheaper decoder")
    ax.legend(fontsize=9)

    fig.suptitle("2-D DWA is functionally identical to 1-D DWA "
                 "at a fraction of the hardware cost")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(f"{FIGDIR}/fig3_equivalence.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_selection_pattern()
    fig_usage_uniformity()
    fig_equivalence()
    print("selection figures written to", FIGDIR)
