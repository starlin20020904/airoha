"""Explainer figures: WHY the 2-D DWA is split into row/column decoders.

fig5_architecture_flow.png - signal-flow diagram of the 2-D DWA with the
                             base-8 pointer-arithmetic interpretation
fig6_worked_example.png    - step-by-step example (paper Fig. 5 sequence)
                             showing how nfull / carry / rows are formed
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

from dwa_core import dwa_2d_masks
import plot_style as ps

ps.apply_style()
FIGDIR = "figures"

BOX_KW = dict(boxstyle="round,pad=0.35", linewidth=1.2)


def box(ax, x, y, text, fc="white", ec=ps.TEXT_SECONDARY, fontsize=9.5,
        color=ps.TEXT_PRIMARY):
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=color, bbox=dict(facecolor=fc, edgecolor=ec, **BOX_KW),
            zorder=3)


def arrow(ax, xy_from, xy_to, label=None, color=None, lx=0, ly=0,
          fontsize=8.5, ls="-"):
    color = color or ps.TEXT_SECONDARY
    ax.add_patch(FancyArrowPatch(xy_from, xy_to, arrowstyle="-|>",
                                 mutation_scale=14, color=color,
                                 linestyle=ls, lw=1.4, zorder=2))
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2 + lx
        my = (xy_from[1] + xy_to[1]) / 2 + ly
        ax.text(mx, my, label, fontsize=fontsize, ha="center",
                va="center", color=color,
                bbox=dict(facecolor=ps.SURFACE, edgecolor="none", pad=1))


# ---------------------------------------------------------------------------
# Figure 5: architecture / signal flow
# ---------------------------------------------------------------------------

def fig_architecture():
    fig, ax = plt.subplots(figsize=(11, 8.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    box(ax, 5, 9.45,
        "DAC input  d[5:0]     (example:  d = 13 = 001 101$_2$ = 15$_8$)\n"
        "task: select the NEXT 13 elements after pointer P, wrapping around",
        fc="#fdf3ee", ec=ps.C_2DDWA, fontsize=10)

    box(ax, 2.35, 7.9,
        "MSB  d[5:3] = 001$_2$ = 1\n(counts whole rows of 8)", fontsize=9)
    box(ax, 7.65, 7.9,
        "LSB  d[2:0] = 101$_2$ = 5\n(counts leftover elements)", fontsize=9)
    arrow(ax, (4.35, 9.1), (2.6, 8.35))
    arrow(ax, (5.65, 9.1), (7.4, 8.35))

    box(ax, 7.65, 6.1,
        "COLUMN decoder  (runs first, on clk2e)\n"
        "3-bit DWA:  hd $\\leftarrow$ hd + LSB  (mod 8)\n"
        "$\\bf{nfull}$: was the last row left half-used?\n"
        "$\\bf{carry}$: does this LSB fill it up and\n"
        "spill into one more row?",
        fc="#eef4fc", ec=ps.C_SEGMENTED)
    box(ax, 2.35, 6.1,
        "ROW decoder  (on clk2)\n"
        "rows to select = MSB + carry + nfull\n"
        "3-bit DWA rotates the row pointer",
        fc="#eef4fc", ec=ps.C_SEGMENTED)
    arrow(ax, (2.35, 7.55), (2.35, 6.95))
    arrow(ax, (7.65, 7.55), (7.65, 7.0))
    arrow(ax, (5.85, 6.1), (4.15, 6.1), label="carry, nfull\n(base-8 carry digit)",
          color=ps.C_2DDWA, ly=0.42)

    box(ax, 2.35, 4.15,
        "row selection logic\n"
        "$r_{first}$ / $r_{mid}$ / $r_{last}$ / $r_{one}$\n"
        "one wire per ROW j  (8 rows)")
    box(ax, 7.65, 4.15,
        "column selection logic\n"
        "$c_{first}$ = (i $\\geq$ hd),  $c_{last}$ = (i $\\leq$ tl),  $c_{one}$\n"
        "one wire per COLUMN i  (8 columns)")
    arrow(ax, (2.35, 5.25), (2.35, 4.75))
    arrow(ax, (7.65, 5.2), (7.65, 4.75))

    box(ax, 5, 2.55,
        "every unit cell ANDs its own row and column wires:\n"
        "sel(i, j)  =  $r_{mid}$  +  $r_{first}\\cdot c_{first}$  +  "
        "$r_{last}\\cdot c_{last}$  +  $r_{one}\\cdot c_{one}$",
        fc="#fdf3ee", ec=ps.C_2DDWA)
    arrow(ax, (2.35, 3.55), (3.7, 3.0))
    arrow(ax, (7.65, 3.55), (6.3, 3.0))

    box(ax, 5, 1.15,
        "8$\\times$8 unit-element CDAC — the selected region is always one\n"
        "contiguous run in row-major order: partial first row +\n"
        "full middle rows + partial last row",
        fontsize=9)
    arrow(ax, (5, 2.0), (5, 1.75))

    ax.text(0.15, 0.02,
            "Why split at all?  Selecting a run of $d$ elements is pointer "
            "arithmetic  P $\\leftarrow$ (P + d) mod 64.  Writing P as a two-digit "
            "base-8 number (row, column) turns one 64-wide rotation into two "
            "8-wide rotations plus a carry —\nexactly like column addition. "
            "A 1-D DWA needs a $2^N$-wide barrel shifter and $2^N$ wires "
            "(256 at 8 bits); the 2-D form needs two $2^{N/2}$-wide DWAs and "
            "$7\\cdot2^{N/2}$ shared row/column wires (46% fewer transistors, "
            "Table 1).",
            fontsize=9, color=ps.TEXT_SECONDARY, va="bottom")

    ax.set_title("2-D DWA signal flow — one 64-element rotation, computed "
                 "as base-8 digit arithmetic", fontsize=13, pad=14)
    fig.savefig(f"{FIGDIR}/fig5_architecture_flow.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6: worked example (paper Fig. 5 input sequence)
# ---------------------------------------------------------------------------

SEQ = [8, 9, 4, 18]
STORY = [
    "LSB = 0, so the column pointer\nstays at 0. Exactly MSB = 1 row\n"
    "is used. rows = 1 + 0 + 0 = 1",
    "Row 1 is filled completely and\n1 element SPILLS into row 2\n"
    "$\\Rightarrow$ carry = 1.  rows = 1 + 1 + 0 = 2",
    "Row 2 was left half-used\n$\\Rightarrow$ nfull = 1: keep filling it.\n"
    "4 elements fit. rows = 0 + 0 + 1 = 1",
    "General case: continue row 2\n(r$_{first}$), take row 3 whole (r$_{mid}$),\n"
    "stop mid-row 4 (r$_{last}$). rows = 2+0+1 = 3",
]
ROLE_ROWS = [None, None, None, {2: "$r_{first}$", 3: "$r_{mid}$",
                                4: "$r_{last}$"}]


def fig_worked_example():
    masks, sig = dwa_2d_masks(SEQ, nbits=6, return_signals=True)
    masks = masks.reshape(-1, 8, 8)
    used_before = masks.cumsum(axis=0) - masks   # cells used in prior samples

    fig, axes = plt.subplots(1, 4, figsize=(13, 4.9))
    for n, ax in enumerate(axes):
        s = sig[n]
        for j in range(8):
            for i in range(8):
                if masks[n, j, i]:
                    fc = ps.C_SELECTED
                elif used_before[n, j, i]:
                    fc = "#dddcd8"
                else:
                    fc = "white"
                ax.add_patch(Rectangle((i, j), 1, 1, facecolor=fc,
                                       edgecolor=ps.TEXT_SECONDARY, lw=0.5))
        # hd marker: where this sample's selection starts
        ax.annotate("start (hd)", xy=(s["hd"] + 0.5, s["rows"][0] + 1),
                    xytext=(s["hd"] + 0.5, 9.4), ha="center", fontsize=8,
                    color=ps.C_2DDWA,
                    arrowprops=dict(arrowstyle="->", color=ps.C_2DDWA))
        if ROLE_ROWS[n]:
            for j, role in ROLE_ROWS[n].items():
                ax.text(8.25, j + 0.5, role, fontsize=9, va="center",
                        color=ps.C_SEGMENTED)
        ax.set_xlim(-0.2, 9.4)
        ax.set_ylim(-0.2, 10.1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"sample {n + 1}:  d = {SEQ[n]}   "
                     f"(MSB {s['msb']}, LSB {s['lsb']})", fontsize=10.5)
        ax.text(4, -0.7,
                f"nfull = {s['nfull']}   carry = {s['carry']}   "
                f"rows = {s['nrows']}",
                ha="center", fontsize=9.5, color=ps.TEXT_PRIMARY,
                fontweight="bold")
        ax.text(4, -1.3, STORY[n], ha="center", va="top", fontsize=8.8,
                color=ps.TEXT_SECONDARY)
        ax.set_ylim(-3.6, 10.1)

    fig.suptitle("How the two decoders cooperate — input sequence "
                 "{8, 9, 4, 18} (paper Fig. 5)\n"
                 "red = selected this sample,  gray = used in earlier "
                 "samples;  rows = MSB + carry + nfull", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(f"{FIGDIR}/fig6_worked_example.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_architecture()
    fig_worked_example()
    print("explainer figures written to", FIGDIR)
